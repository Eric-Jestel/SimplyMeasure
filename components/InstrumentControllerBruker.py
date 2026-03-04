from brukeropus import Opus
from pathlib import Path
import shutil
import subprocess
import time


# import os
# import read_opus when using it


# need a class
class InstrumentControllerOpus:
    # need the opus machine to be instantiated
    def __init__(self):
        # needs to connect to opus
        self.opus = Opus()


        # Path to pre-existing blan file/s
        self.blankPath = None

        # Data in the blank file. Saved as a Opus object
        self.blankData = None

        # Settings for measuring samples
        self.sampleSettings = {}

        # Path to Opus software
        self.opusExePath = r"C:\Program Files\Bruker\OPUS\OPUS.exe"  # change to actual path to opus software

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def getBlank(self):
        # gets a reference sample aka a blank from the machine, and also sets it as the reference.
        print("Taking Blank")
        self.opus.measure_ref()
        # TA can set name so fix later
        self.opus.save_ref(
            r"C:\Users\Public\Documents\Bruker\Opus_8.8.4\Data\RefBlank.0"
        )

    # TA can change so fix later
    def loadBlank(
        self, filepath=r"C:\Users\Public\Documents\Bruker\Opus_8.8.4\Data\RefBlank.0"
    ):
        # uses the filepath to load the blank.

        # I'm not sure this will work since writing .open
        # in this way will just cause python to look for an

        # I'm not sure this will work since writing .open
        # in this way will just cause python to look for an
        # open function inside opus
        self.opus.open(filepath)
        self.opus.open(filepath)

    def setBlank(self, filepath):
        path = Path(filepath)

        if not path.exists():
            print("ERROR: Blank file not found.")

        folder = str(path.parent)
        filename = path.name

        # Load the file into OPUS
        result_1 = self.opus.query(
            f"COMMAND_LINE Load (0, {{COF=0, DAP='{folder}', DAF='{filename}'}});"
        )

        # Tell OPUS to use the loaded file as the reference
        result_2 = self.opus.query("COMMAND_LINE LoadReference ();")

        return result_1, result_2

    def getSample(self, save_path=None):

        print("Taking Sample...")
        sample_path = self.opus.measure_sample(unload=True, **self.sampleSettings)
        print("Saved sample to:", str(sample_path))

        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(sample_path, str(save_path))
            print("Moved sample to:", str(save_path))

        return sample_path

    # This function checks that the instrument is connected and checks the opus version
    def ping(self) -> bool:
        try:
            if not self.opus.connected:
                self.opus.connect()

            version = self.opus.get_version()
            print("OPUS responded:", version)
            return True

        except Exception as e:
            print("OPUS ping failed:", e)
            return False

    def setup(self, launch_opus=True) -> bool:
        # Launch OPUS (GUI)
        if launch_opus:
            try:
                subprocess.Popen([self.opus_exe_path])  # starts OPUS Software
                print("OPUS launched.")
            except Exception as e:
                print("Failed to launch OPUS:", e)
                return False

        # Wait for the human to log in
        print("Please log into OPUS.")
        input("Press ENTER here *after* OPUS is open and you are fully logged in... ")

        # Connect ONCE and verify OPUS responds
        try:
            self.opus = Opus()
            _ = self.opus.get_version()  # Checks connection
            print("Connected to OPUS.")
            return True
        except Exception as e:
            print("Could not connect to OPUS (are you logged in?):", e)
            return False

    def changeSettings(
        self, waveStart=None, waveStop=None
    ):  # waveStart is the High end
        if waveStart != None:
            self.sampleSettings["hfw"] = waveStart

        if waveStop != None:
            self.sampleSettings["lfw"] = waveStop

        return self.sampleSettings

    def disconnect(self):
        pass
