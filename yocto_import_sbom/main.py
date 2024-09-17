from .RecipeListClass import RecipeList
from .SBOMClass import SBOM
from .BOMClass import BOM
from .OEClass import OE
from .BBClass import BB
from .ConfigClass import Config
import logging
import sys


def main():
    conf = Config()

    logging.info("")
    logging.info("--- PHASE 1 - PROCESS PROJECT --------------------------------------------")
    reclist = RecipeList()
    bb = BB()
    if not bb.process(conf, reclist):
        sys.exit(2)

    logging.info("")
    logging.info("--- PHASE 2 - GET OE DATA ------------------------------------------------")
    if not conf.skip_oe_data:
        oe_class = OE(conf)
        reclist.check_recipes_in_oe(conf, oe_class)
        logging.info("Done processing OE data")
    else:
        logging.info("Skipping connection to OE APIs to verify origin layers and revisions "
                     "(remove --skip_oe_data to enable)")

    logging.info("")
    logging.info("--- PHASE 3 - WRITE SBOM -------------------------------------------------")
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
    logging.info("")
    logging.info("--- PHASE 4 - UPLOAD SBOM ------------------------------------------------")
    bom = BOM(conf)

    if bom.upload_sbom(conf, bom, sbom):
        logging.info(f"Uploaded SBOM file '{sbom.file}' to create project "
                     f"'{conf.bd_project}' version '{conf.bd_version}'")
    else:
        sys.exit(2)

    logging.info("")
    logging.info("--- PHASE 5 - CHECKING OE RECIPES IN BOM ---------------------------------")
    bom.get_proj()
    if not bom.wait_for_bom_completion():
        logging.error("Error waiting for project scan completion")
        sys.exit(2)
    bom.get_data()
    reclist.check_recipes_in_bom(conf, bom)

    logging.info("")
    logging.info("--- PHASE 6 - SIGNATURE SCAN PACKAGES ------------------------------------")
    if not conf.skip_sig_scan:
        if conf.package_dir and conf.download_dir:
            if not reclist.scan_pkg_download_files(conf, bom):
                logging.error(f"Unable to Signature scan package and download files")
                sys.exit(2)
            logging.info("Done")
        else:
            logging.info("Skipped (package_dir or download_dir not identified)")
    else:
        logging.info("Skipped (--skip_sig_scan specified)")

    logging.info("")
    logging.info("--- PHASE 7 - APPLY CVE PATCHES ------------------------------------------")
    if conf.cve_check_file:
        bom.get_proj()
        if not bom.wait_for_bom_completion():
            logging.error("Error waiting for project scan completion")
            sys.exit(2)

        bom.get_data()
        bom.process_cve_file(conf.cve_check_file, reclist)
        bom.process_patched_cves()
    else:
        logging.info("Skipping CVE processing as no cve_check output file supplied")

    logging.info("")
    logging.info("DONE")


if __name__ == '__main__':
    main()
