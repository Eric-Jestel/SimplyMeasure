# This is the Opus Instrument Controller

from brukeropus import Opus, OPUSFile  # , read_opus
from pathlib import Path
import shutil
import subprocess
import time
import csv

# import os


print("InstrumentController module loaded")


class InstrumentController:
    

    def __init__(self, PROJECT_ROOT, debug: bool = False):

        self.PROJECT_ROOT = PROJECT_ROOT
        self.debug = bool(debug)
        # Path to Opus software
        self.opusExePath = "C:\\Program Files\\Bruker\\OPUS_8.8.4\\opus.exe"  # change to actual path to opus software

        #self.setup(launch_opus=True)
        
        # start Opus Software
        #self.setup(launch_opus=True)

        # needs to connect to opus
        self.opus = None

        # Path to pre-existing blan file/s
        self.blankPath = None

        # Data in the blank file. Saved as a Opus object
        self.blankData = None

        #
        self.MAX_WAVE = 16799
        self.MIN_WAVE = 0
        self.SAMPLE_COUNT_MIN = 1

        # Settings for measuring samples
        self.sampleSettings = {"hfw": 16799, "lfw": 0, "nss": 50}

        self.blank_file = "" # <--

        self._opusProcID = None


        # need to have a connected variable to check if we are connected to the machine
        self.connected = False
        

    def _print_received(self, command: str, payload=None) -> None:
        print(f"[InstrumentController][RECEIVED] {command} payload={payload}")

    def _print_executed(self, command: str, result=None) -> None:
        print(f"[InstrumentController][EXECUTED] {command} result={result}")

    def validate_scan(self, filename):
        """
        Validates that scan/blank file matched the format for this instrument
        Args:
            filename (str): The filename of the blank file being validated
        Returns:
            boolean: True if the file contains a valid scan/blank
        """

        try:
            with open(filename) as blankFile:
                settings = blankFile.readline().split("-")
                if len(settings) < 4:
                    return False

                name = settings[0].split("_")
                satSettings = settings[3].split(",")
                if len(satSettings) < 2 or len(name) < 1 or name[0] != "IR":
                    return False

                fields = blankFile.readline().split(",")
                if len(fields) < 2 or fields[0] != "Wavelength (nm)" or fields[1] != "Abs":
                    return False

                waveStart = float(settings[1])
                waveEnd = float(settings[2])
                sample_count = float(satSettings[0])
                if waveStart > self.MAX_WAVE or waveEnd < self.MIN_WAVE or waveStart <= waveEnd:
                    return False
                if sample_count < self.SAMPLE_COUNT_MIN:
                    return False

                prevWave = waveStart - 2
                for line in blankFile:
                    if line != "\n":
                        values = [float(i) for i in line.strip().split(",")[:2]]
                        waveDif = prevWave - values[0]
                        if waveDif > 3 or waveDif < 0.5:
                            return False
                        prevWave = values[0]

                return True
        except ValueError:
            return False
        except FileNotFoundError:
            return False


    def opus_to_csv(
    self,
    opus_filename,
    csv_filename,
    wave_start,
    wave_stop,
    sample_count,
    blank=False
    ):
        """
        Read a native OPUS .0 file and convert it into a CSV file shaped like the
        IR controller output.

        Returns:
            str | None: path to the CSV file on success, None on failure
        """

        try:
            opus_path = Path(opus_filename)
            csv_path = Path(csv_filename)

            if not opus_path.exists():
                print("ERROR: OPUS file not found:", opus_path)
                return None

            csv_path.parent.mkdir(parents=True, exist_ok=True)

            ofile = OPUSFile(str(opus_path))
            data_iter = ofile.iter_data()

            output_data = None

            for value in data_iter:
                x_values = getattr(value, "x", None)
                y_values = getattr(value, "y", None)

                if x_values is None or y_values is None:
                    continue

                output_data = [
                    [float(x), float(y)]
                    for x, y in zip(x_values, y_values)
                ]

                if output_data:
                    break

            if not output_data:
                print("ERROR: No usable data blocks found in:", opus_path)
                return None

            t = ""
            if blank:
                t = "_Blank"
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)

                # Match the general format expected by the other instrument controller
                csv_file.write(f"IR{t}-{wave_start}-{wave_stop}-{sample_count},\n")

                # Header line
                writer.writerow(["Wavelength (nm)", "Abs"])

                # Data rows
                writer.writerows(output_data)

            return str(csv_path)

        except Exception as e:
            print("ERROR converting OPUS file to CSV:", e)
            return None


    def setup(self, launch_opus=True) -> bool:
        """
        Sets up the instrument
        """
        self._print_received("setup")
        # Launch OPUS (GUI)
        if launch_opus:
            try:
                self._opusProcID = subprocess.Popen([self.opusExePath])  # starts OPUS Software
                print("OPUS launched.")
                result = True
                print("Please log into OPUS.")
                input("Press ENTER here *after* OPUS is open and you are fully logged in... ")
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


    def _get_connected_opus(self):
        opus = Opus()

        if not opus.connected:
            opus.connect()
            opus.connected = True

        _ = opus.get_version()
        return opus

        # This function checks that the instrument is connected and checks the opus version
    '''
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
    '''
    def ping(self) -> bool:
        """
        Lightweight connectivity check against OPUS.
        """
        self._print_received("ping")

        try:
            opus = self._get_connected_opus()
            version = opus.get_version()
            print("OPUS responded:", version)

            self._print_executed("ping", True)
            return True

        except Exception as e:
            print("OPUS ping failed:", e)
            self._print_executed("ping", False)
            return False

    '''
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
    '''

    """def take_blank(self, filename):
        
        #Takes a blank measurement, saves the native OPUS file, converts it to CSV,
        #and stores the native blank path in self.blank_file for later set_blank() use.
        

        self._print_received("take_blank", {"filename": filename})

        try:
            opus = self._get_connected_opus()

            csv_path = Path(filename)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            native_blank_path = csv_path.with_suffix(".0")

            print("Taking Blank...")
            opus.measure_ref()

            saved_path = Path(str(opus.save_ref()))
            print("Blank taken and saved to:", saved_path)

            # Move the native blank file to the location we want
            if saved_path != native_blank_path:
                shutil.move(str(saved_path), str(native_blank_path))
                print("Moved native blank to:", str(native_blank_path))

            # Convert native blank to CSV
            created_csv = self.opus_to_csv(
                opus_filename=str(native_blank_path),
                csv_filename=str(csv_path),
                wave_start=self.sampleSettings.get("hfw", 600),
                wave_stop=self.sampleSettings.get("lfw", 500),
                saturation=0.1,
                bandwidth=2
            )

            if created_csv is None:
                self._print_executed("take_blank", False)
                return False

            # Store the native blank path, because set_blank() needs a real OPUS file
            self.blank_file = str(native_blank_path)

            self._print_executed(
                "take_blank",
                {
                    "success": True,
                    "blank_file": self.blank_file,
                    "blank_csv": created_csv
                }
            )
            return True

        except Exception as e:
            print("Failed to take blank:", e)
            self._print_executed("take_blank", False)
            return False"""




    def _copy_when_ready(self, source_path, target_path, attempts=20, delay=0.5):
        source = Path(source_path)
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        last_error = None

        for _ in range(attempts):
            try:
                shutil.copy2(str(source), str(target))
                return True
            except PermissionError as e:
                last_error = e
                time.sleep(delay)
            except OSError as e:
                last_error = e
                time.sleep(delay)

        if last_error is not None:
            raise last_error

        return False

    def take_blank(self, filename):
        """
        Takes a blank measurement, saves the native OPUS file, converts it to CSV,
        and stores the native blank path in self.blank_file for later set_blank() use.
        """

        self._print_received("take_blank", {"filename": filename})

        try:
            opus = self._get_connected_opus()

            csv_path = Path(filename)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            native_blank_path = csv_path.with_suffix(".0")

            print("Taking Blank...")
            opus.measure_ref(hfw=16799, lfw=0)

            saved_path = Path(str(opus.save_ref()))
            print("Blank taken and saved to:", saved_path)
            
            # need to unload the blank from OPUS software before we can change it
            opus.unload_file(str(saved_path))

            if saved_path != native_blank_path:
                self._copy_when_ready(saved_path, native_blank_path)
                print("Copied native blank to:", str(native_blank_path))
            else:
                native_blank_path = saved_path

            created_csv = self.opus_to_csv(
                opus_filename=str(native_blank_path),
                csv_filename=str(csv_path),
                wave_start=self.sampleSettings.get("hfw", 16799),
                wave_stop=self.sampleSettings.get("lfw", 0),
                sample_count=self.sampleSettings.get("nss", 50)
            )

            if created_csv is None:
                self._print_executed("take_blank", False)
                return False

            self.blank_file = str(created_csv)

            self._print_executed(
                "take_blank",
                {
                    "success": True,
                    "blank_file": self.blank_file,
                    "blank_csv": created_csv
                }
            )
            return created_csv

        except Exception as e:
            print("Failed to take blank:", e)
            self._print_executed("take_blank", False)
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





    """
    def take_sample(self, filename):
        
        Sends a command to the instrument to take a sample and converts the sample to a Sample object

        Args:
            filename (String): the name of the file that the sample will be saved to

        Returns:
            Sample: the sample that the instrument collected
        
        print("Taking Sample...")
        sample_path = self.opus.measure_sample(unload=True, HFQ=1000, LFQ=2000, NSS=2) #, **self.sampleSettings)
        print("Saved sample to:", str(sample_path))
        
        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(sample_path, str(save_path))
            print("Moved sample to:", str(save_path))

        return sample_path
    """
    def take_sample(self, filename):
        """
        Takes a sample, saves the native OPUS file, converts it to CSV,
        and returns the CSV path.
        """
        self._print_received("take_sample", {"filename": filename})

        try:
            opus = self._get_connected_opus()

            csv_path = Path(filename)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            native_target = csv_path.with_suffix(".0")

            print("Taking Sample...")
            sample_path = Path(str(
                opus.measure_sample(
                    unload=True,
                    **self.sampleSettings
                )
            ))
            print("Saved native sample to:", str(sample_path))

            if sample_path != native_target:
                self._copy_when_ready(sample_path, native_target)
                print("Copied native sample to:", str(native_target))
            else:
                native_target = sample_path

            created_csv = self.opus_to_csv(
                opus_filename=str(native_target),
                csv_filename=str(csv_path),
                wave_start=self.sampleSettings.get("hfw", 16799),
                wave_stop=self.sampleSettings.get("lfw", 0),
                sample_count=self.sampleSettings.get("nss", 50)
            )

            if created_csv is None:
                self._print_executed("take_sample", None)
                return None

            self._print_executed("take_sample", created_csv)
            return created_csv

        except Exception as e:
            print("Failed to take sample:", e)
            self._print_executed("take_sample", None)
            return None
    
    def changeSettings(self, waveStart=None, waveStop=None):
        """
        Changes the setting to the inputed values

        Args:
            waveStart (int, optional): The stating wavelength scan (should be the higher number). Defualts can be changed.
            waveStop (int, optional): The ending wavelength scan (should be the lower number). Defaults can be changed.

        Returns:
            Boolean: True if the settings were changed
        """
        if waveStart is not None:
            self.sampleSettings["hfw"] = waveStart
        if waveStop is not None:
            self.sampleSettings["lfw"] = waveStop
        return True
        

    def getSettings(self):
        """
        Returns a dictionary containing the relavent parameters of the instrument controller

        Returns:
            dict: A dictionary containing the parameters
        """
        return self.sampleSettings

def shutdown(self):
        """
        Shuts the instrument down

        Returns:
            Boolean: True if successful
        """
        self._print_received("shutdown")
        proc = getattr(self, "_opusProcID", None)
        if proc and proc.poll() is None:
            self._print_tx("OS", "taskkill", {"pid": proc.pid, "tree": True})
            try:
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self._print_executed("shutdown", True)
                return True
            except Exception as exc:
                self._debug(f"shutdown() taskkill failed: {exc}")
                self._print_executed("shutdown", False)
                return False

        self._print_executed("shutdown", True)
        return True

'''
    def take_sample(self, filename):
        
        self._print_received("take_sample", {"filename": filename})

        try:
            if not self.opus.connected:
                self.opus.connect()

            print("Taking Sample...")

            # Native OPUS output from the instrument
            sample_path = Path(str(
                self.opus.measure_sample(
                    unload=True,
                    **self.sampleSettings
                )
            ))
            print("Saved native sample to:", str(sample_path))

            # The filename passed in from SystemController is the CSV name
            csv_path = Path(filename)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            # Keep the native OPUS file beside the CSV, but with .0 extension
            native_target = csv_path.with_suffix(".0")

            if sample_path != native_target:
                shutil.move(str(sample_path), str(native_target))
                print("Moved native sample to:", str(native_target))

            created_csv = self.opus_to_csv(
                opus_filename=str(native_target),
                csv_filename=str(csv_path),
                wave_start=self.sampleSettings.get("hfw", 600),
                wave_stop=self.sampleSettings.get("lfw", 500),
                saturation=0.1,
                bandwidth=2
            )

            if created_csv is None:
                self._print_executed("take_sample", None)
                return None

            self._print_executed("take_sample", created_csv)
            return created_csv

        except Exception as e:
            print("Failed to take sample:", e)
            self._print_executed("take_sample", None)
            return None


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
            
'''






#test = InstrumentControllerOpus()
#test.take_sample("C:\\Users\\Public\\Documents\\Bruker\\Opus_8.8.4\\Data\\Sample13.0")

"""
ofile = OPUSFile("C:\\Users\\Public\\Documents\\Bruker\\Opus_8.8.4\\Data\\Sample12.0")
iter = ofile.iter_data()

for value in iter:
    print(value)
    print(value.params)

    # outputData becomes: [[x0, y0], [x1, y1], ...]
    outputData = [[float(x), float(y)] for x, y in zip(value.x, value.y)]

    print(outputData)
"""


