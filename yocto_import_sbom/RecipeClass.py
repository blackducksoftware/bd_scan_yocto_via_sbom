import re
import logging


class Recipe:
    def __init__(self, name, version):
        self.name = name
        self.orig_version = version
        self.version = self.filter_version_string(version)
        self.layer = ''
        self.spdxid = ''
        self.recipe_in_oe = False
        self.oe_layer = {}
        self.oe_recipe = {}

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
