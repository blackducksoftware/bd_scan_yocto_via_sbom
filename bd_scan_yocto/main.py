from .RecipeListClass import RecipeList
from .SBOMClass import SBOM
from .BOMClass import BOM
from .OEClass import OE
from .BBClass import BB
from .ConfigClass import Config
from .vendored_deps import (
    parse_src_uri,
    validate_recipe_name,
    warn_missing_recipe_names,
)
import dataclasses
import json
import logging
import sys

import tempfile
from bd_kernel_vulns import main as bdkv_main
# import os

empty_dir = tempfile.TemporaryDirectory()


def main():
    conf = Config()
    bb = BB()
    if not conf.skip_bitbake:
        logging.info("Checking Bitbake environment ...")
        if not bb.check_bitbake():
            logging.error("Terminating")
            sys.exit(2)

    logging.info("")
    logging.info("--- PHASE 0 - INITIATE PROJECT -------------------------------------------")
    logging.info("")

    bom = BOM(conf)

    if bom.get_proj():
        logging.info(f"Project {conf.bd_project} Version {conf.bd_version} already exists")
        if conf.unmap and conf.output_file == '':
            logging.info("Unmapping existing code locations from project version (--unmap specified) ...")
            bom.unmap_codelocations()
    elif conf.output_file == '':
        logging.info("Running Detect to initialise project")
        extra_opt = '--detect.tools=DETECTOR'
        if conf.unmap:
            extra_opt += ' --detect.project.codelocation.unmap=true'
        if not bom.run_detect_sigscan(conf, empty_dir.name,
                                      extra_opt=extra_opt):
            logging.error("Unable to run Detect to initialise project")
            sys.exit(2)

    reclist = RecipeList()

    if not bb.process(conf, reclist):
        sys.exit(2)

    logging.info("")
    logging.info("--- PHASE 1 - GET OE DATA ------------------------------------------------")
    logging.info("")
    if conf.process_oe_recipes:
        if not conf.oe_data_folder:
            logging.info("Not using OE data cache folder (consider using --oe_data_folder) ...")

        if not conf.skip_oe_data:
            oe_class = OE(conf)
            logging.info("")
            logging.info("--- PHASE 2 - MATCH RECIPES AGAINST OE DATA ------------------------------")
            logging.info("")
            logging.info("Checking recipes ...")

            reclist.check_recipes_in_oe(conf, oe_class)
        else:
            logging.info("Skipping connection to OE APIs to verify origin layers and revisions "
                         "(remove --skip_oe_data to enable)")
            logging.info("- PHASE 2 Skipped - --skip_oe_data specified")

    else:
        logging.info("- PHASE 2 Skipped - mode OE_RECIPES not specified")

    logging.info("")
    logging.info("--- PHASE 3 - GENERATE & UPLOAD SBOM -------------------------------------")
    logging.info("")
    if conf.process_oe_recipes:
        sbom = SBOM(conf.bd_project, conf.bd_version)
        sbom.process_recipes(reclist.recipes)

        if conf.process_vendored_deps:
            logging.info("Processing vendored Rust/Go dependencies ...")
            try:
                # Determine which recipes to scan
                recipe_names_in_manifest = {r.name for r in reclist.recipes}
                if conf.vendored_deps_recipes:
                    # Validate each user-supplied name before it reaches any subprocess
                    filter_names = []
                    for rname in conf.vendored_deps_recipes:
                        if validate_recipe_name(rname):
                            filter_names.append(rname)
                        else:
                            logging.warning(
                                f"Ignoring invalid recipe name {rname!r} from "
                                f"--vendored_deps_recipes"
                            )
                    warn_missing_recipe_names(filter_names, recipe_names_in_manifest)
                    recipes_to_scan = [
                        r for r in reclist.recipes if r.name in filter_names
                    ]
                else:
                    recipes_to_scan = list(reclist.recipes)

                # Build a run-level dedup set for unknown-scheme warnings
                seen_unknown: set = set()
                all_deps = []

                for recipe in recipes_to_scan:
                    if not (recipe.spdxid and
                            recipe.spdxid.startswith('SPDXRef-package-')):
                        continue
                    inc_files = BB.get_recipe_inc_files(
                        recipe.name, conf.bblayers
                    )
                    for inc_path in inc_files:
                        try:
                            with open(inc_path, encoding='utf-8', errors='strict') as fh:
                                text = fh.read()
                        except (OSError, UnicodeDecodeError) as exc:
                            logging.warning(
                                f"Cannot read inc file '{inc_path}': {exc}"
                            )
                            continue
                        deps = parse_src_uri(
                            text, recipe.name,
                            seen_unknown_schemes=seen_unknown,
                        )
                        for dep in deps:
                            sbom.add_vendored_dep(dep, recipe.spdxid)
                            all_deps.append(dep)

                # Deduplicate by (name, version) for accurate summary count;
                # SBOM already deduplicates via _dep_spdxid_cache but all_deps
                # retains one entry per recipe occurrence.
                unique_deps = list({(d.name, d.version): d for d in all_deps}.values())
                logging.info(
                    f"- {len(unique_deps)} vendored dependencies added to SBOM"
                )

                if conf.vendored_deps_output and unique_deps:
                    try:
                        with open(conf.vendored_deps_output, 'w', encoding='utf-8') as vf:
                            json.dump(
                                [dataclasses.asdict(d) for d in unique_deps],
                                vf, indent=2,
                            )
                        logging.info(
                            f"Vendored dependencies written to "
                            f"'{conf.vendored_deps_output}'"
                        )
                    except OSError as exc:
                        logging.warning(
                            f"Could not write vendored_deps_output "
                            f"'{conf.vendored_deps_output}': {exc}"
                        )

            except Exception as exc:
                logging.warning(
                    f"VENDORED_DEPS processing failed - continuing without "
                    f"vendored dependencies: {exc}"
                )

        if not sbom.output(conf.output_file):
            logging.error("Unable to create SBOM file")
            sys.exit(2)

        if conf.output_file:
            # Create SBOM and terminate
            logging.info(f"Specified SBOM output file {sbom.file} created - nothing more to do")
            logging.info("")
            logging.info("Done")
            sys.exit(0)

        logging.info("Done creating SBOM file")
        # bom = BOM(conf)

        if bom.upload_sbom(conf, sbom):
            logging.info(f"Uploaded SBOM file '{sbom.file}' to create project "
                         f"'{conf.bd_project}' version '{conf.bd_version}'")
        else:
            sys.exit(2)

    else:
        logging.info("Skipped - mode OE_RECIPES not specified")
    bom.get_proj()
    bom.process(reclist, sbom.file if conf.process_oe_recipes else None)
    logging.info(f"- {reclist.unmatched} Recipes not matched so far")

    logging.info("")
    logging.info("--- PHASE 4 - SIGNATURE SCAN PACKAGES ------------------------------------")
    logging.info("")
    if conf.run_sig_scan:
        if conf.package_dir and conf.download_dir:
            num, ret = reclist.scan_pkg_download_files(conf, bom)
            if num > 0:
                if ret:
                    logging.info("Done")
                    bom.get_proj()
                    bom.process(reclist)
                    logging.info(f"- {reclist.unmatched} Recipes not matched so far")

                else:
                    logging.error("Unable to run Signature scan on package and download files")
                    sys.exit(2)
            else:
                logging.info("No files to scan - skipping")
        else:
            logging.info("Skipped (package_dir or download_dir not identified)")
    else:
        logging.info("Skipped - mode SIG_SCAN not specified")

    logging.info("")
    logging.info("--- PHASE 5 - ADDING RECIPES BY CPE OR CUSTOM COMPONENT ------------------")
    logging.info("")
    if conf.run_cpe_components or conf.run_custom_components:
        try:
            addon_sbom_file = reclist.process_missing_recipes(conf, bom)
            if addon_sbom_file:
                bom.process(reclist, addon_sbom_file)
                logging.info(f"- {reclist.unmatched} Recipes not matched so far")
            else:
                logging.info("Skipped - no unmatched recipes")
        except RuntimeError as e:
            logging.error(f"PHASE 5 failed: {e}")
            logging.error("This may be caused by invalid SPDX license definitions in recipe entries.")
            logging.error("Consider re-running with --ignore_licenses to skip license text in custom "
                          "components, or --filter_recipes_by_licenses to exclude recipes with "
                          "problematic licenses.")
            sys.exit(2)
    else:
        logging.info("Skipped - mode CPE_COMPS or CUSTOM_COMPS not specified")

    logging.info("")
    logging.info("--- PHASE 6 - BOM REPORT -------------------------------------------------")
    logging.info("")
    not_in_bom, not_in_bom_no_oe_version_match = reclist.report_recipes_in_bom(conf)

    if conf.fail_on_unmatched_recipes == 'ANY':
        fail_recipes = not_in_bom
    elif conf.fail_on_unmatched_recipes == 'OE_RECIPES':
        fail_recipes = not_in_bom_no_oe_version_match
    else:
        fail_recipes = []

    if fail_recipes:
        logging.error("")
        logging.error(f"{len(fail_recipes)} recipe(s) not matched in BOM "
                      f"(--fail_on_unmatched_recipes={conf.fail_on_unmatched_recipes} specified):")
        for desc in fail_recipes:
            logging.error(f"- {desc}")
        sys.exit(-1)

    logging.info("")
    logging.info("--- PHASE 7 - APPLY CVE PATCHES FROM CVE_CHECK ---------------------------")
    logging.info("")
    if conf.process_cves and conf.cve_check_file:
        # bom.get_proj()
        if bom.process_cve_file(conf.cve_check_file, reclist):
            bom.process_patched_cves(conf)

        logging.info("")
        logging.info("Updating custom component CPEs from cve_check file ...")
        bom.update_custom_component_cpes(conf, reclist)
    else:
        logging.info("Skipped - mode CVE_PATCHES not specified or no cve_check output file identified")

    logging.info("")
    logging.info("--- PHASE 8 - PROCESS KERNEL VULNS ---------------------------------------")
    logging.info("")
    if conf.process_kernel_vulns and conf.skip_bitbake:
        logging.info("Skipped - --skip_bitbake specified (kernel modules require 'bitbake -e virtual/kernel')")
    elif conf.process_kernel_vulns:
        if bom.check_kernel_in_bom():
            logging.info("Ignoring Kernel vulnerabilities for modules not included in kernel build ...")
            kfilelist = bb.process_kernel_files(conf)
            if len(kfilelist) == 0:
                logging.error("Unable to extract kernel source modules from kernel image - skipping")
            else:
                kfile = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix='.lst')
                kfile.write('\n'.join(kfilelist))
                kfile.close()

                bdkv_main.process_kernel_vulns(blackduck_url=conf.bd_url, blackduck_api_token=conf.bd_api,
                                               kernel_source_file=kfile.name, project=conf.bd_project,
                                               version=conf.bd_version, logger=logging,
                                               blackduck_trust_cert=conf.bd_trustcert,
                                               remediation_status=conf.kernel_vulns_remediation_status,
                                               remediation_justification=conf.kernel_vulns_remediation_justification)
                logging.info("NOTE: Kernel vuln remediations are queued in the BD server - updates may take some time to be applied in the BOM.")
        else:
            logging.info("Kernel component not found in project - skipping")
    else:
        logging.info("Skipped - mode KERNEL_VULNS not specified")

    logging.info("")
    logging.info("bd_scan_yocto_via_sbom DONE")


if __name__ == '__main__':
    main()
