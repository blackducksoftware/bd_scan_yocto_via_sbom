from .RecipeListClass import RecipeList
from .SBOMClass import SBOM
from .BOMClass import BOM
from .OEClass import OE
from .BBClass import BB
from .ConfigClass import Config
import logging
import sys

import tempfile
from bd_kernel_vulns import main as bdkv_main
# import os

empty_dir = tempfile.TemporaryDirectory()


def main():
    conf = Config()

    logging.info("")
    logging.info("--- PHASE 1 - PROCESS PROJECT --------------------------------------------")
    bom = BOM(conf)

    if bom.get_proj():
        logging.info(f"Project {conf.bd_project} Version {conf.bd_version} already exists")

    if conf.output_file == '':
        logging.info("Running Detect to initialise project")
        extra_opt = '--detect.tools=DETECTOR'
        if conf.unmap:
            extra_opt += ' --detect.project.codelocation.unmap=true'
        if not bom.run_detect_sigscan(conf, empty_dir.name,
                                      extra_opt=extra_opt):
            logging.error("Unable to run Detect to initialise project")
            sys.exit(2)

    reclist = RecipeList()
    bb = BB()
    if not bb.process(conf, reclist):
        sys.exit(2)

    logging.info("")
    logging.info("--- PHASE 2 - GET OE DATA ------------------------------------------------")
    if not conf.oe_data_folder:
        logging.info("Not using OE data cache folder (consider using --oe_data_folder) ...")
    if not conf.skip_oe_data:
        oe_class = OE(conf)
        reclist.check_recipes_in_oe(conf, oe_class)
        logging.info("Done processing OE data")
    else:
        logging.info("Skipping connection to OE APIs to verify origin layers and revisions "
                     "(remove --skip_oe_data to enable)")

    logging.info("")
    logging.info("--- PHASE 3 - GENERATE & UPLOAD SBOM -------------------------------------")
    sbom = SBOM(conf.bd_project, conf.bd_version)
    sbom.process_recipes(reclist.recipes)
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

    if bom.upload_sbom(conf, bom, sbom):
        logging.info(f"Uploaded SBOM file '{sbom.file}' to create project "
                     f"'{conf.bd_project}' version '{conf.bd_version}'")
    else:
        sys.exit(2)

    bom.get_proj()
    bom.process(reclist)

    logging.info("")
    logging.info("--- PHASE 4 - SIGNATURE SCAN PACKAGES ------------------------------------")
    if not conf.skip_sig_scan:
        if conf.package_dir and conf.download_dir:
            num, ret = reclist.scan_pkg_download_files(conf, bom)
            if num > 0:
                if ret:
                    logging.info("Done")
                else:
                    logging.error(f"Unable to run Signature scan on package and download files")
                    sys.exit(2)
            else:
                logging.info("No files to scan - skipping")
        else:
            logging.info("Skipped (package_dir or download_dir not identified)")
    else:
        logging.info("Skipped (--skip_sig_scan specified)")

    logging.info("")
    logging.info("--- PHASE 5 - CHECKING RECIPES -------------------------------------------")
    bom.get_proj()
    bom.process(reclist)
    if reclist.process_missing_recipes(conf, bom):
        bom.process(reclist)
    logging.info("")
    logging.info("--- PHASE 6 - BOM REPORT -------------------------------------------------")
    reclist.report_recipes_in_bom(conf, bom)

    logging.info("")
    logging.info("--- PHASE 7 - APPLY CVE PATCHES ------------------------------------------")
    if conf.cve_check_file:
        # bom.get_proj()

        if bom.process_cve_file(conf.cve_check_file, reclist):
            bom.process_patched_cves(conf)
    else:
        logging.info("Skipped CVE processing as no cve_check output file supplied")

    logging.info("")
    logging.info("--- PHASE 8 - PROCESS KERNEL VULNS ---------------------------------------")
    if conf.process_kernel_vulns and bom.check_kernel_in_bom():
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
                                           blackduck_trust_cert=conf.bd_trustcert)
    else:
        logging.info(f"Skipped as --process_kernel_vulns not specified")

    logging.info("")
    logging.info("bd_scan_yocto_via_sbom DONE")


if __name__ == '__main__':
    main()
