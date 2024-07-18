import os
import argparse
import sys
import logging

import global_values

parser = argparse.ArgumentParser(description='Create BD Yocto project from license.manifest', prog='bd-yocto-import-sbom')

# parser.add_argument("projfolder", nargs="?", help="Yocto project folder to analyse", default=".")

parser.add_argument("--blackduck_url", type=str, help="Black Duck server URL (REQUIRED "
                                                      "- can use BLACKDUCK_URL env var)", default="")
parser.add_argument("--blackduck_api_token", type=str, help="Black Duck API token (REQUIRED "
                                                            "- can use BLACKDUCK_API_TOKEN env var)", default="")
parser.add_argument("--blackduck_trust_cert", help="Black Duck trust server cert "
                                                   "(can use BLACKDUCK_TRUST_CERT env var)", action='store_true')
parser.add_argument("-p", "--project", help="Black Duck project to create (REQUIRED)", default="")
parser.add_argument("-v", "--version", help="Black Duck project version to create (REQUIRED)", default="")
parser.add_argument("-l", "--license_manifest", help="license.manifest file path "
                                                     "(REQUIRED - default 'license.manifest)",
                    default="license.manifest")
parser.add_argument("-b", "--bitbake_layers",
                    help="File containing output of 'bitbake-layers show-recipes' command (REQUIRED)", default="")
parser.add_argument("-c", "--cve_check_file",
                    help="CVE check output file", default="")
parser.add_argument("-o", "--output",
                    help="Specify output SBOM SPDX file for manual upload (if specified then BD project will not "
                         "be created automatically and CVE patching not supported)",
                    default="")
parser.add_argument("--get_oe_data",
                    help="Download and use OE data to check layers, versions & revisions", action='store_true')
parser.add_argument("--oe_data_folder",
                    help="Folder to contain OE data files - if files do not exist they will be downloaded, "
                         "if files exist then will be used without download", default="")

parser.add_argument("--debug", help="Debug logging mode", action='store_true')
parser.add_argument("--logfile", help="Logging output file", default="")

args = parser.parse_args()


def check_args():
    terminate = False
    # if platform.system() != "Linux":
    #     print('''Please use this program on a Linux platform or extract data from a Yocto build then
    #     use the --bblayers_out option to scan on other platforms\nExiting''')
    #     sys.exit(2)
    if args.debug:
        global_values.debug = True
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if args.logfile != '':
        if os.path.exists(args.logfile):
            logging.error(f"Specified logfile '{args.logfile}' already exists - EXITING")
            sys.exit(2)
        logging.basicConfig(encoding='utf-8',
                            handlers=[logging.FileHandler(args.logfile), logging.StreamHandler(sys.stdout)],
                            level=loglevel)
    else:
        logging.basicConfig(level=loglevel)

    logging.info("SUPPLIED ARGUMENTS:")
    for arg in vars(args):
        logging.info(f"--{arg}={getattr(args, arg)}")
    logging.info('')

    bd_connect = True
    if args.output != '':
        global_values.output_file = args.output
        bd_connect = False

    url = os.environ.get('BLACKDUCK_URL')
    if args.blackduck_url != '':
        global_values.bd_url = args.blackduck_url
    elif url is not None:
        global_values.bd_url = url
        logging.info(f"BLACKDUCK_URL value {url} found")
    elif bd_connect:
        logging.error("Black Duck URL not specified")
        terminate = True

    if args.project != "" and args.version != "":
        global_values.bd_project = args.project
        global_values.bd_version = args.version
    elif bd_connect:
        logging.error("Black Duck project/version not specified")
        terminate = True

    api = os.environ.get('BLACKDUCK_API_TOKEN')
    if args.blackduck_api_token != '':
        global_values.bd_api = args.blackduck_api_token
    elif api is not None:
        global_values.bd_api = api
        logging.info(f"BLACKDUCK_API_TOKEN value found")
    elif bd_connect:
        logging.error("Black Duck API Token not specified")
        terminate = True

    trustcert = os.environ.get('BLACKDUCK_TRUST_CERT')
    if trustcert == 'true':
        logging.info(f"BLACKDUCK_TRUST_CERT value found")
        global_values.bd_trustcert = True
    elif args.blackduck_trust_cert:
        global_values.bd_trustcert = True

    if not os.path.exists(args.license_manifest):
        logging.error(f"License.manifest '{args.license_manifest}' file does not exist")
        terminate = True
    else:
        global_values.license_manifest = args.license_manifest

    if not os.path.exists(args.bitbake_layers):
        logging.error(f"Bitbake layers command output file '{args.bitbake_layers}' file does not exist")
        terminate = True
    else:
        global_values.bitbake_layers = args.bitbake_layers

    if args.cve_check_file != '' and not os.path.exists(args.cve_check_file):
        logging.error(f"CVE Check file '{args.cve_check_file}' does not exist")
        terminate = True
    else:
        global_values.cve_check_file = args.cve_check_file

    if global_values.output_file == '' and (global_values.bd_url == '' or global_values.bd_api == ''):
        logging.error("Black Duck URL/API and output file not specified - nothing to do")
        terminate = True

    if args.get_oe_data:
        global_values.get_oe_data = True

    global_values.oe_data_folder = args.oe_data_folder

    if terminate:
        sys.exit(2)
    return
