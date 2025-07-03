import re
import logging

from .BOMClass import BOM


class Recipe:
    def __init__(self, name, version, rel=None, license=None):
        self.name = name
        self.orig_version = version
        self.epoch = ''
        self.version = self.filter_version_string(version)
        self.release = rel
        self.layer = ''
        self.spdxid = ''
        self.oe_layer = {}
        self.oe_recipe = {}
        self.matched_oe = False
        self.matched_in_bom = False
        self.recipename_in_oe = False
        self.matched_oe_exact = False
        self.license = license
        self.custom_component = False
        self.cpe_comp_href = ''

    def add_layer(self, layer):
        self.layer = layer

    @staticmethod
    def filter_version_string(version):
        # Remove +git*
        # Remove -snapshot*
        # ret_version = re.sub(r"\+git.*", r"+gitX", version, flags=re.IGNORECASE)

        ret_version = re.sub(r"AUTOINC.*", r"X", version, flags=re.IGNORECASE)
        return ret_version

    def clean_version_string(self):
        # Remove +git*
        # Remove -snapshot*
        # ret_version = re.sub(r"\+git.*", r"+gitX", version, flags=re.IGNORECASE)
        varr = re.split("[+_-]", self.version)
        ret_version = varr[0]
        return ret_version

    @staticmethod
    def get_epoch_and_version(version):
        arr = version.split(':')
        if len(arr) > 1:
            return arr[0], Recipe.filter_version_string(':'.join(arr[1:]))
        return '', Recipe.filter_version_string(version)

    def print_recipe(self):
        logging.info(f"Processed Recipe '{self.name}': {self.full_id()}")

    def check_in_bom(self, bom: BOM):
        return bom.check_recipe_in_bom(self)

    def full_id(self):
        return f"{self.layer}/{self.name}/{self.version}"

    def cpe_string(self, conf):
        # cpe:2.3:a:*:glibc:2.40:*:*:*:*:*:*:*
        ver = self.version.split('+')[0]
        name = self.name
        if conf.kernel_recipe in self.name:
            name = 'linux_kernel'

        cpe = f"cpe:2.3:a:*:{name}:{ver}:*:*:*:*:*:*:*"
        return cpe
