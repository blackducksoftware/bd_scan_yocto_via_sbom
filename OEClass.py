import os
import requests
import json
import logging
import re
from RecipeClass import Recipe


class OE:
    def __init__(self):
        logging.info(f"Processing OE recipes and layers ...")
        self.layers = self.get_oe_layers()
        self.layerid_dict = self.process_layers()
        self.layerbranches = self.get_oe_layerbranches()
        self.layerbranchid_dict = self.process_layerbranches()
        self.recipes = self.get_oe_recipes()
        self.recipename_dict = self.process_recipes()
        self.branches = self.get_oe_branches()
        self.branchid_dict = self.process_branches()

    @staticmethod
    def get_oe_layers():
        lfile = 'oe_layers.json'
        if not os.path.exists(lfile):
            try:
                url = "https://layers.openembedded.org/layerindex/api/layerItems/"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                layer_dict = json.loads(r.text)
                json_object = json.dumps(layer_dict, indent=4)

                # Writing to sample.json
                with open(lfile, "w") as outfile:
                    outfile.write(json_object)
                return layer_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of layers - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    return json.load(infile)

            except Exception as e:
                logging.warning(f"Error processing OE layers {e} from file - skipping")

        return {}

    @staticmethod
    def get_oe_recipes():
        lfile = 'oe_recipes.json'
        if not os.path.exists(lfile):
            try:
                url = "https://layers.openembedded.org/layerindex/api/recipes"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                recipe_dict = json.loads(r.text)
                json_object = json.dumps(recipe_dict, indent=4)

                # Writing to sample.json
                with open(lfile, "w") as outfile:
                    outfile.write(json_object)

                return recipe_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of recipes - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    recipe_dict = json.load(infile)
                return recipe_dict

            except Exception as e:
                logging.warning(f"Error processing OE recipes from file {e} - skipping")

        return {}

    @staticmethod
    def get_oe_layerbranches():
        lfile = 'oe_layerbranches.json'
        if not os.path.exists(lfile):
            try:
                url = "https://layers.openembedded.org/layerindex/api/layerBranches"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                layerbranches_dict = json.loads(r.text)
                json_object = json.dumps(layerbranches_dict, indent=4)

                # Writing to sample.json
                with open(lfile, "w") as outfile:
                    outfile.write(json_object)

                return layerbranches_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of layerbranches - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
                    layerbranches_dict = json.load(infile)
                return layerbranches_dict

            except Exception as e:
                logging.warning(f"Error processing OE layerbranches from file {e} - skipping")

        return {}

    @staticmethod
    def get_oe_branches():
        lfile = 'oe_branches.json'
        if not os.path.exists(lfile):
            try:
                url = "https://layers.openembedded.org/layerindex/api/branches"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                branches_dict = json.loads(r.text)
                json_object = json.dumps(branches_dict, indent=4)

                # Writing to sample.json
                with open(lfile, "w") as outfile:
                    outfile.write(json_object)

                return branches_dict

            except ConnectionError as e:
                logging.warning(f"Unable to connect to openembedded.org to get list of branches - error {e}")
        else:
            try:
                with open(lfile, "r") as infile:
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

    def get_recipe(self, layername, recipename, version):
        # Returns:
        # - recipe dict
        # - layer dict
        # - exactmatch (boolean)
        try:
            if layername == 'meta':
                layername = 'openembedded-core'

            best_recipe = {}
            best_layer = {}
            best_layer_pref = -1
            best_branch_sort_priority = 999
            exact_match = False
            if recipename in self.recipename_dict.keys():
                for oe_recipe in self.recipename_dict[recipename]:
                    if recipename == 'python3-ply':
                        print()
                    add_match = False
                    oe_layer = self.get_layer_by_layerbranchid(oe_recipe['layerbranch'])
                    oe_branch = self.get_branch_by_layerbranchid(oe_recipe['layerbranch'])
                    if oe_branch is not None and oe_branch['sort_priority'] is not None \
                            and str(oe_branch['sort_priority']).isnumeric():
                        branch_sort_priority = oe_branch['sort_priority']
                    else:
                        branch_sort_priority = 999

                    if oe_layer == {}:
                        continue

                    oe_ver = oe_recipe['pv']
                    oe_ver = Recipe.filter_version_string(oe_ver)
                    if oe_ver == version:
                        # Exact match
                        if (oe_layer['index_preference'] >= best_layer_pref and
                                branch_sort_priority < best_branch_sort_priority):
                            add_match = True
                    else:
                        # No exact match
                        ver_split = re.split(r"[+\-]", version)
                        oever_split = re.split(r"[+\-]", oe_recipe['pv'])
                        if ver_split[0] == oever_split[0]:
                            # if oe_layer['name'] == layername:
                            # logging.debug(f"Recipe {recipename}: {layername}/{recipename}/{version} - matched EXACTLY in OE data")
                            # return recipe, oe_layer, True
                            if oe_layer['index_preference'] > best_layer_pref and oe_recipe['pv'] != '':
                                add_match = True
                    if add_match:
                        best_recipe = oe_recipe
                        best_layer = oe_layer
                        best_layer_pref = oe_layer['index_preference']
                        best_branch_sort_priority = branch_sort_priority

            # No exact match found - choose the first recipe
            if best_recipe != {}:
                if exact_match:
                    logging.debug(f"Recipe {recipename}: {layername}/{recipename}/{version} - matched EXACTLY "
                                  f"{best_layer['name']}/{best_recipe['pn']}/{best_recipe['pv']}-{best_recipe['pr']}")
                else:
                    logging.debug(f"Recipe {recipename}: {layername}/{recipename}/{version} - PARTIAL OE match "
                                  f"{best_layer['name']}/{best_recipe['pn']}/{best_recipe['pv']}-{best_recipe['pr']}")
            else:
                logging.debug(f"Recipe {recipename}: {layername}/{recipename}/{version} - NO MATCH in OE data")
            return best_recipe, best_layer, False

        except KeyError as e:
            logging.warning(f"Cannot get recipe by name,version {e}")

        return {}, {}, False
