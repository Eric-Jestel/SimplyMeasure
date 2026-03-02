from brukeropus import Opus, read_opus
from pathlib import Path
import shutil

# import os


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
        # open function inside opus
        self.opus.open(filepath)

    def getSample(self, save_path=None):

        print("Taking Sample...")
        sample_path = self.opus.measure_sample(unload=True)
        print("Saved sample to:", str(sample_path))

        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(sample_path, str(save_path))
            print("Moved sample to:", str(save_path))

        return sample_path

    def disconnect(self):
        pass
