import yaml
import os

class YamlHandler:
    def __init__(self, path):
        self.path = path
        self.sanity()
        self.content = self.load()

    """
        Check if the provided path exist and file or not
        raise exception on failure
    """
    def sanity(self):
        if not os.path.exists(self.path):
            raise AssertionError(f"File {self.path} does not exist!")

        if not os.path.isfile(self.path):
            raise AssertionError(f"File {self.path} is not a regular file!")

    def load(self):
        with open(self.path, 'r') as yml_file:
            return yaml.safe_load(yml_file)