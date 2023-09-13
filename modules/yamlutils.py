import yaml
import os
import logging

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
            logging.error(f"File {self.path} does not exist!")
            sys.exit(1)

        if not os.path.isfile(self.path):
            logging.error(f"File {self.path} is not a regular file!")
            sys.exit(1)

    def load(self):
        with open(self.path, 'r') as yml_file:
            return yaml.safe_load(yml_file)