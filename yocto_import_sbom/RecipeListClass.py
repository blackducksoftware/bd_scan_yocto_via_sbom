from .RecipeClass import Recipe
import logging
import sys


class RecipeList:
    def __init__(self, lic_manifest_file, bitbake_layers_file):
        self.recipes = []
        self.process_licman_file(lic_manifest_file)
        self.process_bitbake_file(bitbake_layers_file)

    def process_licman_file(self, lic_manifest_file):
        recipes_total = 0
        try:
            with open(lic_manifest_file, "r") as lfile:
                lines = lfile.readlines()
                ver = ''
                recipe = ''
                for line in lines:
                    # PACKAGE NAME: name
                    # PACKAGE VERSION: ver
                    # RECIPE NAME: rname
                    # LICENSE: License
                    #
                    line = line.strip()
                    if line.startswith("PACKAGE VERSION:"):
                        ver = line.split(': ')[1]
                    elif line.startswith("RECIPE NAME:"):
                        recipe = line.split(': ')[1]

                    if recipe != '' and ver != '':
                        recipes_total += 1
                        rec_obj = Recipe(recipe, ver)
                        if not self.check_recipe_exists(recipe):
                            self.recipes.append(rec_obj)
                        ver = ''
                        recipe = ''

                logging.info(f"- {recipes_total} packages found in licman file ({self.count()} recipes)")

        except Exception as e:
            logging.error(f"Cannot read license manifest file '{lic_manifest_file}' - error '{e}'")
            sys.exit(2)

        return

    def process_bitbake_file(self, bitbake_file):
        try:
            with open(bitbake_file, "r") as bfile:
                lines = bfile.readlines()
            rec = ""
            bstart = False
            for rline in lines:
                rline = rline.strip()
                if bstart:
                    if rline.endswith(":"):
                        arr = rline.split(":")
                        rec = arr[0]
                    elif rec != "":
                        arr = rline.split()
                        if len(arr) > 1:
                            layer = arr[0]
                            ver = arr[1]
                            self.add_layer_to_recipe(rec, layer, ver)
                        rec = ""
                elif rline.endswith(": ==="):
                    bstart = True

            logging.info(f"- {self.count_recipes_without_layer()} recipes without layer reported from layer file")
        except Exception as e:
            logging.error(f"Cannot process bitbake-layers output file '{bitbake_file} - error {e}")
            sys.exit(2)

        return

    def count(self):
        return len(self.recipes)

    def count_recipes_without_layer(self):
        count_nolayer = 0
        for recipe in self.recipes:
            if recipe.layer == '':
                count_nolayer += 1
        return count_nolayer

    def check_recipe_exists(self, recipe_name):
        for recipe in self.recipes:
            if recipe.name == recipe_name:
                return True
        return False

    def add_layer_to_recipe(self, rec, layer, ver):
        epoch, version = Recipe.get_epoch_and_version(ver)
        for recipe in self.recipes:
            if recipe.name == rec:
                recipe.add_layer(layer)
                recipe.epoch = epoch
                if recipe.version != version and recipe.version in version:
                    recipe.version = ver
                return

    def print_recipes(self):
        for recipe in self.recipes:
            recipe.print_recipe()

    def get_layers(self):
        layers = []
        for recipe in self.recipes:
            if recipe.layer not in layers:
                layers.append(recipe.layer)
        return layers

    def check_recipes_in_oe(self, oe):
        for recipe in self.recipes:
            recipe.oe_recipe, recipe.oe_layer = oe.get_recipe(recipe)