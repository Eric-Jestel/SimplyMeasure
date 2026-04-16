from brukeropus import Opus, OPUSFile  # , read_opus
from pathlib import Path
import shutil
import subprocess


# import os
# import read_opus when using it
# import time when using it


# need a class
class InstrumentControllerOpus:
    # need the opus machine to be instantiated
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
        

    # ------------------------------------------------------------------------------------------------------------------------------------------
    def take_blank(self):
        # gets a reference sample aka a blank from the machine, and also sets it as the reference.
        print("Taking Blank")
        self.opus.measure_ref()
        # TA can set name so fix later
        path_ref = self.opus.save_ref()
        print("Blank taken and saved to:", path_ref)

    # TA can change so fix later
    def set_blank(
        self, filepath= "C:\\Users\\Public\\Documents\\Bruker\\Opus_8.8.4\\Data\\RefBlank.0"
    ):
        # uses the filepath to load the blank.

        # I'm not sure this will work since writing .open
        # in this way will just cause python to look for an

        # I'm not sure this will work since writing .open
        # in this way will just cause python to look for an
        # open function inside opus
        self.opus.open(filepath)

    def set_blank(self, filepath):
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

    def take_sample(self, save_path=None):

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

    def instrumentParams(
        self,
    ):  # it should allow you to change the starting wavelength, stoping wavelength, saturstion, and something else, not sure what.
        pass

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
        print("I'm in here!")
        if launch_opus:
            try:
                subprocess.Popen([self.opusExePath])  # starts OPUS Software
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
        if waveStart is not None:
            self.sampleSettings["hfw"] = waveStart

        if waveStop is not None:
            self.sampleSettings["lfw"] = waveStop

        return self.sampleSettings

    def disconnect(self):
        pass

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



