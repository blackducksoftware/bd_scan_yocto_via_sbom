# Synopsys Scan Yocto Script - bd_scan_yocto_via_sbom.py v1.0.7

# PROVISION OF THIS SCRIPT
This script is provided under the MIT license (see LICENSE file).

It does not represent any extension of licensed functionality of Synopsys software itself and is provided as-is, without warranty or liability.

If you have comments or issues, please raise a GitHub issue here. Synopsys support is not able to respond to support tickets for this OSS utility. Users of this pilot project commit to engage properly with the authors to address any identified issues.

# INTRODUCTION
## OVERVIEW OF BD_SCAN_YOCTO_VIA_SBOM

This utility is intended to:
- Scan a Yocto project to generate an SPDX SBOM file which can be uploaded to the specified Black Duck server to create a project version
- Filter recipes using data from the OpenEmbedded APIs to 'fix-up' recipes moved to new layers or with different versions/revisions
- Signature scan packages/downloaded archives (not from OE)
- Apply patches for locally patched CVEs identified from `cve_patch` if this data is available

This utility has some benefits over the alternative Black Duck Yocto scan processes [Synopsys Detect](https://detect.synopsys.com/doc) and [bd-scan-yocto](https://github.com/matthewb66/bd_scan_yocto), in particular by matching modified original OE recipes and not needing to specify the Bitbake environment script to run Detect Bitbake dependency scans.

<!-- Note that, from Black Duck version 2024.7 onwards, the use of SPDX SBOM upload provides for the optional, automatic creation of custom components 
for recipes not matched in the BD KB. This would enable the creation of a complete SBOM including 3rd party or local, custom components. -->

See the RECOMMENDATIONS section below for guidance on optimising Yocto project scans using this utility.

## INSTALLATION

1. Create virtualenv
2. Run `pip3 install bd_scan_yocto_via_sbom`

Alternatively, if you want to manage the repository locally:

1. clone the repository
2. Create virtualenv
3. Build the utility `python -m build`
4. Install the package `pip3 install dist/bd_scan_yocto_via_sbom-1.0.X-py3-none-any.whl`

## EXECUTION

Run the utility as a package:

1. Set the Bitbake environment (for example `source oe-init-build-env`)
2. Invoke virtualenv where utility was installed
3. Run `bd-scan-yocto-via-sbom OPTIONS`

Alternatively, if you have installed the repository locally:

1. Set the Bitbake environment (for example `source oe-init-build-env`)
2. Invoke virtualenv where utility was installed
3. Run `python3 run.py OPTIONS`

## RECOMMENDATIONS

For optimal Yocto scan results, consider the following:

1. The utility will call Bitbake to extract the environment and layer information by default. Locations and other values (license.manifest, machine, target, download_dir, package_dir, image_package_type) extracted from the environment can be overridden using command line options.
2. Use the `--oe_data_folder FOLDER` option to cache the downloaded OE data (~300MB on every run) noting that the data does not change frequently.
3. Add the `cve_check` class to the Bitbake local.conf to ensure patched CVEs are identified, and then check that PHASE 6 picks up the cve-check file (see CVE PATCHING below). Optionally specify the output CVE check file using `--cve_check_file FILE`.
4. Where recipes have been modified from original versions against the OE data, use the `--max_oe_version_distance X.X.X` option to specify fuzzy matching against OE recipes (distance values in the range '0.0.1' to '0.0.10' are recommended).

## OPTIONAL BEHAVIOUR

There are several additional options to modify the behaviour of this utility including:
- Skip use of bitbake command to locate project files by specifying license.manifest and bitbake-layers output files (use `--skip_bitbake`)
- Use data from the OpenEmbedded API to verify original recipes, layers, version to ensure they match known components in the BD KB (use `--skip_oe_data` to skip)
- Cache OE data in JSON files in a local folder to remove need to download on every run (use `--oe_data_folder FOLDER`)
- Specify semantic version distance for matching recipes against OE data (default distance is '0.0.0' - use `--max_oe_version_distance X.X.X`)
- Create SPDX output file for manual upload (do not upload to Black Duck to create project - use `--output_file OUTPUT`)
- Specify license.manifest, machine, target, download_dir, package_dir, image_package_type to override values extracted from Bitbake environment
- Skip Signature scan of downloaded archives and packages (use `--skip_sig_scan`)

## USAGE

      usage: bd-scan-yocto-via-sbom [-h] [--blackduck_url BLACKDUCK_URL] [--blackduck_api_token BLACKDUCK_API_TOKEN] [--blackduck_trust_cert] [-p PROJECT] [-v VERSION]
                  [-l LICENSE_MANIFEST] [-b BITBAKE_LAYERS] [-c CVE_CHECK_FILE] [-o OUTPUT] [--debug] [--logfile LOGFILE]

      Create BD Yocto project from license.manifest
      
     -h, --help            show this help message and exit
     --blackduck_url BLACKDUCK_URL
                           Black Duck server URL (REQUIRED - can use
                           BLACKDUCK_URL env var)
     --blackduck_api_token BLACKDUCK_API_TOKEN
                           Black Duck API token (REQUIRED - can use
                           BLACKDUCK_API_TOKEN env var)
     --blackduck_trust_cert
                           Black Duck trust server cert (can use
                           BLACKDUCK_TRUST_CERT env var)
     -p PROJECT, --project PROJECT
                           Black Duck project to create (REQUIRED)
     -v VERSION, --version VERSION
                           Black Duck project version to create (REQUIRED)
     -t TARGET, --target TARGET
                           Yocto target (e.g. core-image-sato - REQUIRED if
                           license.manifest not specified)
     -l LICENSE_MANIFEST, --license_manifest LICENSE_MANIFEST
                           license.manifest file path (REQUIRED - default
                           'license.manifest)
     -b BITBAKE_LAYERS, --bitbake_layers_file BITBAKE_LAYERS
                           File containing output of 'bitbake-layers show-
                           recipes' command (REQUIRED)
     -c CVE_CHECK_FILE, --cve_check_file CVE_CHECK_FILE
                           CVE check output file
     -o OUTPUT, --output OUTPUT
                           Specify output SBOM SPDX file for manual upload (if
                           specified then BD project will not be created
                           automatically and CVE patching not supported)
     --skip_oe_data        Download and use OE data to check layers, versions &
                           revisions
     --oe_data_folder OE_DATA_FOLDER
                           Folder to contain OE data files - if files do not
                           exist they will be downloaded, if files exist then
                           will be used without download
     --max_oe_version_distance MAX_OE_VERSION_DISTANCE
                           Where no exact match, use closest previous recipe
                           version up to specified distance.Distance should be
                           specified as MAJOR.MINOR.PATCH (e.g. 0.1.0)
     --build_dir BUILD_DIR
                           Alternative build folder
     --download_dir DOWNLOAD_DIR
                           Download directory where original OSS source is
                           downloaded (usually poky/build/downloads)
     --package_dir PACKAGE_DIR
                           Download directory where package files are downloaded
                           (for example poky/build/tmp/deploy/rpm/<ARCH>)
     --image_package_type IMAGE_PACKAGE_TYPE
                           Package type used for installing packages (e.g. rpm,
                           deb or ipx)
     --skip_sig_scan       Do not Signature scan downloads and packages
     --scan_all_packages   Signature scan all packages (only recipes not matched from
                           OE data are scanned by default)
     --detect_jar_path DETECT_JAR_PATH
                           Synopsys Detect jar path
     --detect_opts DETECT_OPTS
                           Additional Synopsys Detect options
     --api_timeout         Specify API timeout in seconds (default 60) - will be used in
                           Synopsys Detect as --detect.timeout
     --sbom_create_custom_components
                           Create custom components when uploading SBOM (default False)
     --debug               Debug logging mode
     --logfile LOGFILE     Logging output file

## DETAILED DESCRIPTION OF OPTIONS

- --blackduck_url, --blackduck_api_token, --blackduck_trust_cert:
  - Connection credentials to Black Duck server. Can also be picked up from the environment variables BLACKDUCK_URL,
BLACKDUCK_API_TOKEN and BLACKDUCK_TRUST_CERT. Required to create the BD project version automatically and optionally process CVE patch status; not required if `--output` specified.

- --output SBOM_FILE (also -o):
  - Create an output SBOM file for manual upload; do not create BD project version. 

- --project PROJECT --version VERSION (also -p -v):
  - Black Duck project and version to create - REQUIRED

- --license_manifest LICENSE_MANIFEST_FILE (also -l):
  - Optionally specify yocto license.manifest file created by Bitbake. Usually located in the folder `tmp/deploy/licenses/<yocto-image>-<yocto-machine>/license.manifest`. Should be determined from Bitbake environment by default (unless `--skip_bitbake` used).

- --target TARGET (also -t):
  - Bitbake target (e.g. `core-image-sato`) - required unless `--skip_bitbake` used.

- --skip_bitbake:
  - Do not extract Bitbake environment and layers information using Bitbake commands - requires license.manifest and bitbake-layers
output to be specified.

- --bitbake_layers_file BITBAKE_OUTPUT_FILE (also -b):
  - Optionally specify output of the command `bitbake-layers show-recipes` stored in the specified file.  Should be determined from Bitbake environment
by default (unless `--skip_bitbake` used).

- --cve_checkfile CVE_CHECK_FILE:
  - Optionally specify output file from run of the `cve_check` custom class which generates a list of patched CVEs. Usually located in the
folder `build/tmp/deploy/images/XXX`.  Should be determined from Bitbake environment by default (unless `--skip_bitbake` used)

- --skip_oe_data:
  - Do not download layers/recipes/layers from layers.openembedded.org APIs to review origin layers and revisions used in recipes to 
ensure more accurate matching and complete BOMs.

- --oe_data_folder FOLDER:
  - Create OE data files in the specified folder if not already existing. If OE data files exist already in this folder,
use them to review layers and revisions to ensure more accurate matching and complete BOMs. Allows offline usage
of OE data or reduction of large data transfers if script is run frequently.

--skip_sig_scan:

: Do not send identified package and downloaded archives for Signature scanning. By default, only recipes
not matched against OE data will be scanned, use `--scan_all_packages` to scan all recipes.


- --max_oe_version_distance MAJOR.MINOR.PATCH:
  - Specify version distance to enable close (previous) recipe version matching against OE data.
By default, when `--get_oe_data` is specified, OE recipe versions must match the version exactly to replace layers and revision values.
Setting this value will allow close (previous) recipe version matching.
The value needs to be of the format MAJOR.MINOR.PATCH (e.g. '0.10.0').
CAUTION - setting this value to a large value will cause versions of components to be matched against previous recipes maintained in the OE data,
which may lead to different levels of reported vulnerabilities. It is preferable to maintain close relation between the matched
versions and the ones in the project and then to identify unmatched components which can be added as custom components or manually. Consequently
only consider using values which allow versions from different MINOR or MAJOR versions in exceptional circumstances (meaning the supplied
value should probably be in the range 0.0.1 to 0.0.10).

### EXAMPLE DISTANCE CALCULATIONS
- Recipe version is 3.2.4 - closest previous OE recipe version is 3.2.1: Distance value would need to be minimum 0.0.3
- Recipe version is 3.2.4 - closest previous OE recipe version is 3.0.1: Distance value would need to be minimum 0.2.0
- Recipe version is 3.2.4 - closest previous OE recipe version is 2.0.1: Distance value would need to be minimum 1.0.0

Note that lower order values are overriden by higher order (for example distance 1.0.0 is equivalant to 1.999.999).

## CVE PATCHING

For patched CVE remediation in the Black Duck project, you will need to add the `cve_check` bbclass to the Yocto build configuration to generate the CVE check log output. Add the following line to the `build/conf/local.conf` file:

       INHERIT += "cve-check"

Then rebuild the project (using for example `bitbake core-image-sato`)  to run the CVE check action and generate the required CVE log files without a full rebuild.
