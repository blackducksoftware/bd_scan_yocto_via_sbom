import argparse
import logging
import os
import sys
from .OEClass import OE

script_version = "v1.2.5"


class Config:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Create BD Yocto project from license.manifest via SBOM, '
                                                     'optionally process CVEs, signature scan package & download files',
                                         prog='bd-yocto-import-sbom')

        parser.add_argument("--blackduck_url", type=str,
                            help="Black Duck server URL (REQUIRED - can use $BLACKDUCK_URL env var)",
                            default="")
        parser.add_argument("--blackduck_api_token", type=str,
                            help="Black Duck API token (REQUIRED - can use $BLACKDUCK_API_TOKEN env var)",
                            default="")
        parser.add_argument("--blackduck_trust_cert",
                            help="Black Duck trust server cert (can use $BLACKDUCK_TRUST_CERT env var)",
                            action='store_true')
        parser.add_argument("-p", "--project", type=str,
                            help="Black Duck project to create (REQUIRED)",
                            default="")
        parser.add_argument("-v", "--version", type=str,
                            help="Black Duck project version to create (REQUIRED)",
                            default="")

        parser.add_argument("--modes", type=str,
                            help="Specify scan modes to include - comma-separated list from 'ALL,DEFAULT,"
                                 "OE_RECIPES,IMAGE_MANIFEST,SIG_SCAN,SIG_SCAN_ALL,CVE_PATCHES,CPE_COMPS,CUSTOM_COMPS,"
                                 "KERNEL_VULNS'. (DEFAULT = OE_RECIPES,SIG_SCAN,CVE_PATCHES)",
                            default="")

        parser.add_argument("-t", "--target", type=str,
                            help="Yocto target (e.g. core-image-sato - REQUIRED if license.manifest not specified or "
                                 "--task_depends_dot_file specified)",
                            default="")
        parser.add_argument("--machine", type=str,
                            help="OPTIONAL Yocto machine (usually determined from Bitbake env)",
                            default="")
        parser.add_argument("-l", "--license_manifest", type=str,
                            help="OPTIONAL license.manifest file path (usually determined from Bitbake env - default "
                                 "'license.manifest')",
                            default="")
        parser.add_argument("--process_image_manifest",
                            help="LEGACY PARAMETER - Process image_license.manifest file - replace with "
                                 "'--modes IMAGE_MANIFEST'",
                            action='store_true')
        parser.add_argument("-i", "--image_license_manifest", type=str,
                            help="OPTIONAL image_license.manifest file path "
                                 "(usually determined from Bitbake env - default 'image_license.manifest')",
                            default="")
        parser.add_argument("-b", "--bitbake_layers_file", type=str,
                            help="OPTIONAL File containing output of 'bitbake-layers show-recipes' command (usually "
                                 "determined from Bitbake command)",
                            default="")
        parser.add_argument("--task_depends_dot_file", type=str,
                            help="OPTIONAL Specify the path to the task-depends.dot file created by 'bitbake -g' "
                                 "command (if 'license.manifest' is not also specified, will process ALL recipes "
                                 "including dev dependencies, --target is also required)",
                            default="")
        parser.add_argument("-c", "--cve_check_file", type=str,
                            help="OPTIONAL CVE check output file to mark locally patched CVEs as patched in project",
                            default="")
        parser.add_argument("--build_dir", type=str,
                            help="OPTIONAL Alternative build folder (usually determined from Bitbake env)",
                            default="")
        parser.add_argument("--download_dir", type=str,
                            help="OPTIONAL Download directory where original OSS source is downloaded (usually "
                                 "determined from Bitbake env)",
                            default="")
        parser.add_argument("--package_dir", type=str,
                            help="OPTIONAL Download directory where package files are downloaded (usually "
                                 "determined from Bitbake env)",
                            default="")
        parser.add_argument("--image_package_type", type=str,
                            help="Package type used for installing packages (e.g. rpm, deb or ipx)",
                            default="rpm")

        parser.add_argument("--skip_bitbake",
                            help="Do not run 'bitbake -e' or 'bitbake-layers show-recipes' commands to extract data",
                            action='store_true')
        parser.add_argument("-o", "--output", type=str,
                            help="OPTIONAL Specify output SBOM SPDX file for manual upload (if specified then BD "
                                 "project will not be created automatically and CVE patching not supported)",
                            default="")
        parser.add_argument("--skip_oe_data",
                            help="OPTIONAL Download and use OE data to check layers, versions & revisions",
                            action='store_true')
        parser.add_argument("--oe_data_folder", type=str,
                            help="Folder to contain OE data files - if files do not exist they will be downloaded, "
                                 "if files exist then will be used without download",
                            default="")
        parser.add_argument("--max_oe_version_distance", type=str,
                            help="Where no exact match, use closest previous recipe version up to specified distance."
                                 "Distance should be specified as MAJOR.MINOR.PATCH (e.g. 0.1.0)",
                            default='0.0.0')

        parser.add_argument("--add_comps_by_cpe",
                            help="LEGACY PARAMETER - Use CPE to add recipes not matched by OE lookup or signature "
                                 "scan - replace with '--modes CPE_COMPS'",
                            action='store_true')
        parser.add_argument("--process_kernel_vulns",
                            help="LEGACY PARAMETER - Process kernel modules to ignore vulns not in compiled kernel "
                                 "modules (assumes --process_image_manifest) - replace with '--modes KERNEL_VULNS'",
                            action='store_true')
        parser.add_argument("--kernel_recipe", type=str,
                            help="Alternate kernel recipe name - used in CPE matching --add_comps_by_cpe "
                                 "(default 'linux-yocto')",
                            default="linux-yocto")
        parser.add_argument("--sbom_create_custom_components",
                            help="LEGACY PARAMETER - Create custom components for unmatched components on SBOM upload "
                                 "- replace with '--modes CUSTOM_COMPS'",
                            action='store_true')
        parser.add_argument("--skip_sig_scan",
                            help="Do not Signature scan downloads and packages",
                            action='store_true')
        parser.add_argument("--scan_all_packages",
                            help="LEGACY PARAMETER - Signature scan all packages (only recipes not matched from OE "
                                 "data are scanned by default) - replace with '--modes SIG_SCAN_ALL'",
                            action='store_true')
        parser.add_argument("--detect_jar_path", type=str,
                            help="OPTIONAL BD Detect jar path",
                            default="")
        parser.add_argument("--detect_opts", type=str,
                            help="OPTIONAL Additional BD Detect options (remove leading '--')",
                            default="")
        parser.add_argument("--api_timeout", type=int,
                            help="OPTIONAL API and Detect timeout in seconds (default 600)",
                            default="600")

        parser.add_argument("--debug",
                            help="Debug logging mode",
                            action='store_true')
        parser.add_argument("--logfile", type=str,
                            help="Logging output file",
                            default="")
        parser.add_argument("--recipe_report", type=str,
                            help="Output recipe report to file",
                            default="")
        parser.add_argument("--no_unmap",
                            help="Do not unmap previous scans when running new scan",
                            action='store_true')

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
        self.target = args.target
        self.machine = args.machine
        self.task_depends_dot_file = ''
        self.bitbake_layers_file = ''
        self.cve_check_file = ''
        self.skip_oe_data = args.skip_oe_data
        self.max_oe_version_distance = ''
        self.oe_data_folder = args.oe_data_folder
        self.package_dir = ''
        self.download_dir = ''
        self.deploy_dir = ''
        self.build_dir = ''
        self.log_dir = ''
        self.image_package_type = args.image_package_type
        self.run_sig_scan = True
        self.scan_all_packages = False
        self.detect_jar = ''
        self.detect_opts = ''
        self.api_timeout = args.api_timeout
        self.run_custom_components = False
        self.cve_check_dir = ''
        self.license_dir = ''
        self.recipe_report = ''
        self.unmap = not args.no_unmap
        self.run_cpe_components = False
        self.process_kernel_vulns = False
        self.kernel_recipe = args.kernel_recipe
        self.kernel_files = []
        self.process_oe_recipes = True
        self.process_cves = True

        terminate = False
        if args.debug:
            self.debug = True
            loglevel = logging.DEBUG

        if args.logfile:
            if os.path.exists(args.logfile):
                logging.error(f"Specified logfile '{args.logfile}' already exists - EXITING")
                sys.exit(2)
            logging.basicConfig(encoding='utf-8',
                                handlers=[logging.FileHandler(args.logfile), logging.StreamHandler(sys.stdout)],
                                level=loglevel)
        else:
            logging.basicConfig(level=loglevel)

        logging.info("**************************************************************************")
        logging.info(f"Black Duck Yocto scan via SBOM utility - {script_version}")
        logging.info("**************************************************************************")
        logging.info('')
        logging.info("--- PHASE 0 - CONFIG -----------------------------------------------------")

        logging.info("SUPPLIED ARGUMENTS:")
        for arg in vars(args):
            logging.info(f"    --{arg}={getattr(args, arg)}")

        # Check modes
        # ALL,DEFAULT,OE_RECIPES,IMAGE_MANIFEST,SIG_SCAN,SIG_SCAN_ALL,CVE_PATCHES,CPE_COMPS,CUSTOM_COMPS,KERNEL_VULNS

        # modes = ("ALL","DEFAULT","OE_RECIPES","IMAGE_MANIFEST","SIG_SCAN","SIG_SCAN_ALL","CVE_PATCHES","CPE_COMPS",
        # "CUSTOM_COMPS","KERNEL_VULNS")
        mode_dict = {
            "OE_RECIPES": "process_oe_recipes",
            "IMAGE_MANIFEST": "process_image_manifest",
            "SIG_SCAN": "run_sig_scan",
            "SIG_SCAN_ALL": "scan_all_packages",
            "CVE_PATCHES": "process_cves",
            "CPE_COMPS": "run_cpe_components",
            "CUSTOM_COMPS": "run_custom_components",
            "KERNEL_VULNS": "process_kernel_vulns"
        }

        if args.modes != '':
            modes_to_set = []
            for mode in args.modes.split(','):
                if mode == 'ALL':
                    # logging.debug(f" - Setting ALL scan modes")
                    for key in mode_dict.keys():
                        if key != 'SIG_SCAN_ALL':
                            modes_to_set.append(key)
                            # setattr(self, mode_dict[val], True)
                elif mode == 'DEFAULT':
                    # logging.debug(f" - Setting DEFAULT scan modes")
                    for key in ["OE_RECIPES", "SIG_SCAN", "CVE_PATCHES"]:
                        modes_to_set.append(key)
                        # setattr(self, mode_dict[key], True)
                elif mode in mode_dict.keys():
                    modes_to_set.append(mode)
                else:
                    logging.error(f"Invalid --modes option {mode} specified - ignored")

            for mode in mode_dict.keys():
                if mode in modes_to_set:
                    setattr(self, mode_dict[mode], True)
                else:
                    setattr(self, mode_dict[mode], False)

        if args.process_image_manifest:
            self.process_image_manifest = args.process_image_manifest
            logging.debug("Will process image manifest (--process_image_manifest specified)")
        if args.sbom_create_custom_components:
            logging.debug("Will create custom components (--sbom_create_custom_components specified)")
            self.run_custom_components = args.sbom_create_custom_components
        if args.add_comps_by_cpe:
            logging.debug("Will create components by CPE --add_comps_by_cpe specified)")
            self.run_cpe_components = args.add_comps_by_cpe
        if args.process_kernel_vulns:
            logging.debug("Will process kernel vulns --process_kernel_vulns specified)")
            self.process_kernel_vulns = args.process_kernel_vulns

        logging.info("")
        logging.info("Scan modes:")
        for mode in mode_dict.keys():
            logging.info(f" - {mode}: {getattr(self,mode_dict[mode])}")
        logging.info("")

        bd_connect = True
        if args.output:
            if os.path.exists(args.output):
                logging.error(f"Specified SBOM output file '{args.output}' already exists - EXITING")
                sys.exit(2)
            self.output_file = args.output
            bd_connect = False

        url = os.environ.get('BLACKDUCK_URL')
        if args.blackduck_url:
            self.bd_url = args.blackduck_url
        elif url is not None:
            self.bd_url = url
            logging.info(f"BLACKDUCK_URL value {url} read from environment")
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
            logging.info(f"BLACKDUCK_API_TOKEN value read from environment")
        elif bd_connect:
            logging.error("Black Duck API Token not specified")
            terminate = True

        trustcert = os.environ.get('BLACKDUCK_TRUST_CERT')
        if trustcert == 'true':
            logging.info(f"BLACKDUCK_TRUST_CERT value read from environment")
            self.bd_trustcert = True
        elif args.blackduck_trust_cert:
            self.bd_trustcert = True

        if args.license_manifest:
            if not os.path.exists(args.license_manifest):
                logging.error(f"License.manifest '{args.license_manifest}' file does not exist")
                terminate = True
            else:
                self.license_manifest = args.license_manifest

        if args.image_license_manifest:
            if not os.path.exists(args.image_license_manifest):
                logging.error(f"License.manifest '{args.image_license_manifest}' file does not exist")
                terminate = True
            else:
                self.image_license_manifest = args.image_license_manifest
                self.process_image_manifest = True

        if args.task_depends_dot_file:
            if not os.path.exists(args.task_depends_dot_file):
                logging.error(f"Specified task-depends.dot file '{args.task_depends_dot_file}' does not exist")
                terminate = True
            else:
                if not self.target:
                    logging.error(f"Target --target required if --task_depends_dot_file specified")
                    terminate = True
                else:
                    self.task_depends_dot_file = args.task_depends_dot_file

        if args.bitbake_layers_file:
            if not os.path.exists(args.bitbake_layers_file):
                logging.error(f"Bitbake layers command output file '{args.bitbake_layers_file}' does not exist")
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

        distarr = OE.calc_specified_version_distance(args.max_oe_version_distance)
        if distarr[0] == -1:
            logging.error(
                f"Invalid max_oe_version_distance '{args.max_oe_version_distance}' specified - "
                f"should be MAJOR.MINOR.PATCH with numeric values")
            terminate = True
        self.max_oe_version_distance = distarr

        if self.oe_data_folder and not os.path.isdir(self.oe_data_folder):
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
            self.run_sig_scan = False
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

        # if not self.license_manifest and not self.task_depends_dot_file:
        #     logging.error(f"License manifest and/or task-depends.dot file must be specified - terminating")
        #     terminate = True

        if self.process_kernel_vulns and not self.process_image_manifest:
            logging.warning(f"Mode KERNEL_VULNS requires IMAGE_MANIFEST - setting IMAGE_MANIFEST")
            self.process_image_manifest = True

        if self.scan_all_packages and not self.run_sig_scan:
            self.run_sig_scan = True

        if args.detect_opts != '':
            self.detect_opts = args.detect_opts.replace('detect', '--detect')

        if terminate:
            sys.exit(2)
        return
