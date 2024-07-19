import os
import requests
import json
import logging
import re

from . import global_values
from .RecipeClass import Recipe


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
        oe_data_file_exists = False
        if global_values.oe_data_folder != '':
            lfile = os.path.join(global_values.oe_data_folder, 'oe_layers.json')
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

                if global_values.oe_data_folder != '':
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
        oe_data_file_exists = False
        if global_values.oe_data_folder != '':
            lfile = os.path.join(global_values.oe_data_folder, 'oe_recipes.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        lfile = 'oe_recipes.json'
        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/recipes"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                recipe_dict = json.loads(r.text)
                json_object = json.dumps(recipe_dict, indent=4)

                if global_values.oe_data_folder != '':
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
        oe_data_file_exists = False
        if global_values.oe_data_folder != '':
            lfile = os.path.join(global_values.oe_data_folder, 'oe_layerbranches.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/layerBranches"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                layerbranches_dict = json.loads(r.text)
                json_object = json.dumps(layerbranches_dict, indent=4)

                if global_values.oe_data_folder != '':
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
        oe_data_file_exists = False
        if global_values.oe_data_folder != '':
            lfile = os.path.join(global_values.oe_data_folder, 'oe_branches.json')
            if os.path.exists(lfile):
                oe_data_file_exists = True

        if not oe_data_file_exists:
            try:
                url = "https://layers.openembedded.org/layerindex/api/branches"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Status code {r.status_code}")

                branches_dict = json.loads(r.text)
                json_object = json.dumps(branches_dict, indent=4)

                if global_values.oe_data_folder != '':
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

    def get_recipe(self, recipe):
        # Returns:
        # - recipe dict
        # - layer dict
        # - exactmatch (boolean)
        try:
            best_recipe = {}
            best_layer = {}
            best_layer_pref = -1
            best_branch_sort_priority = 999
            recipe_exists_in_oe = False
            if recipe.name in self.recipename_dict.keys():
                recipe_exists_in_oe = True
                for oe_recipe in self.recipename_dict[recipe.name]:
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

                    oe_epoch, oe_ver = Recipe.get_epoch_and_version(oe_recipe['pv'])
                    if oe_ver == recipe.version:
                        # Exact match
                        if (oe_layer['index_preference'] >= best_layer_pref and
                                branch_sort_priority < best_branch_sort_priority):
                            add_match = True
                    else:
                        # No exact match
                        ver_split = re.split(r"[+\-]", recipe.version)
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
            if recipe.epoch != '':
                recipe_ver = f"{recipe.epoch}:{recipe.orig_version}"
            else:
                recipe_ver = recipe.orig_version

            if best_recipe != {}:
                if best_recipe['pe'] != '':
                    best_ver = f"{best_recipe['pe']}:{best_recipe['pv']}"
                else:
                    best_ver = best_recipe['pv']

                logging.debug(f"Recipe {recipe.name}: {recipe.layer}/{recipe.name}/{recipe_ver} - OE match "
                                  f"{best_layer['name']}/{best_recipe['pn']}/{best_ver}-{best_recipe['pr']}")
            else:
                logging.debug(f"Recipe {recipe.name}: {recipe.layer}/{recipe.name}/{recipe_ver} - "
                              f"NO MATCH in OE data (recipe exists in OE {recipe_exists_in_oe})")
            return best_recipe, best_layer, False

        except KeyError as e:
            logging.warning(f"Cannot get recipe by name,version {e}")

        return {}, {}, False
