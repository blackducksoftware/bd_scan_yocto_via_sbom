import os.path
import re
import logging
import shutil
import tempfile

from .RecipeClass import Recipe
from .BBClass import BB
# from .BOMClass import BOM
# from .ConfigClass import Config
from .SBOMClass import SBOM


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
                if recipe.version != '':
                    if recipe.version in version:
                        recipe.add_layer(layer)
                        recipe.epoch = epoch
                else:
                    recipe.add_layer(layer)
                    recipe.epoch = epoch
                    recipe.version = version
                return

    def add_rel_to_recipe(self, rec, rel):
        for recipe in self.recipes:
            if recipe.name == rec:
                recipe.release = rel
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

    def check_recipes_in_oe(self, conf: "Config", oe):
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

    def scan_pkg_download_files(self, conf: "Config", bom: "BOM"):
        all_pkg_files = BB.get_pkg_files(conf)
        all_download_files = BB.get_download_files(conf)
        found_files = self.find_files(conf, all_pkg_files, all_download_files)
        if len(found_files) > 0:
            tdir = self.copy_files(conf, found_files)
            if tdir and bom.run_detect_sigscan(conf, tdir):
                return len(found_files), True
            else:
                return len(found_files), False
        return 0, False

    def find_files(self, conf, all_pkg_files, all_download_files):
        found_files = []
        for recipe in self.recipes:
            if not conf.scan_all_packages and recipe.matched_in_bom:
                continue
            found = False
            recipe_esc = re.escape(recipe.name)
            ver_esc = re.escape(recipe.version)
            download_regex = re.compile(rf"^{recipe_esc}[_-]v?{ver_esc}[.-].*$")
            pkg_regex = re.compile(rf"^(lib)?{recipe_esc}\d*[_-]v?{ver_esc}[+.-].*\.{conf.image_package_type}")

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
    def copy_files(conf, files):
        try:
            temppkgdir = tempfile.mkdtemp(prefix="bd_sig_pkgs")
            proj_string = conf.bd_project + "_" + conf.bd_version
            temppkgdir = os.path.join(temppkgdir, proj_string)
            if not os.path.isdir(temppkgdir):
                # os.mkdir(temppkgdir)
                os.makedirs(temppkgdir, exist_ok=True)

            count = 0
            for file in files:
                    shutil.copy(file, temppkgdir)
                    count += 1

            logging.info(f"Copying recipe package files")
            logging.info(f"- Copied {count} package files ...")
            if count > 0:
                return temppkgdir

        except Exception as e:
            logging.error(f"Unable to copy package files {e}")
        return ''

    def report_recipes_in_bom(self, conf: "Config", bom: "BOM"):

        in_bom = []
        not_in_bom = []
        matched_oe_not_in_bom = []
        not_matched_oe_not_in_bom = []
        not_matched_oe_in_bom = []
        not_in_bom_recipename_in_oe = []
        logging.info(f"Missing Recipes:")
        count_missing = 0
        for recipe in self.recipes:
            fullid = recipe.full_id()

            if recipe.matched_oe_exact:
                fullid += " (OE EXACT VERSION)"
            elif recipe.matched_oe:
                fullid += f" (OE Closest version {recipe.oe_recipe['pv']}-{recipe.oe_recipe['pr']})"
            elif recipe.custom_component:
                fullid += f" (CUSTOM COMPONENT CREATED)"
            elif recipe.cpe_comp_href:
                fullid += f" (CPE MATCHED COMPONENT)"

            if not recipe.matched_in_bom:
                not_in_bom.append(fullid)
                if recipe.matched_oe:
                    matched_oe_not_in_bom.append(fullid)
                    logging.info(f"- Recipe {fullid}: Matched in OE data but NOT found in BOM")
                    count_missing += 1
                else:
                    not_matched_oe_not_in_bom.append(fullid)
                    logging.debug(f"- Recipe {fullid}: NOT matched in OE data and NOT found in BOM")
                    count_missing += 1
                if recipe.recipename_in_oe:
                    not_in_bom_recipename_in_oe.append(fullid)
            else:
                in_bom.append(fullid)
                if not recipe.matched_oe:
                    not_matched_oe_in_bom.append(fullid)
                    # logging.debug(f"- Recipe {fullid}: Not matched in OE data but found in BOM")
            #     logging.info(f"- Recipe {recipe.name}/{recipe.version}: Found in BOM")

        if count_missing == 0:
            logging.info(" - None")
            logging.info("")

        logging.info("")
        logging.info(" Summary of Components Mapped in Black Duck BOM:")
        logging.info(f"- Total recipes in Yocto project - {self.count()}")
        logging.info(f"- Total recipes matched in BOM - {bom.count_comps()}")
        logging.info(f"    - Of which {len(not_matched_oe_in_bom)} not matched in OE data")
        logging.info(f"- Recipes NOT in BOM - {len(not_in_bom)}")
        logging.info(f"    - Of which {len(matched_oe_not_in_bom)} matched in OE data")
        logging.info(f"    - Of which {len(not_matched_oe_not_in_bom)} not matched in OE data")
        logging.info(f"    - Of which {len(not_in_bom_recipename_in_oe)} not matched but recipe exists in OE data")

        if conf.recipe_report != '':
            try:
                with open(conf.recipe_report, "w") as repfile:
                    repfile.write(f"RECIPES IN BOM ({len(in_bom)}):\n")
                    repfile.write("\n".join(in_bom))
                    repfile.write(f"\n\nRECIPES IN BOM - NOT MATCHED IN OE DATA ({len(not_matched_oe_in_bom)}):\n")
                    repfile.write("\n".join(not_matched_oe_in_bom))
                    repfile.write(f"\n\nRECIPES NOT IN BOM ({len(not_in_bom)}):\n")
                    repfile.write("\n".join(not_in_bom))
                    repfile.write(f"\n\nRECIPES NOT IN BOM - NOT MATCHED IN OE DATA ({len(not_matched_oe_not_in_bom)}):\n")
                    repfile.write("\n".join(not_matched_oe_not_in_bom))
                    repfile.write(f"\n\nRECIPES NOT IN BOM - MATCHED IN OE DATA ({len(matched_oe_not_in_bom)}):\n")
                    repfile.write("\n".join(matched_oe_not_in_bom))
                    repfile.write(f"\n\nRECIPES NOT IN BOM - RECIPE EXISTS IN OE DATA BUT NO VERSION MATCH ({len(not_in_bom_recipename_in_oe)}):\n")
                    repfile.write("\n".join(not_in_bom_recipename_in_oe))
                logging.info(f"Output full recipe report to '{conf.recipe_report}'")
            except IOError as error:
                logging.error(f"Unable to write recipe report file {conf.recipe_report} - {error}")

    def mark_recipes_in_bom(self, bom: "BOM"):
        for recipe in self.recipes:
            if recipe.check_in_bom(bom):
                recipe.matched_in_bom = True
            else:
                recipe.matched_in_bom = False

    # def get_cpes(self):
    #     cpes = []
    #     for recipe in self.recipes:
    #         if not recipe.matched_in_bom:
    #             reccpe = recipe.cpe_string()
    #             print(f"CPE - missing recipe {recipe.name}/{recipe.version} - {reccpe}")
    #             cpes.append([recipe.name, reccpe])
    #     return cpes

    @staticmethod
    def get_rel(entry):
        try:
            if '_meta' in entry and 'links' in entry['_meta']:
                link_arr = entry['_meta']['links']
                for link in link_arr:
                    if link['rel'] == 'cpe-versions':
                        return link['href']
        except KeyError as e:
            logging.exception(f"Cannot get rel entry - {e}")
        return ''

    def process_missing_recipes(self, conf: "Config", bom: "BOM"):
        comps_added = False
        if not conf.add_comps_by_cpe and not conf.sbom_custom_components:
            return comps_added

        try:
            add_sbom = SBOM(conf.bd_project, conf.bd_version, sbom_version="2.0")
            for recipe in self.recipes:
                if recipe.matched_in_bom:
                    continue

                rec_cpe = recipe.cpe_string(conf)
                # print(f"CPE - missing recipe {recipe.name}/{recipe.version} - {rec_cpe}")

                url = f"{conf.bd_url}/api/cpes?q={rec_cpe}"
                cpe_arr = bom.get_data(url, "application/vnd.blackducksoftware.component-detail-5+json")
                logging.debug(f"Recipe {recipe.name}/{recipe.version} - found {len(cpe_arr)} CPE entries")
                for comp in cpe_arr:
                    val = self.get_rel(comp)
                    if val:
                        comp_arr = bom.get_data(val, "application/vnd.blackducksoftware.component-detail-5+json")
                        logging.debug(f"Found {len(comp_arr)} matching components from CPE")
                        for pkg in comp_arr:
                            if '_meta' in pkg and 'links' in pkg['_meta']:
                                orig_arr = pkg['_meta']['links']
                                orig_data = None
                                for orig in orig_arr:
                                    if orig['rel'] == 'origins':
                                        orig_data = bom.get_data(orig['href'], "application/vnd.blackducksoftware.component-detail-5+json")
                                        break
                                if orig_data:
                                    orig = orig_data[0]
                                    o_vername = orig['versionName']
                                    add_sbom.add_component(recipe.name, o_vername, orig['_meta']['href'])
                                    recipe.cpe_comp_href = orig['_meta']['href']
                                    comps_added = True
                                    recipe.matched_in_bom = True
                                    logging.info(f"Added component {recipe.name}/{recipe.version} to SBOM using CPE")
                                    break

                        if recipe.matched_in_bom:
                            break

                if conf.sbom_custom_components and not recipe.matched_in_bom:
                    # v1.1.2 - add component to sbom for custom component creation
                    add_sbom.add_recipe(recipe, clean_version=True)
                    logging.info(f"Added component {recipe.name}/{recipe.version} to SBOM as custom component")

                    comps_added = True

            if comps_added:
                if not add_sbom.output(conf.output_file):
                    logging.error("Unable to create SBOM file")
                if bom.upload_sbom(conf, bom, add_sbom, allow_create_custom_comps=True):
                    logging.info(f"Uploaded add-on SBOM file '{add_sbom.file}' to modify project "
                                 f"'{conf.bd_project}' version '{conf.bd_version}'")
                else:
                    return False
            return comps_added

        except Exception as e:
            logging.exception(f"Error processing missing recipes - {e}")
        return comps_added
