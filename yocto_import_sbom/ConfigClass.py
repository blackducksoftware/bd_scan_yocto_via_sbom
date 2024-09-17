import argparse
import logging
import os
import sys
from .OEClass import OE


class Config:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Create BD Yocto project from license.manifest via SBOM, '
                                                     'optionally process CVEs, signature scan package & download files',
                                         prog='bd-yocto-import-sbom')

        parser.add_argument("--blackduck_url", type=str, help="Black Duck server URL (REQUIRED "
                                                              "- can use BLACKDUCK_URL env var)", default="")
        parser.add_argument("--blackduck_api_token", type=str, help="Black Duck API token (REQUIRED "
                                                                    "- can use BLACKDUCK_API_TOKEN env var)",
                            default="")
        parser.add_argument("--blackduck_trust_cert", help="Black Duck trust server cert "
                                                           "(can use BLACKDUCK_TRUST_CERT env var)",
                            action='store_true')
        parser.add_argument("-p", "--project", help="Black Duck project to create (REQUIRED)", default="")
        parser.add_argument("-v", "--version", help="Black Duck project version to create (REQUIRED)", default="")
        parser.add_argument("--skip_bitbake", help="Do not run Bitbake command",
                            action='store_true')
        parser.add_argument("-t", "--target",
                            help="Yocto target (e.g. core-image-sato - REQUIRED if license.manifest not specified)",
                            default="")
        parser.add_argument("--machine",
                            help="OPTIONAL Yocto machine (usually determined from Bitbake env)",
                            default="")
        parser.add_argument("-l", "--license_manifest", help="OPTIONAL license.manifest file path "
                                                             "(usually determined from Bitbake env - default "
                                                             "'license.manifest')",
                            default="")
        parser.add_argument("--process_image_manifest",
                            help="Process image_license.manifest file",
                            action='store_true')
        parser.add_argument("-i", "--image_license_manifest", help="OPTIONAL image_license.manifest file path "
                                                             "(usually determined from Bitbake env - default "
                                                             "'image_license.manifest')",
                            default="")
        parser.add_argument("-b", "--bitbake_layers_file",
                            help="OPTIONAL File containing output of 'bitbake-layers show-recipes' command (usually "
                                 "determined from Bitbake command)",
                            default="")
        parser.add_argument("-c", "--cve_check_file",
                            help="OPTIONAL CVE check output file", default="")
        parser.add_argument("-o", "--output",
                            help="OPTIONAL Specify output SBOM SPDX file for manual upload (if specified then BD "
                                 "project will not be created automatically and CVE patching not supported)",
                            default="")
        parser.add_argument("--skip_oe_data",
                            help="OPTIONAL Download and use OE data to check layers, versions & revisions",
                            action='store_true')
        parser.add_argument("--oe_data_folder",
                            help="Folder to contain OE data files - if files do not exist they will be downloaded, "
                                 "if files exist then will be used without download", default="")
        parser.add_argument("--max_oe_version_distance",
                            help="Where no exact match, use closest previous recipe version up to specified distance."
                                 "Distance should be specified as MAJOR.MINOR.PATCH (e.g. 0.1.0)", default='0.0.0')

        parser.add_argument("--build_dir", type=str, help="OPTIONAL Alternative build folder (usually "
                                                          "determined from Bitbake env)", default="")
        parser.add_argument("--download_dir",
                            help="OPTIONAL Download directory where original OSS source is downloaded (usually "
                                 "determined from Bitbake env)",
                            default="")
        parser.add_argument("--package_dir",
                            help="OPTIONAL Download directory where package files are downloaded (usually "
                                 "determined from Bitbake env)",
                            default="")
        parser.add_argument("--image_package_type",
                            help="Package type used for installing packages (e.g. rpm, deb or ipx)",
                            default="rpm")

        parser.add_argument("--skip_sig_scan", help="Do not Signature scan downloads and packages",
                            action='store_true')
        parser.add_argument("--scan_all_packages", help="Signature scan all packages (only recipes not matched"
                                                     "from OE data are scanned by default)",
                            action='store_true')
        parser.add_argument("--detect_jar_path", help="OPTIONAL Synopsys Detect jar path", default="")
        parser.add_argument("--detect_opts", help="OPTIONAL Additional Synopsys Detect options", default="")
        parser.add_argument("--api_timeout", help="OPTIONAL API and Detect timeout in seconds (default 60)",
                            default="60")
        parser.add_argument("--sbom_create_custom_components",
                            help="Create custom components for unmatched components on SBOM upload",
                            action='store_true')

        parser.add_argument("--debug", help="Debug logging mode", action='store_true')
        parser.add_argument("--logfile", help="Logging output file", default="")
        parser.add_argument("--recipe_report", help="Output recipe report to file", default="")


        args = parser.parse_args()

        self.debug = False
        loglevel = logging.INFO

        self.output_file = ''
        self.bd_url = ''
        self.bd_project = ''
        self.bd_version = ''
        self.bd_api = ''
        self.bd_trustcert = False
        self.skip_bitbake = args.skip_bitbake
        self.license_manifest = ''
        self.image_license_manifest = ''
        self.process_image_manifest = False
        self.target = ''
        self.machine = args.machine
        self.bitbake_layers_file = ''
        self.cve_check_file = ''
        self.skip_oe_data = False
        self.max_oe_version_distance = ''
        self.oe_data_folder = args.oe_data_folder
        self.package_dir = ''
        self.download_dir = ''
        self.deploy_dir = ''
        self.build_dir = ''
        self.image_package_type = args.image_package_type
        self.skip_sig_scan = False
        self.scan_all_packages = False
        self.detect_jar = ''
        self.detect_opts = args.detect_opts
        self.api_timeout = args.api_timeout
        self.sbom_custom_components = args.sbom_create_custom_components
        self.cve_check_dir = ''
        self.license_dir = ''
        self.recipe_report = ''

        terminate = False
        if args.debug:
            self.debug = True
            loglevel = logging.DEBUG

        if args.logfile:
            if os.path.exists(args.logfile):
                logging.error(f"Specified logfile '{args.logfile}' already exists - EXITING")
                return
            logging.basicConfig(encoding='utf-8',
                                handlers=[logging.FileHandler(args.logfile), logging.StreamHandler(sys.stdout)],
                                level=loglevel)
        else:
            logging.basicConfig(level=loglevel)

        logging.info("Black Duck Yocto scan via SBOM utility - v1.0.12")
        logging.info("SUPPLIED ARGUMENTS:")
        for arg in vars(args):
            logging.info(f"--{arg}={getattr(args, arg)}")

        logging.info('')
        logging.info("--- PHASE 0 - CONFIG -----------------------------------------------------")

        bd_connect = True
        if args.output:
            self.output_file = args.output
            bd_connect = False

        url = os.environ.get('BLACKDUCK_URL')
        if args.blackduck_url:
            self.bd_url = args.blackduck_url
        elif url is not None:
            self.bd_url = url
            logging.info(f"BLACKDUCK_URL value {url} found from environment")
        elif bd_connect:
            logging.error("Black Duck URL not specified")
            terminate = True
        if self.bd_url and self.bd_url[-1] == '/':
            self.bd_url = self.bd_url[:-1]

        if args.project and args.version:
            self.bd_project = args.project
            self.bd_version = args.version
        elif bd_connect:
            logging.error("Black Duck project/version not specified")
            terminate = True

        api = os.environ.get('BLACKDUCK_API_TOKEN')
        if args.blackduck_api_token:
            self.bd_api = args.blackduck_api_token
        elif api is not None:
            self.bd_api = api
            logging.info(f"BLACKDUCK_API_TOKEN value found from environment")
        elif bd_connect:
            logging.error("Black Duck API Token not specified")
            terminate = True

        trustcert = os.environ.get('BLACKDUCK_TRUST_CERT')
        if trustcert == 'true':
            logging.info(f"BLACKDUCK_TRUST_CERT value found")
            self.bd_trustcert = True
        elif args.blackduck_trust_cert:
            self.bd_trustcert = True

        if args.license_manifest:
            if not os.path.exists(args.license_manifest):
                logging.error(f"License.manifest '{args.license_manifest}' file does not exist")
                terminate = True
            else:
                self.license_manifest = args.license_manifest

        if args.process_image_manifest:
            self.process_image_manifest = True

        if args.image_license_manifest:
            if not os.path.exists(args.image_license_manifest):
                logging.error(f"License.manifest '{args.image_license_manifest}' file does not exist")
                terminate = True
            else:
                self.image_license_manifest = args.image_license_manifest
                self.process_image_manifest = True

        if args.target:
            self.target = args.target
        elif not self.license_manifest:
            logging.error(f"Target --target required if --license_manifest not specified")
            terminate = True

        if args.bitbake_layers_file:
            if not os.path.exists(args.bitbake_layers_file):
                logging.error(f"Bitbake layers command output file '{args.bitbake_layers_file}' file does not exist")
                terminate = True
            else:
                self.bitbake_layers_file = args.bitbake_layers_file

        if args.cve_check_file and not os.path.exists(args.cve_check_file):
            logging.error(f"CVE Check file '{args.cve_check_file}' does not exist")
            terminate = True
        else:
            self.cve_check_file = args.cve_check_file

        if not self.output_file and (not self.bd_url or not self.bd_api):
            logging.error("Black Duck URL/API and output file not specified - nothing to do")
            terminate = True

        if args.skip_oe_data:
            self.skip_oe_data = True

        distarr = OE.calc_specified_version_distance(args.max_oe_version_distance)
        if distarr[0] == -1:
            logging.error(
                f"Invalid max_oe_version_distance '{args.max_oe_version_distance}' specified - "
                f"should be MAJOR.MINOR.PATCH with numeric values")
            terminate = True
        self.max_oe_version_distance = distarr

        if not os.path.isdir(self.oe_data_folder):
            logging.error(f"OE_data_folder {self.oe_data_folder} does not exist")
            terminate = True

        if args.package_dir:
            if not os.path.exists(args.package_dir):
                logging.error(f"Specified package dir '{args.package_dir}' does not exist")
                terminate = True
            else:
                self.package_dir = args.package_dir

        if args.download_dir:
            if not os.path.exists(args.download_dir):
                logging.error(f"Specified package dir '{args.download_dir}' does not exist")
                terminate = True
            else:
                self.download_dir = args.download_dir

        if args.skip_sig_scan:
            self.skip_sig_scan = True
        elif args.scan_all_packages:
            self.scan_all_packages = True

        if args.detect_jar_path and not os.path.isfile(args.detect_jar_path):
            logging.error(f"Detect jar file {args.detect_jar_path} does not exist")
            terminate = True
        else:
            self.detect_jar = args.detect_jar_path

        if self.skip_bitbake:
            if not self.bitbake_layers_file:
                logging.error("Option --skip_bitbake set but --bitbake_layers_file not supplied")
                terminate = True

        if args.recipe_report != '':
            if os.path.exists(args.recipe_report):
                logging.error(f"Output recipe report file {args.recipe_report} already exists - terminating")
                terminate = True
            else:
                self.recipe_report = args.recipe_report

        if terminate:
            sys.exit(2)
        return
