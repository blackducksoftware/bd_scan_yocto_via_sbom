-----

# Black Duck SCA Scan Yocto Script - `bd_scan_yocto_via_sbom.py` v1.2.5

-----

## Provision of This Script

This script is provided under the MIT license (see `LICENSE` file).

It does not extend the licensed functionality of Black Duck Software. It is provided as-is, without warranty or liability.

For comments or issues, please **raise a GitHub issue in this repository**. Black Duck Support cannot respond to support tickets for this open-source utility. Users are encouraged to engage with the authors to address any identified issues.

Refer to [How to Report Issues ](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#how-to-report-issues-with-this-script) below for the minimum required information to report issues with this script.

-----

## Introduction

### Overview of `bd_scan_yocto_via_sbom`

This script is for **licensed users of Black Duck Software only**. You will need a Black Duck SCA server and an API key to use it.

While [Black Duck Detect](https://detect.blackduck.com/doc) is the default scan utility for Black Duck SCA and supports Yocto projects, its Yocto scans have limitations. A Detect scan will only identify standard recipes from OpenEmbedded.org and **does not cover**:

  * Modified or custom recipes.
  * Recipes moved to new layers or with changed package versions/revisions.
  * Custom kernel identification or kernel vulnerability mapping.
  * Copyright and deep license data.
  * Snippet or other code scanning within custom recipes.

This utility addresses these gaps by creating a comprehensive Black Duck SCA project from your Yocto build. It achieves this by:

  * Scanning Yocto project artifacts to **generate an SPDX SBOM** (Software Bill of Materials), which is then uploaded to your Black Duck server to create a project version (`--modes OE_RECIPES`)
  * **Filtering and "fixing-up" recipes** using data from the OpenEmbedded (OE) APIs to correctly identify local recipes moved to new layers or with different local versions/revisions.
  * **Signature scanning** packages and downloaded archives for recipes not matched by OE data (with the option to scan all packages - `--modes SIG_SCAN` or `--modes SIG_SCAN_ALL`)
  * **Optionally adding unmatched components** via CPE lookup or by creating custom components through a second SBOM upload (`--modes CPE_COMPS` and/or `--modes CUSTOM_COMPS`)
  * **Applying patches for locally patched CVEs** identified from `cve_check` data (if available - `--modes CVE_PATCHES`)
  * **Optionally processing the Linux Kernel** to filter out vulnerabilities not within the sources compiled into your specific kernel build (`--modes IMAGE_MANIFEST,KERNEL_VULNS`)

For guidance on optimizing Yocto project scans with this utility, refer to the **Best Practice Recommendations** section below.

Note the addition of new `--modes` parameter in v1.2.0+ to control scans to be performed (legacy scan parameters still supported) - see Scan Mode section below.

### Understanding Yocto and Why This Script is Needed

Yocto is a powerful, local build system for creating custom Linux images. It's **not a package manager** but a highly customizable environment. Key characteristics that make comprehensive scanning challenging include:

  * **No Centralized Repository:** Unlike other Linux distributions, Yocto downloads software packages from external locations at build time.
  * **Recipe Misconception:** Yocto recipe names do not fully identify software packages. Standard recipes are provided as templates but are only local text files in a project and can be modified to download different software from anywhere - with the potential for supply chain hacking.
  * **Extensive Customization:** Yocto projects can be heavily modified, with unlimited changes to the build environment, layers, recipes, and the addition of custom recipes and patches.
  * **Hidden Dependencies:** Packages within recipes can embed other open-source software not explicitly listed in the Yocto manifest.
  * **Post-Build Analysis:** Due to Yocto's dynamic nature, it's only feasible to accurately determine what was built and packaged into an image *after* the build is complete.

This script employs multiple techniques to **reverse-engineer a built Yocto project** to identify its included packages, report license information, and map vulnerabilities from the package origins.

The script can also **identify and process the Linux kernel**, determining its custom configuration and modules to ignore vulnerabilities reported against excluded modules.

-----

## Prerequisites

Before running the script, ensure you meet the following requirements:

1.  **Yocto v2.1 or newer**
2.  **Python 3.10 or newer**
3.  **Black Duck SCA server 2024.7 or newer**
4.  **Black Duck SCA API Token** with either:
      * **Global Code Scanner** and **Global Project Manager** roles, OR
      * **Project Code Scanner** and **BOM Manager** roles for an existing project.
      * (Also **Global Component Manager** needed to create custom components if `--mode CUSTOM_COMPS` specified)
5.  **Single-target Bitbake configurations only** are supported. Run this utility on one target at a time.
6.  A **built Yocto project** with access to the build platform. Alternatively, specific outputs from the build can be used, though many script features may be limited so not recommended.
7.  Ensure **license text entries in manifest files are SPDX compliant** to support SBOM upload. Custom licenses are not supported for the creation of custom components (mode=CUSTOM_COMPS).

-----

## Installation

You have a few options for installing this utility:

### Option 1: Install from PyPI (Recommended)

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```
2.  Install the package:
    ```bash
    pip3 install bd_scan_yocto_via_sbom --upgrade
    ```

### Option 2: Build and Install Locally

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd bd_scan_yocto_via_sbom
    ```
2.  Create a virtual environment (if you haven't already):
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```
3.  Build the utility:
    ```bash
    python3 -m build
    ```
4.  Install the package:
    ```bash
    pip3 install dist/bd_scan_yocto_via_sbom-1.0.X-py3-none-any.whl --upgrade
    ```
    (Replace `1.0.X` with the actual version number of the built wheel file.)

### Option 3: Clone Repository and Install Prerequisites

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd bd_scan_yocto_via_sbom
    ```
2.  Ensure prerequisite packages are installed (see the `pyproject.toml` file for a list).
    ```bash
    pip install .
    ```

-----

## How to Run

### If you installed the utility as a package:

1.  Set the Bitbake environment (e.g., `source oe-init-build-env`).
2.  Activate your virtual environment (e.g., `source venv/bin/activate`).
3.  Run the script:
    ```bash
    bd-scan-yocto-via-sbom PARAMETERS
    ```

### If you cloned the repository locally:

1.  Set the Bitbake environment (e.g., `source oe-init-build-env`).
2.  Activate your virtual environment where dependency packages were installed (e.g., `source venv/bin/activate`).
3.  Run the script:
    ```bash
    python3 PATH_TO_REPOSITORY/run.py PARAMETERS
    ```

-----

## Best Practice Recommendations

For optimal Yocto scan results, consider the following:

1.  **Check required scan modes using `--modes`:** - the default scans (if --modes not specified) are `OE_RECIPES,SIG_SCAN,CVE_PATCHES` (same as `--modes DEFAULT`) - see [Scan Modes](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#scan-modes) below.
2.  **Optionally override Bitbake Environment Values:** By default, the utility calls Bitbake to extract environment and layer information, and will refer to the latest Yocto build. You can override values including `license.manifest`, `machine`, `target`, `download_dir`, `package_dir`, and `image_package_type` using command-line parameters.
3.  **Generate a Recipe Report:** Use the `--recipe_report REPFILE` parameter to create a report of matched and unmatched recipes in the BOM, required for analysis and debugging.
4. **Cache OE Data:** The `--oe_data_folder FOLDER` parameter allows you to cache downloaded OE data (approx. 300MB) and reuse it in subsequent runs, saving download time. OE data doesn't change frequently.
5. **Identify Patched CVEs:** Add the `cve_check` class to your Bitbake `local.conf` to identify patched CVEs. Ensure **PHASE 7** picks up the `cve-check` file. Optionally, specify the output CVE check file using `--cve_check_file FILE` if an alternative location is needed. See [CVE Patching](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#cve-patching) for more information.
6. **Fuzzy Match Modified Recipes:** For recipes modified from standard OE versions, optionally use `--max_oe_version_distance X.X.X` (e.g., `0.0.1` to `0.0.10`) for fuzzy matching against OE recipes. Be cautious, as this can sometimes disable correct matches. It's recommended to create two projects and compare results with and without this parameter. See [OE Difference Calculations](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#example-distance-calculations-for---max_oe_version_difference) for more information.
7. **Process Image Manifest:** To include the Linux kernel and other packages specified in the image manifest, consider adding `--modes IMAGE_MANIFEST`. Optionally, specify the `image_license.manifest` file path (`--image_license_manifest FILEPATH`) if the latest build is not desired.
8. **Add Components by CPE:** Add `--modes CPE_COMPS` to create packages not matched by other methods through CPE lookup. Note that not all packages have published CPEs.
9. **Process Kernel Vulnerabilities:** To ignore kernel vulnerabilities not within compiled kernel sources, add `--modes KERNEL_VULNS` (assumes `IMAGE_MANIFEST` mode).
10. **Add Custom Components for Unmatched recipes - USE WITH CAUTION** Where OSS recipes are not matched by any other method, and for custom or commercial recipes, you can consider adding `--modes CUSTOM_COMPS` to create Custom Components for unmatched recipes and add them to the BD project as placeholders. However, note that Custom Components do not have any vulnerabilities mapped, will use the license specified in the license.manifest and cannot be easily deleted once added without deleting the project itself. Also note that all future scans for the same recipe will map to the created Custom Components even when KB updates add new recipes (unless
the associated PURL is deleted under 'Management-->Unmatched Components').

-----

## Scan Modes

The new `--modes` option is a comma-delimited list of modes (no spaces), used to control the multiple types of scan supported in the script.
It can be used to replace existing scan control parameters and simplify the command line.

Explanation of modes:
  - `DEFAULT`        - Includes `OE_RECIPES,SIG_SCAN,CVE_PATCHES`
  - `OE_RECIPES`     - Map components by OE recipe lookup (set by `DEFAULT`)
  - `IMAGE_MANIFEST` - Process image manifest in addition to standard manifest (usually to add linux kernel)
  - `SIG_SCAN`       - Scan unmatched recipes/packages using Signature scan (set in `DEFAULT` mode)
  - `SIG_SCAN_ALL`   - Scan all recipes/packages using Signature scan
  - `CPE_COMPS`      - Add unmatched recipes as packages by CPE lookup (where CPEs available)
  - `CUSTOM_COMPS`   - Create Custom Components for unmatched recipes (note Custom Components are only placeholders for SBOM export - no vulnerability or other data is provided)
  - `CVE_PATCHES`    - Process locally patched CVEs from `cve_check` class (set in `DEFAULT` mode) - See [CVE Patching](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#cve-patching)
  - `KERNEL_VULNS`   - Process kernel modules and mark vulns as unaffected where associated modules do not exist in the kernel
  - `ALL`            - Includes `OE_RECIPES,IMAGE_MANIFEST,SIG_SCAN,CVE_PATCHES,CPE_COMPS,CUSTOM_COMPS,KERNEL_VULNS` (but not `SIG_SCAN_ALL`)

Notes:
  - `DEFAULT` is assumed if `--modes` not specified.
  - To add scan modes to the default set use, for example `--modes DEFAULT,IMAGE_MANIFEST,KERNEL_VULNS`.
  - To add `SIG_SCAN_ALL` mode (scanning all packages) to `ALL` scan mode use `--modes ALL,SIG_SCAN_ALL`.

Mapping of existing scan control parameters to scan modes: 
   * `--process_image_manifest` = mode `IMAGE_MANIFEST`
   * `--scan_all_packages` = mode `SIG_SCAN_ALL`
   * `--add_comps_by_cpe` = mode `CPE_COMPS`
   * `--process_kernel_vulns` = mode `KERNEL_VULNS`
   * `--sbom_create_custom_components` = mode `CUSTOM_COMPS`

Specifying legacy parameters in addition to `--modes` will override scan modes defined in the modes list (including modes in `DEFAULT`).

-----

## Other Scan Options

  * **Improve Recipe Release Identification:** Optionally run `bitbake -g` to create a `task-depends.dot` file which is specified in `--task_depends_dot_file FILE` along with `-l license.manifest`. If `-l license.manifest` is *not* also specified, all development dependencies will be processed (not just those within the license manifest).
  * **Signature scan ALL packages (as opposed to only unmatched packages):** Add `--modes SIG_SCAN_ALL` to scan all packages.
  * **Turn on Snippet scanning within Signature scanned packages:** Requires `--modes SIG_SCAN` or `--modes SIG_SCAN_ALL` - add the parameter `--detect_opts detect.blackduck.signature.scanner.snippet.matching=SNIPPET_MATCHING` to enable snippet scanning of sources within scanned packages.

-----

## Command Line Parameters

```
usage: bd-scan-yocto-via-sbom [-h] [--blackduck_url BLACKDUCK_URL] [--blackduck_api_token BLACKDUCK_API_TOKEN] [--blackduck_trust_cert] [-p PROJECT] [-v VERSION] <OTHER PARAMETERS>

Create BD-SCA project version from Yocto project
```

  * `-h, --help`: Show help message and exit.

### Black Duck Project Parameters - REQUIRED:

  * `--blackduck_url BLACKDUCK_URL`: Black Duck server URL (also uses `BLACKDUCK_URL` environment variable).
  * `--blackduck_api_token BLACKDUCK_API_TOKEN`: Black Duck API token (also uses `BLACKDUCK_API_TOKEN` environment variable).
  * `-p PROJECT, --project PROJECT`: Black Duck project to create or update.
  * `-v VERSION, --version VERSION`: Black Duck project version to create or update.
  * `-t TARGET, --target TARGET`: Yocto target (e.g., 'core-image-sato' - single target configuration only supported).
  * `--blackduck_trust_cert`: Trust Black Duck server certificate (also uses `BLACKDUCK_TRUST_CERT` environment variable) - OPTIONAL.

### Scan Mode Configuration Parameter - OPTIONAL:

  * `--modes MODES`: A comma-delimited list of scan modes (no spaces) selected from [ALL,DEFAULT,OE_RECIPES,IMAGE_MANIFEST,SIG_SCAN,SIG_SCAN_ALL,CVE_PATCHES,CPE_COMPS,CUSTOM_COMPS,KERNEL_VULNS] - see [Scan Modes](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#scan-modes).

### Yocto Project Configuration Parameters - OPTIONAL:

  * `-l LICENSE_MANIFEST, --license_manifest LICENSE_MANIFEST`: The most recent Yocto `license.manifest` file is located by default, usually located in `tmp/deploy/licenses/<yocto-image>-<yocto-machine>/license.manifest`. Use this option to specify a different build or if the file is in a non-standard location (or if `--skip_bitbake` is used).
  * `-i IMAGE_LICENSE_MANIFEST, --image_license_manifest IMAGE_LICENSE_MANIFEST`: If `--modes IMAGE_MANIFEST` specified, the latest image manifest will be identified by default from the environment. Specify the path to an alternate `image_license.manifest` file if the latest build is not desired or the file exists in another location.  
  * `--task_depends_dot_file FILE`: Specify the path to the `task-depends.dot` file created by `bitbake -g` for processing. If `-l license.manifest` is *not* also specified, all recipes, including dev dependencies, will be processed (`--target` is also required).
  * `-b BITBAKE_LAYERS, --bitbake_layers_file BITBAKE_LAYERS`: Optionally specify the output of the command `bitbake-layers show-recipes` stored in a file. Should be used with `--skip_bitbake` (although it will prevent many other script modes from operating, so it's **not recommended**).
  * `-c CVE_CHECK_FILE, --cve_check_file CVE_CHECK_FILE`: CVE check output file (in `.cve` or `.json` format) to mark locally patched CVEs. The most recent file will be located by default; use this parameter to specify an alternate file. Usually located in `build/tmp/deploy/images/XXX`. Should be determined from the Bitbake environment by default (unless `--skip_bitbake` is used).
  * `--build_dir BUILD_DIR`: Alternate Yocto build folder (defaults to `poky/build`).
  * `--download_dir DOWNLOAD_DIR`: Alternate directory where original OSS source is downloaded (defaults to `poky/build/downloads`).
  * `--package_dir PACKAGE_DIR`: Alternate directory where package files are downloaded (e.g., `poky/build/tmp/deploy/rpm/<ARCH>`).
  * `--image_package_type IMAGE_PACKAGE_TYPE`: Package type used for installing packages (specify one of `rpm`, `deb`, or `ipx` - default `rpm`).
  * `--kernel_recipe RECIPE_NAME`: Define a non-standard kernel recipe name (defaults to 'linux-yocto').

### Script Behavior Parameters - OPTIONAL:

  * `--skip_oe_data`: Do not download layers/recipes/layers from `layers.openembedded.org` APIs. These are used to review origin layers and revisions within recipes to ensure more components are matched against the Black Duck KnowledgeBase (KB). Useful where recipes have been moved to new layers against the template recipes provided by OE - (equivalent to removing OE_RECIPES from --modes).
  * `--oe_data_folder OE_DATA_FOLDER`: Folder to contain OE data files. If files don't exist, they will be downloaded; if they exist, they will be used without re-downloading. Creates OE data files in the specified folder if they don't already exist. If files exist, they are used without re-downloading. This allows offline usage of OE data or reduces large data transfers if the script is run frequently. **RECOMMENDED.**
  * `--max_oe_version_distance MAX_OE_VERSION_DISTANCE`: When no exact match, use the closest previous recipe version up to the specified distance against OE data. Setting this value allows close (previous) recipe version matching. The value must be in `MAJOR.MINOR.PATCH` format (e.g., `0.10.0`). **CAUTION**: Setting this value too high may cause components to be matched against older recipes in the OE data, potentially leading to different vulnerability reports. It's generally better to maintain a close relationship between matched versions and project versions. Consider values in the range `0.0.1` to `0.0.10`. See [OE Difference Calculations](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#example-distance-calculations-for---max_oe_version_difference).
  * `--skip_sig_scan`: Do not signature scan downloads and packages. By default, only recipes not matched from OE data are scanned (equivalent to removing SIG_SCAN from --modes)

### Connection & Detect Configuration Parameters - OPTIONAL:

  * `--detect_jar_path DETECT_JAR_PATH`: Path to the Detect JAR file.
  * `--detect_opts DETECT_OPTS`: Additional Detect options, comma separated list (remove leading `--` from Detect options).
  * `--api_timeout`: Specify API timeout in seconds (default 60). Used in Detect as `--detect.timeout`.
  * `--no_unmap`: Do not unmap previous code locations (scans) when running the initial scan (default is to unmap).

### Legacy Scan Mode Parameters (replaced by --modes):

  * `--process_image_manifest`: Process the `image_license.manifest` file (default location) to include recipes from the core image - equivalent to `--modes IMAGE_MANIFEST`.
  * `--add_comps_by_cpe`: Look up CPEs for packages not mapped in the BOM or discovered by signature scan and add missing packages. Note: not all packages have published CPEs - equivalent to `--modes CPE_COMPS`.
  * `--process_kernel_vulns`: Process compiled kernel sources to ignore vulnerabilities affecting modules not compiled into the custom kernel. Requires `--process_image_manifest` - equivalent to `--modes KERNEL_VULNS`.
  * `--scan_all_packages`: Signature scan all packages (default: only recipes not matched from OE data are scanned) - equivalent to `--modes SIG_SCAN_ALL`.
  * `--sbom_create_custom_components`: Create Custom Components when *all other* scan techniques do not match recipes. The license reported in `license.manifest` will be used. Custom Components are designed for unknown components but lack associated vulnerabilities, deep license data, or copyrights. **Caution**: This parameter creates new, permanent custom components mapped to PURLs. These PURLs will be matched in all future scans, even if new data is added to the KB for the recipe. Use the **Manage --\> Unmatched Origins** view to disassociate PURLs from custom components if you don't want them matched in future scans. Deleting custom components once created and referenced in projects is not possible unless the projects themselves are removed. Do not use this parameter until you fully understand its implications - equivalent to `--modes CUSTOM_COMPS`.

### General Parameters:

  * `--recipe_report REPFILE`: Create a report file with a list of recipes, including those not matched in the BOM.
  * `-o OUTPUT, --output OUTPUT`: Specify output SPDX SBOM file. If specified, only the initial SBOM will be created and all other script features will be skipped (use for debug purposes only).
  * `--debug`: Enable debug logging mode.
  * `--logfile LOGFILE`: Output logging messages to a specified file.

-----

### Minimum Required Parameters

To run the script, you must provide:

`--blackduck_url BD_URL --blackduck_api_token BD_API -p BD_PROJECT -v BD_VERSION -t YOCTO_TARGET`

Optionally, add `--blackduck_trust_cert` to trust the Black Duck server certificate.

Consider using `--oe_data_folder FOLDER` with an existing folder to **cache OE recipe data** on subsequent runs, saving large downloads.

Server credentials can also be specified using the standard environment variables: `BLACKDUCK_URL`, `BLACKDUCK_API_TOKEN`, and `BLACKDUCK_TRUST_CERT`.

-----

### Example Distance Calculations for `--max_oe_version_difference`

  * Recipe version is `3.2.4` - closest previous OE recipe version is `3.2.1`: Distance value needed: minimum `0.0.3`
  * Recipe version is `3.2.4` - closest previous OE recipe version is `3.0.1`: Distance value needed: minimum `0.2.0`
  * Recipe version is `3.2.4` - closest previous OE recipe version is `2.0.1`: Distance value needed: minimum `1.0.0`

Note that lower-order values are overridden by higher-order values (e.g., a distance of `1.0.0` is equivalent to `1.999.999`).

-----

## CVE Patching

The Yocto `cve_check` class processes Bitbake dependencies within the development environment, generating a list of CVEs identified from the NVD for *all* packages in that environment.

For patched CVE remediation in your Black Duck project, you need to add the `cve_check` bbclass to your Yocto build configuration to generate the CVE check log output. Add the following line to your `build/conf/local.conf` (or similar) file:

```
INHERIT += "cve-check"
```

Then, **rebuild your project** (e.g., using `bitbake core-image-sato`) to run the CVE check action and generate the required CVE log files without a full rebuild.

The script should automatically locate the `cve-check` output file (usually under `poky/tmp/deploy/images/licenses`), but you can also specify the file using the `--cve_check_file CVE_CHECK_FILE` parameter.

The `CVE_PATCHES` mode enables this feature which is included in the `DEFAULT` mode. Remove `CVE_PATCHES` from the list of modes to disable.

-----

## Troubleshooting

  * **Ensure required parameters are specified**: Double-check that you've provided all minimum required parameters, including the Yocto target (`-t`).
  * **Verify prerequisites and build status**: Confirm all prerequisites are met and that you have a built Yocto project with a generated `license.manifest` file - see [Prerequisites](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#prerequisites)
  * **Enable debug logging**: Use the `--debug` parameter to turn on detailed logging.
  * **Check code locations in Black Duck**: After the scan, verify that your Black Duck project's **Source** tab shows 2 or 3 separate code locations: one for the initial SBOM import, one for Signature Scan, and optionally one for the second SBOM used to create CPE matching/custom components.
  * **Review Recipe matching information**: Specify `--recipe_report FILE` to create a full list of recipes and examine missing recipes; consider using `--max_oe_version_difference X.X.X` to enable fuzzy matching of OE recipes, or adding additional scan modes to add missing recipes.
  * **Missing packages**: If a specific package appears missing from the project, confirm you are looking for the **recipe name**, not the package name (See [FAQs](https://github.com/blackducksoftware/bd_scan_yocto_via_sbom?tab=readme-ov-file#faqs) for an explanation of Yocto recipes vs. packages). The scan modes `SIG_SCAN`, `CPE_COMPS` and `CUSTOM_COMPS` can be specified in `--modes` to process missing recipes using various techniques (alternatively use `--modes ALL`).
  * **Linux kernel missing**: Consider adding the `--modes IMAGE_MANIFEST` mode to include packages in the image manifest, which usually includes the Linux kernel. Use `--image_license_manifest PATH` to specify a different path to the `image_license.manifest` file if in a non-standard location or the latest build is not desired. Check the Linux Kernel recipe name ('linux-yocto' is expected - use parameter `--kernel_recipe mylinux` to specify a non-standard recipe name for the kernel). If the kernel still isn't identified due to a custom name format, consider adding the required kernel version manually to the project.
  * **Unable to upload SPDX file during script run**: All licenses in the license.manifest must be valid SPDX licenses for the SBOM to be importable. Check licenses at https://spdx.org/licenses/. Note that license text in the license.manifest is only used for components added as Custom Components (CUSTOM_COMPS), and is not referenced for components added by the OE_RECIPES,IMAGE_MANIFEST,SIG_SCAN,CPE_COMPS options as the licenses from the KB will be used instead, but the license entries must be SPDX compliant to be uploadable.

-----

## How to Report Issues with This Script

If you encounter issues, please **create an issue in GitHub** and include the following information:

  * Your Organization name (to validate your Black Duck license).
  * A clear description of the issue.
  * Yocto version in use (obtain with `bitbake -e | grep DISTRO_CODENAME`).
  * The `license.manifest` file for your build (and optionally `image_license.manifest` is mode `IMAGE_MANIFEST` is used.
  * The output of the command `bitbake-layers show-recipes` in a file.
  * The log output from this script with `--debug` enabled (use `--logfile LOGFILE` to save to a file).
  * The recipe report file (use `--recipe_report REPFILE`).

-----

## Additional Scan Possibilities (Outside This Script)

For custom C/C++ recipes or recipes built with other languages and package managers, you can combine this script with other scan types:

  * **C/C++ Recipes**: The advanced [blackduck\_c\_cpp](https://pypi.org/project/blackduck-c-cpp/) utility can be used during the build process to identify compiled sources, system includes, and operating system dependencies. You would need to modify the recipe's build command to call `blackduck-c-cpp` as part of a scanning cycle after configuring it to connect to your Black Duck server.
  * **Package Manager-Based Recipes**: For recipes utilizing a package manager, a standard **Detect scan in DETECTOR mode** can be used to analyze project dependencies separately.

**Combining Multiple Scans**: Multiple scans can be combined into the same Black Duck project. Ensure you use the Detect parameter `--detect.project.codelocation.unmap=false` to prevent previous scans from being unmapped.

-----

## Release Notes

* **v1.2.5**
   * Added extra comments in remediated vulns
* **v1.2.4**
   * Updated CVE patching using linked vulns from BDSAs using async calls - should mark vulns in BD project as patched/ignored
* **v1.2.3**
   * Removed license entries from SBOM in phase 3 to support non-compliant license types.
* **v1.2.2**
   * Merged PR to support IGNORED vulnerability types (in addition to PATCHED) and 
* **v1.2.1**
   * Minor fix for CPE lookup version strings
* **v1.2.0**
   * Addition of --modes option to simplify multiple scan mode options:
   * Modes string can contain comma separated list (no spaces) from [ALL, OE_RECIPES*, IMAGE_MANIFEST, SIG_SCAN*, SIG_SCAN_ALL, CVE_PATCHES*, CPE_COMPS, CUSTOM_COMPS, KERNEL_VULNS] (modes marked with * run by default)
   * Note that legacy options to control scan modes are still supported
* **v1.1.4**
   * Minor bug fix for sbom_create_custom_components and more
* **v1.1.3**
   * Minor fix to enforce --process_image_manifest if --process_kernel_vulns specified (as image manifest required to locate kernel image package and extract kernel modules).
* **v1.1.2**
   * Improved custom component creation by SBOM import: added to the second SBOM import (which runs when `--add_comps_by_cpe` is specified).
   * Moved SBOM custom component creation step to after Signature scan alongside optional addition of packages using CPE - to ensure custom packages only added if truly unmatched.
   * Removed date/time from SBOM document name and signature scan temporary folder names, allowing rescanning without unmapping (required for Detect 11). Default unmapping will be removed when Detect 11 is implemented.
   * Removed asyncio as dependency (bundled in Python 3.4+)
* **v1.1.1**
   * Minor fix for `cve_check` output file identification.
* **v1.1.0**
   * Added `--add_comps_by_cpe` parameter to look for unmatched packages via CPE.
   * Changed vulnerability patching to use asynchronous updates for improved speed.
   * Added custom kernel source scanning to ignore vulnerabilities affecting uncompiled kernel modules (requires `--process_kernel_vulns` and `process_image_manifest`).

-----

## FAQs

1.  **Why can't I rely on the license data provided by Yocto in the `license.manifest` file?**
    The licenses reported by Bitbake come directly from the recipe files. However, the true applicable license for each package is the one declared in its origin repository, which may differ. Furthermore, most open-source licenses require the full license text and copyrights in the distribution. Many OSS packages also embed other OSS with different licenses, sometimes with re-licensing restrictions. Black Duck uses licenses from the origin packages, supports full license text and copyrights, and offers optional deep license analysis to identify embedded licenses within packages. Licenses from recipes are used when Custom Components are created using `--modes CUSTOM_COMPS`.

2.  **Can this utility be used on a Yocto image without access to the build environment?**
    Yes, potentially. Use the parameters `--skip_bitbake -l LIC_MANIFEST_FILE --bitbake_layers_file LAYERS_FILE`, where `LIC_MANIFEST_FILE` is the path to your `license.manifest` file and `LAYERS_FILE` contains the output of `bitbake-layers show-recipes`. However, several scan modes will be disabled due to the lack of build artefacts (including Signature scanning
of packages `--modes SIG_SCAN`, CVE patching `--modes CVE_PATCHES` and kernel vulnerability applicability `--modes KERNEL_VULNS`).

4.  **Why can't I simply use the `cve-check` class provided by Yocto to determine unpatched vulnerabilities?**
    The `cve-check` class processes all recipes in the build and attempts to associate CVEs from the NVD using CPEs. This often leads to a large number of false positive CVEs, as it reports all packages (including build dependencies) rather than just those in the distributed image and the CPE is a wildcard often associating many vulnerabilities which are false
positive. Furthermore, the CPE association data from the NVD is frequently inaccurate with no earliest affected version meaning that newer vulnerabilities are shown for all previous
verisons of packages. Black Duck Security Advistories are expert-curated to reduce false positives including marking CVEs as ignored where they should not apply.

5.  **Why couldn't I just use the `create-spdx` class provided by Yocto to export a full SBOM?**
    The Yocto `create-spdx` class generates SPDX JSON files for packages, including data like file lists and hashes. However, many SPDX fields (e.g., license text, copyrights) are often blank (`NO-ASSERTION`), and packages are not identified by PURL, stopping import into other tools (including Black Duck).

6.  **I cannot see a specific package in the Black Duck project.**
    Black Duck reports **recipes** in the Yocto project, not individual **packages**. Multiple packages can be combined into a single recipe and are generally considered part of that recipe's main component. Use the `--recipe_report FILE` parameter to list matched and missing recipes, and conider using other scan modes (`--modes ALL` or
`--modes CPE_COMPS,CUSTOM_COMPS`) to add missing recipes. Note also that Signature scan (`--modes SIG_SCAN` or `--modes SIG_SCAN_ALL`) can identify missing recipes as well as
embedded OSS within recipes.

7.  **I cannot see the Linux kernel in the Black Duck project.**
    Consider using the `--modes IMAGE_MANIFEST` (optionally with `--image_license_manifest PATH`) to process packages in the image manifest, which usually includes the Linux kernel. If the kernel still cannot be identified due to a custom name format, consider adding the required kernel version manually to the project.

8.  **I am using another Yocto wrapper like KAS ([https://kas.readthedocs.io/](https://kas.readthedocs.io/)) and cannot run Bitbake, or the script fails for some other reason.**
    Use the parameters `--skip_bitbake -l LIC_MANIFEST_FILE --bitbake_layers_file LAYERS_FILE`, where `LIC_MANIFEST_FILE` is the path to your `license.manifest` file and `LAYERS_FILE` contains the output of `bitbake-layers show-recipes`. Note that this will disable several features, including CVE patching, kernel vulnerability identification, and package scanning.

9.  **I want to scan all recipes, including development dependencies, as opposed to only those in the delivered image.**
    Run the command `bitbake -g` to create a `task-depends.dot` file, then use the parameter `--task_depends_dot_file FILE`, where `FILE` is the path to the generated file.

10. **Unable to upload SPDX file during script run in phase 5**: Where mode=CUSTOM_COMPS, licenses for custom compponents to be added from the license.manifest must be valid SPDX licenses for the SBOM to be importable. Check licenses at https://spdx.org/licenses/ (suggest checking compliance via an LLM) and modify any non-compliant license text in recipes or manifest files. Note that license text in the manifest files is only used to define the licenses for components added as Custom Components (CUSTOM_COMPS), but is not used for components added by the OE_RECIPES,IMAGE_MANIFEST,SIG_SCAN,CPE_COMPS options which will reference the licenses from the KB instead. Resolved licenses can be modified within the project version or globally once components have been added to the BOM.

