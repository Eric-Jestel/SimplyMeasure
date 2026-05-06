class InstrumentController:
    """
    Communicates with the instrument
    """

    def __init__(self, PROJECT_ROOT, debug: bool = False):
        """
        Creates a new instrument controller

        Args:
            PROJECT_ROOT (str): the root folder that the project was run from
            debug (bool, optional): a flag to enable debug mode. Defaults to False.
        """
        pass

    def validate_scan(self, filename):
        """
        Validates that scan/blank file matched the format for this instrument

        Args:
            filename (str): The filename of the blank file being validated

        Returns:
            boolean: True if the file contains a valid scan/blank
        """
        return False

    def getScanTime(self):
        """
        Estimates the time it will take to complete a scan in seconds

        Returns:
            float: estimated time it will take to complete a scan in seconds
        """
        return 0

    def getBlankTime(self):
        """
        Estimates the time it will take to complete a blank scan in seconds

        Returns:
            float: estimated time it will take to complete a blank scan in seconds
        """
        return 0

    def setup(self):
        """
        Sets up the instrument and anything else nessesary to operate the instrument

        Returns:
            Boolean: True if the instrument is ready to run
        """
        return False

    def ping(self) -> bool:
        """
        Lightweight connectivity check against the instrument bridge.

        Returns:
            Boolean: True if the instrument is connected
        """
        return False

    def take_blank(self, filename):
        """
        Sends a command to the instrument to take a blank sample and saves it to a file
        The controller shoulf set the active blank at the same time

        Args:
            filename (String): the name of the file that the blank will be saved to

        Returns:
            String: The file path to the CSV file containing the blank that the instrument collected
        """
        return ""

    def set_blank(self, filename):
        """
        Sets the blank that the machine will test the generated samples against

        Args:
            filename (String): the name of the file that the holds the blank's data

        Returns:
            Boolean: True if the blank was read properly
        """
        return False

    def clear_blank(self) -> None:
        """
        Removes the blank from memory and 

        Returns:
            Boolena: True if the blank was cleared
        """
        return False

    def take_sample(self, filename):
        """
        Sends a command to the instrument to take a sample and converts the data to a CSV file
        The data should be compared against the blank on file before returning the file

        Args:
            filename (String): the name of the file that the sample will be saved to

        Returns:
            String: The file path to the CSV file containing the sample that the instrument collected
        """
        return ""

    def changeSettings(self, waveStart="", waveStop=""):
        """
        Changes the setting to the inputed values

        Args:
            waveStart (str, optional): The stating wavelength scan (should be the higher number). Defualts can be changed.
            waveStop (str, optional): The ending wavelength scan (should be the lower number). Defaults can be changed.

        Returns:
            Boolean: True if the settings were changed
        """
        return False

    def getSettings(self):
        """
        Returns a dictionary containing the relavent parameters of the instrument controller

        Returns:
            dict: A dictionary containing the parameters
        """
        return {}

    def shutdown(self):
        """
        Properly shuts the instrument controller
        Should be run when the application is closed

        Returns:
            Boolean: True if the controller was shutdown properly
        """
        return False
