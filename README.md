# Synopsys Scan Yocto Script - bd_scan_yocto_via_sbom.py v1.0.12

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

Note that, from Black Duck version 2024.7 onwards, the use of SPDX SBOM upload provides for the optional, automatic creation of custom components 
for recipes not matched in the BD KB using the option `--sbom_create_custom_components`. This would enable the creation of a complete SBOM including 3rd party or local, custom components.

See the RECOMMENDATIONS section below for guidance on optimising Yocto project scans using this utility.

## INSTALLATION

1. Create virtualenv
2. Run `pip3 install bd_scan_yocto_via_sbom`

Alternatively, if you want to manage the repository locally:

1. clone the repository
2. Create virtualenv
3. Build the utility `python -m build`
4. Install the package `pip3 install dist/bd_scan_yocto_via_sbom-1.0.X-py3-none-any.whl`

## PREREQUISITES

1. Yocto v2.1 or newer
2. Black Duck server 2024.1 or newer

## EXECUTION

Run the utility as a package:

1. Set the Bitbake environment (for example `source oe-init-build-env`)
2. Invoke virtualenv where utility was installed
3. Run `bd-scan-yocto-via-sbom OPTIONS`

Alternatively, if you have installed the repository locally:

1. Set the Bitbake environment (for example `source oe-init-build-env`)
2. Invoke virtualenv where utility was installed
3. Run `python3 run.py OPTIONS`

## BEST PRACTICE RECOMMENDATIONS

For optimal Yocto scan results, consider the following:

1. The utility will call Bitbake to extract the environment and layer information by default. Locations and other values (license.manifest, machine, target, download_dir, package_dir, image_package_type) extracted from the environment can be overridden using command line options.
2. Use the `--oe_data_folder FOLDER` option to cache the downloaded OE data (~300MB on every run) noting that the data does not change frequently.
3. Add the `cve_check` class to the Bitbake local.conf to ensure patched CVEs are identified, and then check that PHASE 6 picks up the cve-check file (see CVE PATCHING below). Optionally specify the output CVE check file using `--cve_check_file FILE`.
4. Where recipes have been modified from original versions against the OE data, use the `--max_oe_version_distance X.X.X` option to specify fuzzy matching against OE recipes (distance values in the range '0.0.1' to '0.0.10' are recommended), although this can also cause some matches to be disabled. Create
2 projects and compare the results with and without this option.
5. If you wish to add the Linux kernel and other packages specified in the image manifest only, 
consider using the `--process_image_manifest` option and optionally specifying the image manifest license file path (--image_license_manifest FILEPATH) where it does not exist in the same folder and the license.manifest file.
6. Use the `--recipe_report REPFILE` option to create a report of matched and unmatched recipes in the BOM. In particular check the recipes in the `RECIPES NOT IN BOM - MATCHED IN OE DATA` section.

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
                           'license.manifest')
     -i IMAGE_LICENSE_MANIFEST, --image_license_manifest IMAGE_LICENSE_MANIFEST
                           Specify the image_license.manifest file path to process recipes from the core image.
     --process_image_manifest
                           Process the image_license.manifest file to process recipes from the core image using the
                           default location. Alternatively specify the image_license.manifest file path.
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
     --recipe_report REPFILE
                           Output specified file with a list of recipes including those not matched in the BOM

### MINIMUM REQUIRED OPTIONS

- --blackduck_url BD_URL --blackduck_api_token BD_API -p BD_PROJECT -v BD_VERSION -t YOCTO_TARGET

Optionally add the `--blackduck_trust_cert` option to trust the Black Duck server certificate.
Also consider using `--oe_data_folder FOLDER` with an existing folder to cache the OE recipe data on subsequent runs to save large downloads at each execution.

Server credentials can also be specified using standard environment variables (BLACKDUCK_URL, BLACKDUCK_API_TOKEN and BLACKDUCK_TRUST_CERT).

### DETAILED DESCRIPTION OF OPTIONS

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

- --skip_sig_scan:
- Do not send identified package and downloaded archives for Signature scanning. By default, only recipes
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

- --process_image_manifest OR --image_license_manifest PATH:
  - Process the image_license.manifest file to process and add recipes from the core image to the BOM.
  
### EXAMPLE DISTANCE CALCULATIONS
- Recipe version is 3.2.4 - closest previous OE recipe version is 3.2.1: Distance value would need to be minimum 0.0.3
- Recipe version is 3.2.4 - closest previous OE recipe version is 3.0.1: Distance value would need to be minimum 0.2.0
- Recipe version is 3.2.4 - closest previous OE recipe version is 2.0.1: Distance value would need to be minimum 1.0.0

Note that lower order values are overridden by higher order (for example distance 1.0.0 is equivalant to 1.999.999).

## CVE PATCHING

The Yocto `cve_check` class works on the Bitbake dependencies within the dev environment, and produces a list of CVEs identified from the NVD for ALL packages in the development environment.

For patched CVE remediation in the Black Duck project, you will need to add the `cve_check` bbclass to the Yocto build configuration to generate the CVE check log output. Add the following line to the `build/conf/local.conf` file:

       INHERIT += "cve-check"

Then rebuild the project (using for example `bitbake core-image-sato`)  to run the CVE check action and generate the required CVE log files without a full rebuild.

The script should locate the path for the output file from cve-check, but you can also specify the file using the option `--cve_check_file CVE_CHECK_FILE` which is usually located in the `poky/tmp/deploy/images

## TROUBLESHOOTING

- Ensure that you have specified the required minimum options including the Yocto target (-t).

- Check all the prerequisites, and that there is a built Yocto project with a generated license.manifest file.

- Use the option --debug to turn on debug logging.

- After scan completion, check that there are at least 2 separate code locations in the Source tab in the Black Duck project (one for SBOM import and the other for Signature scan).

- Check the information from PHASE 5 (if it is run) in particular the total components in BOM against total recipes in Yocto project. The `Recipes matched in OE data but not in BOM` counts recipes
which were found in OE data but could not be matched against the BD KB. Check to see if these recipes (also listed in Phase 5) are identified by subsequent Signature scan and consider adding the origin
OSS components as manual additions in the Project Version.

- If you are looking for a specific package which appears to be missing from the project, confirm that you are looking for the recipe name not the package name. See the FAQs for an explanation of Yocto recipes versus packages. Check that the package file was included in the Signature scan (within the Source tab).

## HOW TO REPORT ISSUES WITH THIS SCRIPT

If you encounter issues using the script, then please create an issue in GitHub, ensuring that you include the following information:

- Your Organisation name (to validate you have a Black Duck license)
- Description of the issue
- Yocto version in use (use the command `bitbake -e | grep DISTRO_CODENAME`)
- The `license.manifest` file for the build
- The output of the command `bitbake-layers show-recipes`
- The log output from this script with `--debug` enabled (use the `--logfile LOGFILE` option to output to a file )
- The recipe report file (use `--recipe_report REPFILE`)

# ADDITIONAL SCAN OPTIONS

For a custom C/C++ recipe, or where other languages and package managers are used to build custom recipes, other types of scan could be considered in addition to the techniques used in this script.

For C/C++ recipes, the advanced [blackduck_c_cpp](https://pypi.org/project/blackduck-c-cpp/) utility could be used as part of the build to identify the compiled sources, system includes and operating system dependencies. You would need to modify the build command for the recipe to call the `blackduck-c-cpp` utility as part of a scanning cycle after it had been configured to connect to the Black Duck server.

For recipes where a package manager is used, then a standard Synopsys Detect scan in DETECTOR mode could be utilised to analyse the project dependencies separately.

Multiple scans can be combined into the same Black Duck project (ensure to use the Synopsys Detect option `--detect.project.codelocation.unmap=false` to stop previous scans from being unmapped).

# FAQs

1. Why can't I rely on the license data provided by Yocto in the license.manifest file?

   _The licenses reported by Bitbake come straight from the recipe files used to build the project.
   However, the applicable license for each package is the actual declared license reported in the origin repository,
   which may not match the license name in the recipe used to build/install the package. Furthermore, the obligations of
   most OSS licenses require that the full license text is included in the distribution along with any relevant copyrights.
   Another concern is that most OSS packages use or encapsulate other OSS which can have different licenses to the declared
   license in the main package, and in some cases re-licensing is not allowed meaning that the declared license of the main
   is not applicable. Black Duck uses the licenses from the origin packages (not the Yocto recipe), supports full
   license text and copyrights as well as optional deep license analysis to identify embedded licenses within packages._


2. Can this utility be used on a Yocto image without access to the build environment?

   _Yes possibly - Use the options `--skip_bitbake -l LIC_MANIFEST_FILE --bitbake_layers_file LAYERS_FILE` where LIC_MANIFEST_FILE is the path to the specific license.manifest file and LAYERS_FILE
   contains the output of the command `bitbake-layers show-recipes`.


3. Why can't I simply use the `cve-check` class provided by Yocto to determine unpatched vulnerabilities?

   _The cve-check class processes all recipes in the build and then looks up packages in the NVD to try to associate CVEs. The script reports all packages including build dependencies as opposed to the packages only in the distributed image which is usually not useful.
   The CVE association uses CPE (package enumerators) to match packages, but this uses wildcards which result in a large number of false positive CVEs being reported.
   For example, for a sample Yocto 4.1 minimal build, cve-check reported 160 total unpatched CVEs of which 14 were shown against zlib, however the Black Duck project shows that none of these should be associated with the zlib version in the build (only 3 patched and 0 unpatched vulnerabilities should be shown in the project)._


4. Why couldn't I just use the `create-spdx` class provided by Yocto to export a full SBOM?

   _The Yocto `create-spdx` class produces SPDX JSON files for the packages in the project with the runtime packages also identified,
   including useful data such as the list of files in the image per package with hashes.
   However, many of the SPDX fields are blank (NO-ASSERTION) including license text, copyrights etc.
   The packages are also not identified by PURL so the SBOM cannot be effectively imported into other tools (including Black Duck)._


5. I cannot see a specific package in the Black Duck project.

   _Black Duck reports recipes in the Yocto project not individual packages. Multiple packages can be combined into a single recipe, but these are typically not downloaded separately and are considered to be part of the main component managed by the recipe, not individual OSS components._


6. I cannot see the Linux kernel in the Black Duck project.

   _Consider using the `--process_image_manifest` OR `--image_license_manifest PATH` options to add processing of the
    packages in the image manifest usually including the Linux kernel. Note that the kernel cannot always be identified due to a custom name format being used in Yocto in which case consider adding the required kernel version to the project manually._


7. I am using another Yocto wrapper such as KAS https://kas.readthedocs.io/ and cannot run bitbake, or the script fails for some other reason.

   _Use the options `--skip_bitbake -l LIC_MANIFEST_FILE --bitbake_layers_file LAYERS_FILE` where LIC_MANIFEST_FILE is the path to the specific license.manifest file and LAYERS_FILE
   contains the output of the command `bitbake-layers show-recipes`._

