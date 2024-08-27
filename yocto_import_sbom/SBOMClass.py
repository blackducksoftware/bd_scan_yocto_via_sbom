import logging
# import sys
import datetime
from random import randint
import json
import tempfile


class SBOM:
    def __init__(self, proj, ver):
        self.package_id = self.create_spdx_ident()
        hex_string = self.create_spdx_ident()
        self.namespace = f"https://blackducksoftware.github.io/spdx/{proj}-{hex_string}"
        self.file = ''

        mytime = datetime.datetime.now()
        mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        self.json = {
            "SPDXID": "SPDXRef-DOCUMENT",
            "spdxVersion": "SPDX-2.3",
            "creationInfo": {
                "created": self.quote(mytime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
                "creators": [
                    "Organization: COMPANY NAME",
                    "Tool: Black Duck Hub-2024.4.0"
                ],
                "licenseListVersion": "3.13"
            },
            "name": self.quote(f"{proj}-{ver}"),
            "documentDescribes": [
                self.quote(f"SPDXRef-package-{self.package_id}")
            ],
            "documentNamespace": self.quote(self.namespace),
            "packages": [
                {
                    "SPDXID": self.quote(f"SPDXRef-package-{self.package_id}"),
                    "downloadLocation": "NOASSERTION",
                    "externalRefs": [
                        {
                            "referenceCategory": "OTHER",
                            "referenceLocator": self.quote(self.package_id),
                            "referenceType": "BlackDuck-Version"
                        }
                    ],
                    "filesAnalyzed": False,
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": "NOASSERTION",
                    "name": self.quote(proj),
                    "originator": "NOASSERTION",
                    "supplier": "NOASSERTION",
                    "versionInfo": self.quote(ver)
                }
            ],
            "relationships": []
        }

    @staticmethod
    def quote(astr):
        name = ''
        remove_chars = ['"', "'"]
        for i in remove_chars:
            name = astr.replace(i, '')
        return name

    @staticmethod
    def create_spdx_ident():
        # "SPDXRef-package-59f5a8a4-d154-42f5-a995-b89a35aad53c"
        hex1 = hex(randint(0, 4294967295))
        hex2 = hex(randint(0, 65535))
        hex3 = hex(randint(0, 65535))
        hex4 = hex(randint(0, 65535))
        hex5 = hex(randint(0, 281474976710655))

        rand_hex_str = f"{hex1}-{hex2}-{hex3}-{hex4}-{hex5}"
        return rand_hex_str

    def add_package(self, recipe):
        spdxid = self.create_spdx_ident()
        if recipe.oe_recipe == {}:
            recipe_layer = recipe.layer
            recipe_name = recipe.name
            if recipe.epoch:
                recipe_version = f"{recipe.epoch}:{recipe.version}"
            else:
                recipe_version = recipe.version
            recipe_pr = 'r0'
        else:
            recipe_layer = recipe.oe_layer['name']
            if recipe_layer == 'openembedded-core':
                recipe_layer = 'meta'
            recipe_name = recipe.oe_recipe['pn']
            if recipe.oe_recipe['pe']:
                recipe_version = f"{recipe.oe_recipe['pe']}:{recipe.oe_recipe['pv']}"
            else:
                recipe_version = recipe.oe_recipe['pv']
            if recipe.oe_recipe['pr']:
                recipe_pr = recipe.oe_recipe['pr']
            else:
                recipe_pr = 'r0'

        if recipe_layer == 'openemdedded-core':
            recipe_layer = 'meta'
        if recipe_version.endswith('+git'):
            recipe_version = recipe_version.replace('+git', '+gitX')

        recipe_name = self.filter_special_chars(recipe_name)
        recipe_version = self.filter_special_chars(recipe_version)

        package_json = {
            "SPDXID": self.quote(f"SPDXRef-package-{spdxid}"),
            "downloadLocation": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceLocator": self.quote(
                        f"pkg:openembedded/{recipe_layer}/{recipe_name}@{recipe_version}-{recipe_pr}"),
                    "referenceType": "purl"
                }
            ],
            "name": self.quote(recipe_name),
            "versionInfo": self.quote(f"{recipe_version}")
        }
        self.json['packages'].append(package_json)
        rel_json = {
            "spdxElementId": self.quote(f"SPDXRef-package-{spdxid}"),
            "relationshipType": "DYNAMIC_LINK",
            "relatedSpdxElement": self.quote(f"SPDXRef-package-{self.package_id}")
        }
        self.json["relationships"].append(rel_json)

    def process_recipes(self, reclist):
        for recipe in reclist:
            self.add_package(recipe)

    def output(self, output_file):
        try:
            if not output_file:
                lfile = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix='.json')
                lfile.write(json.dumps(self.json, indent=4))
                lfile.close()
                output_file = lfile.name
            else:
                with open(output_file, "w") as ofile:
                    json.dump(self.json, ofile, indent=4)

        except Exception as e:
            logging.error('Unable to create output SPDX file \n' + str(e))
            return False

        self.file = output_file
        return True

    @staticmethod
    def filter_special_chars(val):
        newval = val.replace(':', '%3A')
        newval = newval.replace('+', '%2B')
        return newval
