# This is the Opus Instrument Controller

from brukeropus import Opus, OPUSFile  # , read_opus
from pathlib import Path
import shutil
import subprocess
import time

# import os


print("InstrumentController module loaded")


class InstrumentControllerOpus:
    

    def __init__(self):

        # Path to Opus software
        self.opusExePath = "C:\\Program Files\\Bruker\\OPUS_8.8.4\\opus.exe"  # change to actual path to opus software
        
        # start Opus Software
        #self.setup(launch_opus=True)

        # needs to connect to opus
        self.opus = Opus()

        # Path to pre-existing blan file/s
        self.blankPath = None

        # Data in the blank file. Saved as a Opus object
        self.blankData = None

        # Settings for measuring samples
        self.sampleSettings = {}

        self.opus_process = None
        

    def _print_received(self, command: str, payload=None) -> None:
        print(f"[InstrumentController][RECEIVED] {command} payload={payload}")

    def _print_executed(self, command: str, result=None) -> None:
        print(f"[InstrumentController][EXECUTED] {command} result={result}")




    def setup(self, launch_opus=True) -> bool:
        """
        Sets up the instrument
        """
        self._print_received("setup")
        # Launch OPUS (GUI)
        if launch_opus:
            try:
                self.opus_process = subprocess.Popen([self.opusExePath])  # starts OPUS Software
                print("OPUS launched.")
                result = True
                self._print_executed("setup", result)
                return result
            except Exception as e:
                print("Failed to launch OPUS:", e)
                result = False
                self._print_executed("setup", result)
                return result

        # Wait for the human to log in
        print("Please log into OPUS.")
        input("Press ENTER here *after* OPUS is open and you are fully logged in... ")


        # This function checks that the instrument is connected and checks the opus version
    def ping(self) -> bool:
        """
        Lightweight connectivity check against the instrument bridge.
        """
        self._print_received("ping")
        try:
            if not self.opus.connected:
                self.opus.connect()

            version = self.opus.get_version()
            print("OPUS responded:", version)
            self._print_executed("ping", True)
            return True

        except Exception as e:
            print("OPUS ping failed:", e)
            self._print_executed("ping", False)
            return False
    

    def take_blank(self, filename):
        
        """
        Sends a command to the instrument to take a blank sample and saves it to a file

        Args:
            filename (String): the name of the file that the blank will be saved to

        Returns:
            Boolean: True if successful
        """

        self._print_received("take_blank", {"filename": filename})

        print("Taking Blank")
        self.opus.measure_ref()
        # TA can set name so fix later
        path_ref = self.opus.save_ref()
        print("Blank taken and saved to:", path_ref)


        try:
            print("Taking Blank")
            self.opus.measure_ref()

            path_ref = self.opus.save_ref()
            print("Blank taken and saved to:", path_ref)
            return True

        except Exception as e:
            print("Failed to take blank:", e)
            return False


    def set_blank(self, filename): # Hopefull this works,not sure (it shoudl in theory)
        
        """
        Sets the blank that the machine will test the generated samples against

        Args:
            filename (String): the name of the file that the holds the blank's data

        Returns:
            Boolean: True if successful
        """
        # uses the filepath to load the blank.

        # I'm not sure this will work since writing .open
        # in this way will just cause python to look for an
        # open function inside opus
        self._print_received("set_blank", {"filename": filename})
        path = Path(filename)
        
        if not path.exists():
            print("ERROR: Blank file not found.")
            self._print_executed("set_blank", False)
            return False
        

        try:
            if not self.opus.connected:
                self.opus.connect()

            folder = str(path.parent)
            file_name = path.name

            # Load the blank file into OPUS
            self.opus.query(
                f"COMMAND_LINE Load (0, {{COF=0, DAP='{folder}', DAF='{file_name}'}});"
            )

            # Tell OPUS to use the loaded file as the active reference
            self.opus.query("COMMAND_LINE LoadReference ();")

            self.blank_file = str(path)
            self._print_executed("set_blank", True)
            return True

        except Exception as e:
            print("Failed to set blank:", e)
            self._print_executed("set_blank", False)
            return False






    def take_sample(self, filename):
        """
        Sends a command to the instrument to take a sample and converts the sample to a Sample object

        Args:
            filename (String): the name of the file that the sample will be saved to

        Returns:
            Sample: the sample that the instrument collected
        """
        print("Taking Sample...")
        sample_path = self.opus.measure_sample(unload=True, HFQ=1000, LFQ=2000, NSS=2) #, **self.sampleSettings)
        print("Saved sample to:", str(sample_path))
        """"""
        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(sample_path, str(save_path))
            print("Moved sample to:", str(save_path))

        return sample_path





    def changeSettings(
        self, waveStart=None, waveStop=None
    ):  # waveStart is the High end
        if waveStart != None:
            self.sampleSettings["hfw"] = waveStart

        if waveStop != None:
            self.sampleSettings["lfw"] = waveStop

        return self.sampleSettings

    def shutdown(self):
        """
        Shuts the instrument down

        Returns:
            Boolean: True if successful
        """
        self._print_received("shutdown")

        try:
            if self.opus is not None and hasattr(self.opus, "disconnect"):
                self.opus.disconnect()

            if self.opus_process is not None and self.opus_process.poll() is None:
                self.opus_process.terminate()
                self.opus_process.wait(timeout=5)

            self.opus = None
            self.opus_process = None
            return True

        except Exception as e:
            print("Shutdown failed:", e)
            return False
            






#test = InstrumentControllerOpus()
#test.take_sample("C:\\Users\\Public\\Documents\\Bruker\\Opus_8.8.4\\Data\\Sample13.0")
ofile = OPUSFile("C:\\Users\\Public\\Documents\\Bruker\\Opus_8.8.4\\Data\\Sample12.0")
iter = ofile.iter_data()

for value in iter:
    print(value)
    print(value.params)

    # outputData becomes: [[x0, y0], [x1, y1], ...]
    outputData = [[float(x), float(y)] for x, y in zip(value.x, value.y)]

    print(outputData)



