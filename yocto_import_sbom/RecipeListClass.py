import os.path
import re
import logging
import shutil
import tempfile

from .RecipeClass import Recipe
from .BBClass import BB


class RecipeList:
    def __init__(self):
        self.recipes = []

    def count(self):
        return len(self.recipes)

    def count_recipes_without_layer(self):
        count_nolayer = 0
        for recipe in self.recipes:
            if not recipe.layer:
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
                    recipe.version = version
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

    def check_recipes_in_oe(self, conf, oe):
        recipes_in_oe = 0
        exact_recipes_in_oe = 0
        changed_layers = 0
        exact_layers = 0
        for recipe in self.recipes:
            recipe.oe_recipe, recipe.oe_layer, exact_ver, exact_layer = oe.get_recipe(conf, recipe)
            if recipe.oe_recipe != {}:
                recipes_in_oe += 1
                if not exact_layer:
                    changed_layers += 1
                else:
                    exact_layers += 1
            if exact_ver:
                exact_recipes_in_oe += 1

        # logging.info(f"- {recipes_in_oe} out of {self.count()} total recipes found in OE data ({exact_recipes_in_oe} "
        #              f"exact version matches and {changed_layers} recipe layers modified)")
        logging.info("")
        logging.info(f"SUMMARY OE MATCH DATA:")
        logging.info(f"- {self.count()} Total Recipes")
        logging.info(f"- {recipes_in_oe} Recipes found in OE Data:")
        logging.info(f"    - {exact_recipes_in_oe} with exact version match")
        logging.info(f"    - {recipes_in_oe - exact_recipes_in_oe} with close version match (mapped to closest version)")
        logging.info(f"    - {exact_layers} with the same layer as OE")
        logging.info(f"    - {changed_layers} exist in different OE layer (mapped to original)")

    def scan_pkg_download_files(self, conf, bom):
        all_pkg_files = BB.get_pkg_files(conf)
        all_download_files = BB.get_download_files(conf)
        found_files = self.find_files(conf, all_pkg_files, all_download_files)
        tdir = self.copy_files(found_files)
        if tdir and bom.run_detect_sigscan(conf, tdir):
            return True
        return False

    def find_files(self, conf, all_download_files, all_pkg_files):
        found_files = []
        for recipe in self.recipes:
            if not conf.scan_all_packages and recipe.matched_in_bom:
                continue
            found = False
            recipe_esc = re.escape(recipe.name)
            ver_esc = re.escape(recipe.version)
            download_regex = re.compile(rf"^{recipe_esc}[_-]v?{ver_esc}[.-].*$")
            pkg_regex = re.compile(rf"^(lib)?{recipe_esc}\d*[_-]v?{ver_esc}[+.-].*\.{conf.image_pkgtype}")

            for path in all_download_files:
                filename = os.path.basename(path)
                download_res = download_regex.match(filename)
                if download_res is not None:
                    found_files.append(path)
                    found = True
                    logging.info(f"- Recipe:{recipe.name}/{recipe.version} - Located download file: {path}")

            if found:
                continue

            for path in all_pkg_files:
                filename = os.path.basename(path)
                # pattern = f"{os.path.join(global_values.pkg_dir, global_values.machine)}/" \
                #           f"{recipe}[-_]{ver}-*.{global_values.image_pkgtype}"
                pkg_res = pkg_regex.match(filename)

                if pkg_res is not None:
                    found_files.append(path)
                    logging.info(f"- Recipe:{recipe.name}/{recipe.version} - Located package file: {path}")
                    found = True

            if not found:
                logging.info(f"- Recipe:{recipe.name}/{recipe.version} - No package file found")

        return found_files

    @staticmethod
    def copy_files(files):
        temppkgdir = tempfile.mkdtemp(prefix="bd_sig_pkgs")

        # print(temppkgdir)
        count = 0
        for file in files:
            try:
                shutil.copy(file, temppkgdir)
                count += 1
            except Exception as e:
                logging.warning(f"Unable to copy package file {file} to temporary scan folder - {e}")

        logging.info(f"Copying recipe package files")
        logging.info(f"- Copied {count} package files ...")
        if count > 0:
            return temppkgdir
        else:
            return ''

    def check_recipes_in_bom(self, conf, bom):

        in_bom = []
        not_in_bom = []
        matched_oe_not_in_bom = []
        not_matched_oe_not_in_bom = []
        not_matched_oe_in_bom = []
        logging.info(f"Missing Recipes:")
        for recipe in self.recipes:
            fullid = recipe.full_id()

            if not recipe.check_in_bom(bom):
                not_in_bom.append(fullid)
                if recipe.matched_oe:
                    matched_oe_not_in_bom.append(fullid)
                    logging.info(f"- Recipe {fullid}: Matched in OE data but NOT found in BOM")
                else:
                    not_matched_oe_not_in_bom.append(fullid)
                    logging.debug(f"- Recipe {fullid}: NOT matched in OE data and NOT found in BOM")
            else:
                in_bom.append(fullid)
                recipe.matched_in_bom = True
                if not recipe.matched_oe:
                    not_matched_oe_in_bom.append(fullid)
                    # logging.debug(f"- Recipe {fullid}: Not matched in OE data but found in BOM")
            #     logging.info(f"- Recipe {recipe.name}/{recipe.version}: Found in BOM")

        logging.info("")
        logging.info(" Summary of Components Mapped in Black Duck BOM:")
        logging.info(f"- Total recipes in Yocto project - {self.count()}")
        logging.info(f"- Total recipes matched in BOM - {bom.count_comps()}")
        logging.info(f"    - Of which {len(not_matched_oe_in_bom)} not matched in OE data")
        logging.info(f"- Recipes NOT in BOM - {len(not_in_bom)}")
        logging.info(f"    - Of which {len(matched_oe_not_in_bom)} matched in OE data")
        logging.info(f"    - Of which {len(not_matched_oe_not_in_bom)} not matched in OE data")

        if conf.recipe_report != '':
            try:
                with open(conf.recipe_report, "w") as repfile:
                    repfile.write(f"RECIPES IN BOM ({len(in_bom)}):\n")
                    repfile.write("\n".join(in_bom))
                    repfile.write(f"\n\nRECIPES IN BOM - NOT MATCHED IN OE DATA ({len(not_matched_oe_in_bom)}):\n")
                    repfile.write("\n".join(not_matched_oe_in_bom))
                    repfile.write(f"\n\nRECIPES NOT IN BOM - NOT MATCHED IN OE DATA ({len(not_matched_oe_not_in_bom)}):\n")
                    repfile.write("\n".join(not_matched_oe_not_in_bom))
                    repfile.write(f"\n\nRECIPES NOT IN BOM - MATCHED IN OE DATA ({len(matched_oe_not_in_bom)}):\n")
                    repfile.write("\n".join(matched_oe_not_in_bom))
                logging.info(f"Output full recipe report to '{conf.recipe_report}'")
            except IOError as error:
                logging.error(f"Unable to write recipe report file {conf.recipe_report} - {error}")
