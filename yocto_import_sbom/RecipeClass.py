import re
import logging


class Recipe:
    def __init__(self, name, version):
        self.name = name
        self.orig_version = version
        self.epoch = ''
        self.version = self.filter_version_string(version)
        self.layer = ''
        self.spdxid = ''
        self.oe_layer = {}
        self.oe_recipe = {}
        self.matched_oe = False

    def add_layer(self, layer):
        self.layer = layer

    @staticmethod
    def filter_version_string(version):
        # Remove +git*
        # Remove -snapshot*
        ret_version = re.sub(r"\+git.*", r"+gitX", version, flags=re.IGNORECASE)
        return ret_version

    @staticmethod
    def get_epoch_and_version(version):
        arr = version.split(':')
        if len(arr) > 1:
            return arr[0], Recipe.filter_version_string(':'.join(arr[1:]))
        return '', Recipe.filter_version_string(version)

    def print_recipe(self):
        logging.info(f"Processed Recipe '{self.name}': {self.layer}/{self.name}/{self.version}")
