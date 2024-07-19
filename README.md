# Synopsys Scan Yocto Script - bd_yocto_import_sbom.py

# PROVISION OF THIS SCRIPT
This script is provided under the MIT license (see LICENSE file).

It does not represent any extension of licensed functionality of Synopsys software itself and is provided as-is, without warranty or liability.

If you have comments or issues, please raise a GitHub issue here. Synopsys support is not able to respond to support tickets for this OSS utility. Users of this pilot project commit to engage properly with the authors to address any identified issues.

# INTRODUCTION
## OVERVIEW OF BD_YOCTO_IMPORT_SBOM

This utility is intended to scan Yocto projects to create Synopsys Black Duck projects.

This is an alternative to other Yocto scan processes (including [Synopsys Detect](https://detect.synopsys.com/doc) and [bd-scan-yocto](https://github.com/matthewb66/bd_scan_yocto)),
both of which require access to the full build environment to export dependencies from Bitbake, and/or scan compiled sources and installed packages.

This utility uses the outputs of Bitbake commands to create an SPDX SBOM file for import to Black Duck without the need to run within the build environment itself.
The SPDX SBOM file can optionally be imported directly into Black Duck to create a project version and 
can optionally use the output of the `cve_patch` custom class to identify locally patched CVEs which are applied to the Black Duck project as vulnerability updates.

## INSTALLATION

1. Clone the repository
2. Create virtualenv
3. Install required dependencies:
   1. Run `pip3 install blackduck`

## EXECUTION

Run the utility using python:

    python main.py OPTIONS

## USAGE

      usage: bd-yocto-import-sbom [-h] [--blackduck_url BLACKDUCK_URL] [--blackduck_api_token BLACKDUCK_API_TOKEN] [--blackduck_trust_cert] [-p PROJECT] [-v VERSION] [-l LICENSE_MANIFEST]
                             [-b BITBAKE_LAYERS] [-c CVE_CHECK_FILE] [-o OUTPUT] [--debug] [--logfile LOGFILE]

      Create BD Yocto project from license.manifest
      
      optional arguments:
        -h, --help            Show this help message and exit
        --blackduck_url BLACKDUCK_URL
                              Black Duck server URL (REQUIRED - can use BLACKDUCK_URL env var)
        --blackduck_api_token BLACKDUCK_API_TOKEN
                              Black Duck API token (REQUIRED - can use BLACKDUCK_API_TOKEN env var)
        --blackduck_trust_cert
                              Black Duck trust server cert (can use BLACKDUCK_TRUST_CERT env var)
        -p PROJECT, --project PROJECT
                              Black Duck project to create (REQUIRED)
        -v VERSION, --version VERSION
                              Black Duck project version to create (REQUIRED)
        -l LICENSE_MANIFEST, --license_manifest LICENSE_MANIFEST
                              license.manifest file path (REQUIRED - default 'license.manifest)
        -b BITBAKE_LAYERS, --bitbake_layers BITBAKE_LAYERS
                              File containing output of 'bitbake-layers show-recipes' command (REQUIRED)
        -c CVE_CHECK_FILE, --cve_check_file CVE_CHECK_FILE
                              CVE check output file
        -o OUTPUT, --output OUTPUT
                              Specify output SBOM SPDX file for manual upload (if specified then BD project will not be created automatically and CVE patching not supported)
        --get_oe_data         Download and use OE data to check layers, versions & revisions
        --oe_data_folder FOLDER
                              Folder to contain OE data files - if files do not exist they will be downloaded, if files exist then will be used without download
        --debug               Debug logging mode
        --logfile LOGFILE     Logging output file

## OPTIONS

--blackduck_url, --blackduck_api_token, --blackduck_trust_cert:

: Connection credentials to Black Duck server. Can also be picked up from the environment variables BLACKDUCK_URL,
BLACKDUCK_API_TOKEN and BLACKDUCK_TRUST_CERT. Required to create the BD project version automatically and optionally 
process CVE patch status.

--output SBOM_FILE:

: Create an output SBOM file as specified for manual upload; do not create BD project version. Either
specify the BD credentials or use this option to create an output SBOM file. 

--project PROJECT --version VERSION:

: Black Duck project and version to create.

--license_manifest LICENSE_MANIFEST_FILE:

: Yocto license.manifest file created by Bitbake. Usually located in the folder 
`tmp/deploy/licenses/<yocto-image>-<yocto-machine>/license.manifest`

--bitbake_layers BITBAKE_OUTPUT_FILE:

: Output of the command `bitbake-layers show-recipes` stored in the specified file.

--cve_checkfile CVE_CHECK_FILE:

: Output file from run of the `cve_check` custom class which generates a list of patched CVEs. Usually located in the
folder `build/tmp/deploy/images/XXX`.

--get_oe_data:

: Download all layers/recipes/layers from layers.openembedded.org APIs to review origin layers and revision to 
ensure more accurate matching and complete BOMs.

--oe_data_folder:

: Create OE data files in the specified folder if not already existing. If OE data files exist already in this folder,
use them to review layers and revisions to ensure more accurate matching and complete BOMs. Allows offline usage
of OE data or reduction of large data transfers if script is run frequently.