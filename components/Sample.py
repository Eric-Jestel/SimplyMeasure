# This is the sample class file


class Sample:
    """
    Represents a sample generated from the instrument
    """

    name = ""
    type = ""
    data = []
    interval = 0

    def __init__(self, name, type, data, interval):
        """
        Creates a new Sample object

        Args:
            name (String): The name of the sample
            type (String): the type of data the sample took ("infrared" or "uv-vis")
            data (Float[]): The data points
            interval (Float): The interval between each data point
        """
        self.name = name
        self.type = type
        self.data = data
        self.interval = interval

    def __str__(self):
        """
        Generates a string representation of the sample that will be used to create the sample file
        """
        point_count = len(self.data) if self.data is not None else 0
        return (
            f"Sample(name={self.name}, type={self.type}, "
            f"points={point_count}, interval={self.interval})"
        )
