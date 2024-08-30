import os
import requests
import json
import logging
import re
from semver import Version

from .RecipeClass import Recipe


class OE:
    def __init__(self, conf):
        logging.info(f"Processing OE recipes and layers ...")
        self.layers = self.get_oe_layers(conf)
        self.layerid_dict = self.process_layers()
        self.layerbranches = self.get_oe_layerbranches(conf)
        self.layerbranchid_dict = self.process_layerbranches()
        self.recipes = self.get_oe_recipes(conf)
        self.recipename_dict = self.process_recipes()
        self.branches = self.get_oe_branches(conf)
        self.branchid_dict = self.process_branches()

    @staticmethod
    def get_oe_layers(conf):
        logging.info("- Getting OE layers")
        oe_data_file_exists = False
        if conf.oe_data_folder:
            lfile = os.path.join(conf.oe_data_folder, 'oe_layers.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/layerItems/"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                layer_dict = json.loads(r.text)
                json_object = json.dumps(layer_dict, indent=4)

                if conf.oe_data_folder:
                    # Writing to sample.json
                    with open(lfile, "w") as outfile:
                        logging.info(f"- writing to file {lfile}")
                        outfile.write(json_object)

                return layer_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of layers - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    logging.info(f"- loaded from file {lfile}")
                    return json.load(infile)

            except Exception as e:
                logging.warning(f"Error processing OE layers {e} from file - skipping")

        return {}

    @staticmethod
    def get_oe_recipes(conf):
        logging.info("- Getting OE recipes")
        oe_data_file_exists = False
        if conf.oe_data_folder:
            lfile = os.path.join(conf.oe_data_folder, 'oe_recipes.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/recipes/"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                recipe_dict = json.loads(r.text)
                json_object = json.dumps(recipe_dict, indent=4)

                if conf.oe_data_folder:
                    # Writing to sample.json
                    with open(lfile, "w") as outfile:
                        logging.info(f"- writing to file {lfile}")
                        outfile.write(json_object)

                return recipe_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of recipes - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    logging.info(f"- loaded from file {lfile}")
                    recipe_dict = json.load(infile)
                return recipe_dict

            except Exception as e:
                logging.warning(f"Error processing OE recipes from file {e} - skipping")

        return {}

    @staticmethod
    def get_oe_layerbranches(conf):
        logging.info("- Getting OE layerbranches")

        oe_data_file_exists = False
        if conf.oe_data_folder:
            lfile = os.path.join(conf.oe_data_folder, 'oe_layerbranches.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/layerBranches/"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                layerbranches_dict = json.loads(r.text)
                json_object = json.dumps(layerbranches_dict, indent=4)

                if conf.oe_data_folder:
                    # Writing to sample.json
                    with open(lfile, "w") as outfile:
                        logging.info(f"- writing to file {lfile}")
                        outfile.write(json_object)

                return layerbranches_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of layerbranches - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    logging.info(f"- loaded from file {lfile}")
                    layerbranches_dict = json.load(infile)
                return layerbranches_dict

            except Exception as e:
                logging.warning(f"Error processing OE layerbranches from file {e} - skipping")

        return {}

    @staticmethod
    def get_oe_branches(conf):
        logging.info("- Getting OE branches")

        oe_data_file_exists = False
        if conf.oe_data_folder:
            lfile = os.path.join(conf.oe_data_folder, 'oe_branches.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/branches/"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                branches_dict = json.loads(r.text)
                json_object = json.dumps(branches_dict, indent=4)

                if conf.oe_data_folder:
                    # Writing to sample.json
                    with open(lfile, "w") as outfile:
                        logging.info(f"- writing to file {lfile}")
                        outfile.write(json_object)

                return branches_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of branches - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    logging.info(f"- loaded from file {lfile}")
                    layerbranches_dict = json.load(infile)
                return layerbranches_dict

            except Exception as e:
                logging.warning(f"Error processing OE branches from file {e} - skipping")

        return {}

    def process_layers(self):
        try:
            layer_dict = {}
            for layer in self.layers:
                layer_dict[layer['id']] = layer
            return layer_dict
        except Exception as e:
            logging.warning(f"Cannot process layer {e}")

        return {}

    def process_recipes(self):
        try:
            recipe_dict = {}
            for recipe in self.recipes:
                if recipe['pn'] in recipe_dict.keys():
                    recipe_dict[recipe['pn']].append(recipe)
                else:
                    recipe_dict[recipe['pn']] = [recipe]
            return recipe_dict
        except Exception as e:
            logging.warning(f"Cannot process recipe {e}")
        return {}

    def process_layerbranches(self):
        try:
            layerbranch_dict = {}
            for layerbranch in self.layerbranches:
                layerbranch_dict[layerbranch['id']] = layerbranch
            return layerbranch_dict
        except Exception as e:
            logging.warning(f"Cannot process layerbranch {e}")
        return {}

    def process_branches(self):
        try:
            branch_dict = {}
            for branch in self.branches:
                branch_dict[branch['id']] = branch
            return branch_dict
        except Exception as e:
            logging.warning(f"Cannot process branch {e}")

        return {}

    def get_layer_by_layerbranchid(self, id):
        try:
            layerid = self.layerbranchid_dict[id]['layer']
            return self.layerid_dict[layerid]
        except KeyError as e:
            logging.warning(f"Cannot get layer by layerbranchid {e}")
        return {}

    def get_branch_by_layerbranchid(self, id):
        try:
            branchid = self.layerbranchid_dict[id]['branch']
            return self.branchid_dict[branchid]
        except KeyError as e:
            logging.warning(f"Cannot get branch by layerbranchid {e}")
        return {}

    def compare_recipes(self, conf, recipe, oe_recipe, best_oe_recipe):
        # Returns:
        # - Bool - Match found
        # - Bool - Exact version match
        oe_ver_equal = False

        try:
            if best_oe_recipe != {}:
                logging.debug(f"Comparing {recipe.name}/{recipe.version} to {oe_recipe['pn']}/{oe_recipe['pv']} "
                              f"(best so far = {best_oe_recipe['pn']}/{best_oe_recipe['pv']})")
            else:
                logging.debug(f"Comparing {recipe.name}/{recipe.version} to {oe_recipe['pn']}/{oe_recipe['pv']}")

            pref = False

            oe_ver = Recipe.filter_version_string(oe_recipe['pv'])
            if best_oe_recipe != {}:
                best_oe_ver = Recipe.filter_version_string(best_oe_recipe['pv'])
            else:
                best_oe_ver = ''

            if oe_ver == best_oe_ver:
                oe_ver_equal = True

            if recipe.version != best_oe_ver:
                if recipe.version == oe_ver:
                    pref = True
                else:
                    semver, rest = self.coerce_version(recipe.version)
                    oe_semver, oe_rest = self.coerce_version(oe_ver)
                    best_oe_semver, best_oe_rest = self.coerce_version(best_oe_ver)
                    if semver is not None and oe_semver is not None and oe_semver <= semver:
                        if self.check_semver_distance(conf, semver, oe_semver):
                            if best_oe_semver is not None:
                                if oe_semver == best_oe_semver:
                                    if len(oe_ver) < len(best_oe_ver):
                                        pref = True
                                    oe_ver_equal = True
                                elif semver >= oe_semver > best_oe_semver:
                                    if (semver.major - best_oe_semver.major) > (semver.major - oe_semver.major):
                                        pref = True
                                    elif (semver.minor - best_oe_semver.minor) > (semver.minor - oe_semver.minor):
                                        pref = True
                                    elif (semver.patch - best_oe_semver.patch) > (semver.patch - oe_semver.patch):
                                        pref = True
                            else:
                                pref = True

            if not pref and oe_ver_equal and recipe.epoch and oe_recipe['pe']:
                if best_oe_recipe['pe'] and recipe.epoch and oe_recipe['pe']:
                    if (int(oe_recipe['pe']) <= int(recipe.epoch) and (int(recipe.epoch) - int(oe_recipe['pe'])) <=
                            (int(recipe.epoch) - int(best_oe_recipe['pe']))):
                        pref = True
                else:
                    pref = True

            if not pref and best_oe_recipe != {}:
                oe_layer = self.get_layer_by_layerbranchid(oe_recipe['layerbranch'])
                oe_branch = self.get_branch_by_layerbranchid(oe_recipe['layerbranch'])
                branch_sort_priority = self.get_branch_priority(oe_branch)

                best_oe_layer = self.get_layer_by_layerbranchid(best_oe_recipe['layerbranch'])
                best_oe_branch = self.get_branch_by_layerbranchid(best_oe_recipe['layerbranch'])
                if best_oe_branch != {}:
                    best_branch_sort_priority = self.get_branch_priority(best_oe_branch)
                else:
                    best_branch_sort_priority = 999

                if (oe_ver_equal and branch_sort_priority < best_branch_sort_priority and
                        oe_layer['index_preference'] >= best_oe_layer['index_preference']):
                    pref = True

            if pref:
                return True, (recipe.version == oe_ver)
        except Exception as e:
            logging.error(f"Error in compare_recipes(): {e}")
        return False, False

    @staticmethod
    def get_branch_priority(branch):
        if branch is not None and 'sort_priority' in branch and branch['sort_priority'] is not None \
                and str(branch['sort_priority']).isnumeric():
            branch_sort_priority = branch['sort_priority']
        else:
            branch_sort_priority = 999
        return branch_sort_priority

    def get_recipe(self, conf, recipe):
        # need to look for closest version match
        # Return:
        # - OE Recipe
        # - OE Layer
        # - Bool exact version match
        # - Bool exact layer match
        try:
            best_recipe = {}
            exact_ver = False
            exact_layer = False

            if recipe.name in self.recipename_dict.keys():
                for oe_recipe in self.recipename_dict[recipe.name]:
                    # print(f"{oe_recipe['pn']} - {oe_recipe['pv']}")
                    match, exact_ver_temp = self.compare_recipes(conf, recipe, oe_recipe, best_recipe)
                    if match:
                        best_recipe = oe_recipe
                        recipe.matched_oe = True
                        if exact_ver_temp:
                            exact_ver = True

            if recipe.epoch:
                recipe_ver = f"{recipe.epoch}:{recipe.orig_version}"
            else:
                recipe_ver = recipe.orig_version

            if best_recipe != {}:
                if best_recipe['pe']:
                    best_ver = f"{best_recipe['pe']}:{best_recipe['pv']}"
                else:
                    best_ver = best_recipe['pv']
            else:
                logging.debug(f"Recipe {recipe.name}: {recipe.layer}/{recipe.name}/{recipe_ver} - "
                              f"No close (previous) OE version match found")
                return {}, {}, False, False

            best_layer = self.get_layer_by_layerbranchid(best_recipe['layerbranch'])

            logging.debug(f"Recipe {recipe.name}: {recipe.layer}/{recipe.name}/{recipe_ver} - OE near match "
                          f"{best_layer['name']}/{best_recipe['pn']}/{best_ver}-{best_recipe['pr']}")
            if recipe.layer == best_layer['name'] or (recipe.layer == 'meta' and best_layer['name'] == 'openembedded-core'):
                exact_layer = True
            return best_recipe, best_layer, exact_ver, exact_layer

        except KeyError as e:
            logging.warning(f"Error getting nearest OE recipe - {e}")
        return {}, {}, False, False

    @staticmethod
    def coerce_version(version: str):
        if not version:
            return None, ''

        if Version.is_valid(version):
            return Version.parse(version), ''

        """
        Convert an incomplete version string into a semver-compatible Version
        object

        * Tries to detect a "basic" version string (``major.minor.patch``).
        * If not enough components can be found, missing components are
            set to zero to obtain a valid semver version.

        :param str version: the version string to convert
        :return: a tuple with a :class:`Version` instance (or ``None``
            if it's not a version) and the rest of the string which doesn't
            belong to a basic version.
        :rtype: tuple(:class:`Version` | None, str)
        """
        baseversion = re.compile(
            r"""[vV]?0?
                (?P<major>0|[1-9]\d*)
                (\.0?
                (?P<minor>0|[1-9]\d*)
                (\.0?
                    (?P<patch>0|[1-9]\d*)
                )?
                )?
            """,
            re.VERBOSE,
        )

        match = baseversion.search(version)
        if not match:
            return None, version

        ver = {
            key: 0 if value is None else value for key, value in match.groupdict().items()
        }
        ver = Version(**ver)
        rest = match.string[match.end():]  # noqa:E203
        return ver, rest

    @staticmethod
    def calc_specified_version_distance(distance_str):
        arr = distance_str.split('.')
        for entry in arr:
            if not entry.isnumeric():
                return [-1, -1, -1]

        if len(arr) == 3:
            return [int(arr[0]), int(arr[1]), int(arr[2])]
        elif len(arr) == 2:
            return [0, int(arr[0]), int(arr[1])]
        elif len(arr) == 1:
            return [0, 0, int(arr[0])]
        else:
            return [0, 0, 0]

    @staticmethod
    def check_semver_distance(conf, ver1, ver2):
        # Is ver2 less than ver1 AND
        # ver2 is within the distance of ver1
        if conf.max_oe_version_distance[0] > 0:
            if ver1.major - ver2.major <= conf.max_oe_version_distance[0]:
                return True
        elif conf.max_oe_version_distance[1] > 0:
            if (ver1.major == ver2.major and
               ver1.minor - ver2.minor <= conf.max_oe_version_distance[1]):
                return True
        elif conf.max_oe_version_distance[2] > 0:
            if (ver1.major == ver2.major and ver1.minor == ver2.minor and
                    ver1.patch - ver2.patch <= conf.max_oe_version_distance[2]):
                return True
        return False
