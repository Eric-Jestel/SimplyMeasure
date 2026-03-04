# This is the system controller

from pathlib import Path
from datetime import datetime

try:
    from InstrumentController import InstrumentController
    from ServerController import ServerController
except ImportError:
    from components.InstrumentController import InstrumentController
    from components.ServerController import ServerController

print("SystemController imported")


# ------------------------------------------------------------------------------------------------------------------------------------------
class SystemController:

    # I need variables

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(
        self,
        server_controller_cls=ServerController,
        instrument_controller_cls=InstrumentController,
        file_dir=None,
        debug: bool = True,
    ):
        print(
            "[SystemController][RECEIVED] __init__ "
            f"server_controller_cls={server_controller_cls.__name__}, "
            f"instrument_controller_cls={instrument_controller_cls.__name__}, "
            f"file_dir={file_dir}, debug={debug}"
        )
        self.debug = bool(debug)
        sample_dir = file_dir or str(Path(__file__).parent / "sample_data")
        self.ServController = server_controller_cls(
            file_dir=sample_dir, debug=self.debug
        )
        self.InstController = instrument_controller_cls(debug=self.debug)
        # needed a dictionary for error codes
        self.ErrorDictionary = {
            0: "Good to go",
            100: "Machine is not connecting",
            110: "Server is not connecting",
            220: "Not a valid Account",
            330: "User not logged in",
            300: "No active session",
            400: "No data",
            550: "No blank to set",
        }
        print("[SystemController][EXECUTED] __init__ controllers initialized")

    def _print_received(self, command: str, payload=None) -> None:
        print(f"[SystemController][RECEIVED] {command} payload={payload}")

    def _print_executed(self, command: str, result=None) -> None:
        print(f"[SystemController][EXECUTED] {command} result={result}")

    def _debug(self, message: str) -> None:
        if self.debug:
            print(f"[SystemController] {message}")

    def _instrument_ready(self) -> bool:
        self._print_received("_instrument_ready")
        ping = getattr(self.InstController, "ping", None)
        if callable(ping):
            ready = bool(ping())
            self._debug(f"_instrument_ready() via ping -> {ready}")
            self._print_executed("_instrument_ready", ready)
            return ready
        ready = bool(self.InstController)
        self._debug(f"_instrument_ready() fallback -> {ready}")
        self._print_executed("_instrument_ready", ready)
        return ready

    def _server_ready(self) -> bool:
        self._print_received("_server_ready")
        connect = getattr(self.ServController, "connect", None)
        if callable(connect):
            ready = bool(connect())
            self._debug(f"_server_ready() via connect -> {ready}")
            self._print_executed("_server_ready", ready)
            return ready
        try:
            ready = bool(self.ServController.ping())
            self._debug(f"_server_ready() via ping -> {ready}")
            self._print_executed("_server_ready", ready)
            return ready
        except Exception as exc:
            self._debug(f"_server_ready() ping exception: {exc}")
            self._print_executed("_server_ready", False)
            return False

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def startUp(self):
        self._print_received("startUp")
        # verify machine connection
        self._debug("startUp() starting")
        self._print_received("InstrumentController.setup")
        InstConn = self.InstController.setup()
        self._print_executed("InstrumentController.setup", InstConn)
        self._debug(f"startUp() instrument setup -> {InstConn}")
        if InstConn:
            # verify server connection
            ServConn = self._server_ready()
            self._debug(f"startUp() server connect -> {ServConn}")
            if ServConn:
                self._print_executed("startUp", 0)
                return 000
            else:
                self._print_executed("startUp", 110)
                return 110
        else:
            self._print_executed("startUp", 100)
            return 100

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def signIn(self, username):
        self._print_received("signIn", {"username": username})
        # verify connection to ICN
        self._debug(f"signIn() username={username}")
        if self._server_ready():
            # send information to server controller to sign in
            self._print_received("ServerController.login", {"username": username})
            loggedIn = self.ServController.login(username)
            self._print_executed("ServerController.login", loggedIn)
            self._debug(f"signIn() login response={loggedIn}")
            if loggedIn:
                self._print_executed("signIn", 0)
                return 000
            else:
                self._print_executed("signIn", 220)
                return 220
        else:
            self._print_executed("signIn", 110)
            return 110

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def signOut(self):
        self._print_received("signOut")
        # verify server connectivity
        self._debug("signOut() invoked")
        if self._server_ready():
            # send all data to the server controller after taking samples
            self._print_received("ServerController.send_all_data")
            upload_result = self.ServController.send_all_data()
            self._print_executed("ServerController.send_all_data", upload_result)
            self._debug(f"signOut() send_all_data -> {upload_result}")
            # check to see if anyone is logged in already
            if self.ServController.is_logged_in():
                self._print_received("ServerController.logout")
                if self.ServController.logout():
                    self._print_executed("ServerController.logout", True)
                    self._print_executed("signOut", 0)
                    return 000
                else:
                    self._print_executed("ServerController.logout", False)
                    self._print_executed("signOut", 330)
                    return 330
            else:
                self._print_executed("signOut", 300)
                return 300
        else:
            self._print_executed("signOut", 110)
            return 110

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def runLabMachine(self):
        self._print_received("runLabMachine")
        # verify instrument connection
        self._debug("runLabMachine() invoked")
        if self._instrument_ready():
            # sends instructions to machine to run test
            self._print_received("InstrumentController.take_sample")
            targetFilename = datetime.now().strftime("%Y%m%d_%H%M%SZ") + ".csv"
            csv_path = self.InstController.take_sample(targetFilename)
            self._print_executed("InstrumentController.take_sample", csv_path)
            self._debug(f"runLabMachine() sample received={bool(csv_path)}")
            if csv_path:
                self.ServController.process_sample(csv_path)
                # verify server connection
                if self._server_ready():
                    # sends data to UI somehow and send data to server controller to send to the ICN
                    self._print_received("ServerController.send_all_data")
                    sent = self.ServController.send_all_data()
                    self._print_executed("ServerController.send_all_data", sent)
                    self._debug(f"runLabMachine() send_all_data -> {sent}")
                    for fileSent in sent:
                        if fileSent[1] is False:
                            self._debug(f"runLabMachine() failed to send {fileSent[0]}")
                        if fileSent[0] == csv_path:
                            self._print_executed("runLabMachine", (0, csv_path))
                            return 000, csv_path
                    self._print_executed("runLabMachine", (110, None))
                    return 110, None
                else:
                    self._print_executed("runLabMachine", (110, None))
                    return 110, None
            else:
                self._print_executed("runLabMachine", (400, None))
                return 400, None
        else:
            self._print_executed("runLabMachine", (100, None))
            return 100, None

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def takeBlank(self, filename=None):
        self._print_received("takeBlank", {"filename": filename})
        # verify instrument connection
        self._debug(f"takeBlank() filename={filename}")
        if self._instrument_ready():
            if filename is None:
                filename = str(
                    Path(self.ServController.file_dir)
                    / f"blank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
            # sends instructions to machine to run test
            self._print_received(
                "InstrumentController.take_blank", {"filename": filename}
            )
            data = self.InstController.take_blank(filename)
            self._print_executed("InstrumentController.take_blank", data)
            self._debug(f"takeBlank() result={data}")
            if data:
                # send data to UI to hold onto for setting the blank
                self._print_executed("takeBlank", (0, self.InstController.blank_file))
                return 000, self.InstController.blank_file
            else:
                self._print_executed("takeBlank", (400, None))
                return 400, None
        else:
            self._print_executed("takeBlank", (100, None))
            return 100, None

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def setBlank(self, data):
        self._print_received("setBlank", {"data": data})
        # verify instrument connection
        self._debug(f"setBlank() data={data}")
        if self._instrument_ready():
            if data:
                # send instructions to machine to set data
                self._print_received("InstrumentController.set_blank", {"data": data})
                set_ok = self.InstController.set_blank(data)
                self._print_executed("InstrumentController.set_blank", set_ok)
                self._debug(f"setBlank() set_blank -> {set_ok}")
                if set_ok:
                    self._print_executed("setBlank", 0)
                    return 000
                else:
                    self._print_executed("setBlank", 550)
                    return 550
            else:
                self._print_executed("setBlank", 400)
                return 400
        else:
            self._print_executed("setBlank", 100)
            return 100

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def takeSample(self):
        self._print_received("takeSample")
        # verify instrument connection
        self._debug("takeSample() invoked")
        if self._instrument_ready():
            # sends instructions to machine to run test
            self._print_received("InstrumentController.take_sample")
            data = self.InstController.take_sample()
            self._print_executed("InstrumentController.take_sample", data)
            self._debug(f"takeSample() sample received={bool(data)}")
            if data:
                # send data to UI to hold onto for setting the blank
                self._print_executed("takeSample", (0, data))
                return 000, data
            else:
                self._print_executed("takeSample", (400, None))
                return 400, None
        else:
            self._print_executed("takeSample", (100, None))
            return 100, None

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def stopProgram(self):
        self._print_received("stopProgram")
        # verify the server controller is connected and logged in
        self._debug("stopProgram() invoked")
        if self._server_ready():
            if self.ServController.is_logged_in():
                # sends instructions for the Server controller to disconnect
                self._print_received("ServerController.logout")
                self.ServController.logout()
                self._print_executed("ServerController.logout", True)
            # verify instrument connection
            if self._instrument_ready():
                # sends instructions for the Instrument Controller to shut down the machine
                self._print_received("InstrumentController.shutdown")
                shut_ok = self.InstController.shutdown()
                self._print_executed("InstrumentController.shutdown", shut_ok)
                self._debug(f"stopProgram() shutdown -> {shut_ok}")
                result = 000 if shut_ok else 100
                self._print_executed("stopProgram", result)
                return result
            else:
                self._print_executed("stopProgram", 100)
                return 100
        else:
            self._print_executed("stopProgram", 110)
            return 110


# ------------------------------------------------------------------------------------------------------------------------------------------
# error code stuffs
"""
All of this is subject to change
Preabmle = 000 means that it is good to go
1) 100 = Machine is not connecting
2) 110 = Server is not connecting
3) 220 = Not a valid Account
4) 330 = User not logged in
5) 400 = No data :(
6) 550 = No blank to set
"""
# Info needed
"""
I need a way to verify server connectivity (ping it)
I need a way to verify machine connectivity (maybe ping it?)
When running the machine is there really no possible way to send
information to and from the instrument controller to the machine controller?
"""


class SystemControllerSample:

    instCon = InstrumentController()
    servCon = ServerController()
    samples = []

    def setup(self):
        """
        Sets up the instrument and server controllers

        Returns:
            Boolean: True if successful
        """
        return self.instCon.setup() and self.servCon.connect()

    def take_blank(self, filename):
        """
        Takes a blank sample and saves it to a file

        Args:
            filename (String): The name of the file that the blank sample is saved to

        Returns:
            Boolean: True if successful
        """
        return self.instCon.take_blank(filename)

    def set_blank(self, filename):
        """
        Sets the blank that the instrument will compare samples against

        Args:
            filename (String): the name of the blank file

        Returns:
            Boolean: True if successful
        """
        return self.instCon.set_blank(filename)

    def take_sample(self):
        """
        Takes a sample and sends it to ICN

        Returns:
            Boolean: True if successful
        """
        if not self.servCon.is_logged_in():
            return False
        newSample = self.instCon.take_sample()
        self.samples.append(newSample)
        return self.servCon.send_data(newSample)

    def login_user(self, username):
        """
        Logs in a user with the given username

        Args:
            username (string): the username of the user

        Returns:
            Boolean: True if successful
        """
        return self.servCon.login(username)

    def logout_user(self):
        """
        Logs out the user currently logged in

        Returns:
            Boolean: True if successful
        """
        self.samples = []
        return self.servCon.logout()

    def display_data(self):
        """
        Displays all the samples the user has currently taken
        """
        return

    def shutdown(self):
        """
        Shuts down the instrument and sends all unsent data to ICN

        Returns:
            Boolean: True if it successfuly sent all unsent data
        """
        self.logout_user()
        self.instCon.shutdown()
        return self.servCon.send_all_data()
