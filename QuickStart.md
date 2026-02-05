-----

# Black Duck SCA Scan Yocto Script - Quick Start Guide

-----

### Before You Start
1. Read the [intro sections](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#introduction) to understand why Yocto is challenging to scan and why this script exists.
2. Check [prerequisites](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#prerequisites).

### Installation & Preparation
3. [Install](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#installation) the utility.
4. Obtain Black Duck credentials with correct permissions - optionally set as environment variables (BLACKDUCK_URL and BLACKDUCK_API_TOKEN).
5. Change to the Yocto poky folder and set the Bitbake environment (e.g. by running `source oe-init-build-env`).
6. Check the required [scan modes](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#scan-modes). `ALL` is recommended for full accuracy scans.
7. IF CVE patching from the Yocto build to the BD project is required, ensure [CVE Patching](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#cve-patching) has been enabled in the Yocto config.

### Gather Script Parameters & Options
8. Gather the mandatory parameters:
   1. BD project & version: e.g. `-p BD_PROJECT_NAME` and `-v BD_VERSION_NAME`
   2. Yocto target name: e.g. `-t core-image-sato`
   3. Specify a recipe report file: `--recipe_report RECIPE_REPORT_FILE`
   4. If BD server and API token not set as environment variables: `--blackduck_url BD_URL_TO_USE --blackduck_api_token BD_API_TOKEN_TO_USE`
9. Review the optional parameters:
   1. Optionally specify to trust BD Server certificate: `--blackduck_trust_cert`
   2. Optionally specify a location to store OE recipe data to stop downloading every run: `--oe_data_folder PATH_TO_USE`
   3. Optionally specify license.manifest file (script will use the latest by default): `-l PATH_TO_LICENSE_MANIFEST`
   4. Optionally [override other Yocto locations](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#yocto-project-configuration-parameters---optional)
   5. Optionally lookup OE recipes using [--oe_max_version_distance](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#example-distance-calculations-for---max_oe_version_difference)
   6. Optionally ignore recipes or layers using `--ignore_recipes RECIPE1,RECIPE2` or `--ignore_layers LAYER1,LAYER2`

### Run the Scan
10. Run the scan using `bd_scan_yocto_via_sbom OPTIONS` (or see the [docs](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#if-you-cloned-the-repository-locally) if you want to run from sources)
11. Review the recipe_report output file to see full list of recipes scanned
12. Review scan results in the BD server - check the [troubleshooting](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#troubleshooting) and [FAQ](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#faqs) sections for problems or missing recipes
