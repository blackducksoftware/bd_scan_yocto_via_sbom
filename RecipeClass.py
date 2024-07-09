# import global_values
import re
# import global_values
import logging
# from thefuzz import fuzz
# from VulnListClass import VulnList


class Recipe:
    def __init__(self, name, version):
        self.name = name
        self.orig_version = version
        self.version = self.filter_version_string(version)
        self.layer = ''
        self.spdxid = ''

    def add_layer(self, layer):
        self.layer = layer

    @staticmethod
    def filter_version_string(version):
        # Remove +git*
        # Remove -snapshot*
        # Replace / with space
        ret_version = re.sub(r"\+git.*", r"+gitX", version, flags=re.IGNORECASE)

        return ret_version

    def print_recipe(self):
        logging.info(f"Processed Recipe '{self.name}': {self.layer}/{self.name}/{self.version}")
