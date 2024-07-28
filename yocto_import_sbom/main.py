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

    logging.info(f"Processing files '{conf.license_manifest}' and '{conf.bitbake_layers_file}' ...")

    reclist = RecipeList()
    bb = BB()
    if not bb.process(conf, reclist):
        sys.exit(2)

    if conf.get_oe_data:
        oe_class = OE(conf)
        reclist.check_recipes_in_oe(conf, oe_class)
        logging.info("Done processing OE data")
    else:
        logging.info("Skipping connection to OE APIs to verify origin layers and revisions")

    sbom = SBOM(conf.bd_project, conf.bd_version)
    sbom.process_recipes(reclist.recipes)
    sbom.output(conf.output_file)

    if conf.output_file:
        # Create SBOM and terminate
        logging.info(f"Specified SBOM output file {sbom.file} created - nothing more to do")
        logging.info("Done")
        sys.exit(0)

    bom = BOM(conf)

    if bom.upload_sbom(conf, bom, sbom):
        logging.info(f"Uploaded SBOM file '{sbom.file}' to create project "
                     f"{conf.bd_project}/{conf.bd_version}")
    else:
        sys.exit(2)

    if not conf.skip_sig_scan and conf.package_dir and conf.download_dir:
        if reclist.scan_pkg_download_files(conf, bom):
            logging.error(f"Unable to scan package and download files")
            sys.exit(2)

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

    logging.info("Done")


if __name__ == '__main__':
    main()
