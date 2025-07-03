import logging
# import sys
import datetime
from random import randint
import json
import tempfile

# from .RecipeClass import Recipe
# from .RecipeListClass import RecipeList


class SBOM:
    def __init__(self, proj, ver, sbom_version='1.0'):
        self.sbom_version = sbom_version
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
            # "name": self.quote(f"{proj}-{ver}-" + mytime.strftime("%Y%m%dT%H%M%S")),
            "name": self.quote(f"{proj}-{ver}-" + self.sbom_version),
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

    def add_recipe(self, recipe: "Recipe", clean_version=False):
        spdxid = self.create_spdx_ident()
        if recipe.oe_recipe == {}:
            if recipe.layer:
                recipe_layer = recipe.layer
            else:
                recipe_layer = 'meta'
            recipe_name = recipe.name
            recipe_version = recipe.version
            if clean_version:
                recipe_version = recipe.clean_version_string()
            if recipe.epoch:
                recipe_version = f"{recipe.epoch}:{recipe_version}"
            else:
                recipe_version = recipe_version
            if recipe.release:
                recipe_pr = recipe.release
            else:
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

        # if recipe_layer == 'openemdedded-core':
        #     recipe_layer = 'meta'
        # if recipe_version.endswith('+git'):
        #     recipe_version = recipe_version.replace('+git', '+gitX')

        recipe_name = self.filter_special_chars(recipe_name)
        if not clean_version:
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
        if recipe.license:
            package_json["licenseConcluded"] = recipe.license
            package_json["licenseDeclared"] = recipe.license

        self.json['packages'].append(package_json)
        rel_json = {
            "spdxElementId": self.quote(f"SPDXRef-package-{spdxid}"),
            "relationshipType": "DYNAMIC_LINK",
            "relatedSpdxElement": self.quote(f"SPDXRef-package-{self.package_id}")
        }
        self.json["relationships"].append(rel_json)

    def add_component(self, compname, compversion, orig_href):
        spdxid = self.create_spdx_ident()
        name = self.filter_special_chars(compname)
        version = self.filter_special_chars(compversion)
        # 'https://sca247.poc.blackduck.com/api/components/5baf441a-8153-44f7-88d7-726c943b03d0/versions/60ea79ce-2204-4144-be58-3ace36b4c080/origins/33842216-89c3-49c9-a791-adbc08a71249'

        package_json = {
            "SPDXID": self.quote(f"SPDXRef-package-{spdxid}"),
            "downloadLocation": "NOASSERTION",
            "externalRefs": [],
            "name": self.quote(name),
            "versionInfo": self.quote(f"{version}")
        }
        href_arr = orig_href.split('/')
        if len(href_arr) <= 9:
            return
        compid = href_arr[5]
        verid = href_arr[7]
        origid = href_arr[9]
        package_json['externalRefs'].append(
                {
                    "referenceCategory": "OTHER",
                    "referenceLocator": origid,
                    "referenceType": "BlackDuck-ComponentOrigin"
                })
        package_json['externalRefs'].append(
                {
                    "referenceCategory": "OTHER",
                    "referenceLocator": verid,
                    "referenceType": "BlackDuck-ComponentVersion"
                })
        package_json['externalRefs'].append(
                {
                    "referenceCategory": "OTHER",
                    "referenceLocator": compid,
                    "referenceType": "BlackDuck-Component"
                })

        self.json['packages'].append(package_json)
        rel_json = {
            "spdxElementId": self.quote(f"SPDXRef-package-{spdxid}"),
            "relationshipType": "DYNAMIC_LINK",
            "relatedSpdxElement": self.quote(f"SPDXRef-package-{self.package_id}")
        }
        self.json["relationships"].append(rel_json)

    def process_recipes(self, reclist: "RecipeList"):
        for recipe in reclist:
            self.add_recipe(recipe)

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
        # return val
        newval = val.replace(':', '%3A')
        newval = newval.replace('+', '%2B')
        return newval
