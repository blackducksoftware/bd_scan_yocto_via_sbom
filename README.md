-----

# Black Duck SCA Scan Yocto Script - `bd_scan_yocto_via_sbom.py` v1.1.4

-----

## Provision of This Script

This script is provided under the MIT license (see `LICENSE` file).

It does not extend the licensed functionality of Black Duck Software. It is provided as-is, without warranty or liability.

For comments or issues, please **raise a GitHub issue in this repository**. Black Duck Support cannot respond to support tickets for this open-source utility. Users are encouraged to engage with the authors to address any identified issues.

-----

## Introduction

### Overview of `bd_scan_yocto_via_sbom`

This script is for **licensed users of Black Duck Software only**. You will need a Black Duck SCA server and an API key to use it.

While [Black Duck Detect](https://detect.blackduck.com/doc) is the default scan utility for Black Duck SCA and supports Yocto projects, its Yocto scans have limitations. The scan will only identify standard recipes from OpenEmbedded.org and **does not cover**:

  * Modified or custom recipes.
  * Recipes moved to new layers or with changed package versions/revisions.
  * Custom kernel identification or kernel vulnerability mapping.
  * Copyright and deep license data.
  * Snippet or other code scanning within custom recipes.

This utility addresses these gaps by creating a comprehensive Black Duck SCA project from your Yocto build. It achieves this by:

  * Scanning Yocto project artifacts to **generate an SPDX SBOM** (Software Bill of Materials), which is then uploaded to your Black Duck server to create a project version.
  * **Filtering and "fixing-up" recipes** using data from the OpenEmbedded (OE) APIs to correctly identify local recipes moved to new layers or with different local versions/revisions.
  * **Signature scanning** packages and downloaded archives for recipes not matched by OE data (with the option to scan all packages).
  * **Optionally adding unmatched components** via CPE lookup or by creating custom components through a second SBOM upload.
  * **Applying patches for locally patched CVEs** identified from `cve_check` data (if available).
  * **Optionally processing the Linux Kernel** to filter out vulnerabilities not within the sources compiled into your specific kernel build.

For guidance on optimizing Yocto project scans with this utility, refer to the **Best Practice Recommendations** section below.

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

-----

## Prerequisites

Before running the script, ensure you meet the following requirements:

1.  **Yocto v2.1 or newer**
2.  **Black Duck SCA server 2024.1 or newer**
3.  **Black Duck SCA API Token** with either:
      * **Global Code Scanner** and **Global Project Manager** roles, OR
      * **Project Code Scanner** and **BOM Manager** roles for an existing project.
4.  **Single-target Bitbake configurations only** are supported. Run this utility on one target at a time.
5.  A **built Yocto project** with access to the build platform. Alternatively, specific outputs from the build can be used, though some script features may be limited.
6.  **Python 3.10 or newer**

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

1.  **Override Bitbake Environment Values:** By default, the utility calls Bitbake to extract environment and layer information. You can override values including `license.manifest`, `machine`, `target`, `download_dir`, `package_dir`, and `image_package_type` using command-line parameters. Use `-l PATH/license.manifest` to specify a different `license.manifest` file (latest build will be used by default).
2.  **Generate a Recipe Report:** Use the `--recipe_report REPFILE` parameter to create a report of matched and unmatched recipes in the BOM, which is useful for analysis and debugging.
3.  **Cache OE Data:** The `--oe_data_folder FOLDER` parameter allows you to cache downloaded OE data (approx. 300MB) and reuse it in subsequent runs, saving download time. OE data doesn't change frequently.
4.  **Identify Patched CVEs:** Add the `cve_check` class to your Bitbake `local.conf` to identify patched CVEs. Ensure **PHASE 6** picks up the `cve-check` file. Optionally, specify the output CVE check file using `--cve_check_file FILE` if an alternative location is needed.
5.  **Fuzzy Match Modified Recipes:** For recipes modified from standard OE versions, use `--max_oe_version_distance X.X.X` (e.g., `0.0.1` to `0.0.10`) for fuzzy matching against OE recipes. Be cautious, as this can sometimes disable correct matches. It's recommended to create two projects and compare results with and without this parameter.
6.  **Process Image Manifest:** To include the Linux kernel and other packages specified in the image manifest, consider using the `--process_image_manifest` parameter. Optionally, specify the `image_license.manifest` file path (`--image_license_manifest FILEPATH`) if the latest build is not required.
7.  **Add Components by CPE:** Use `--add_comps_by_cpe` to add packages not matched by other methods through CPE lookup. Note that not all packages have published CPEs.
8.  **Process Kernel Vulnerabilities:** To ignore kernel vulnerabilities not within compiled kernel sources, use `--process_kernel_vulns`. This parameter also requires `--process_image_manifest`.
9.  **Add Custom Components for Unmatched recipes - USE WITH CAUTION** Where OSS recipes are not matched by any other method, and for custom or commercial recipes, you can consider using the
`--sbom_create_custom_compoents` parameter to create Custom Components for unmatched recipes to add them to the BD project as placeholders. However, note that Custom Components do not have any vulnerabilities mapped, use the license specified in the license.manifest and cannot be easily deleted once added
without deleting the project itself. Also note that all future scans for the same recipe will map to the Custom Components even when KB updates add new recipes unless
the PURL associated is deleted under 'Management-->Unmatched Components'.

-----

## Other Scan Options

Several other options are available to modify the script's behavior:

  * **Skip OE Data:** Use `--skip_oe_data` to bypass downloading OE API data (used for verifying original recipes, layers, and versions).
  * **Improve Recipe Release Identification:** Optionally run `bitbake -g` to create a `task-depends.dot` file and specify `--task_depends_dot_file FILE` along with `-l license.manifest`. If `-l license.manifest` is *not* also specified, it will scan all development dependencies (not just those in the built image).
  * **Generate SBOM for Manual Upload/Debug:** Use `--output_file OUTPUT` to create an SPDX output file for debugging. The script will stop after creating the initial SBOM and will not upload it to Black Duck or process CVE patching.
  * **Control Signature Scanning:**
      * `--skip_sig_scan`: Skips signature scanning of downloaded archives and packages.
      * `--scan_all_packages`: Runs signature scan on *all* packages, not just those unmatched by identifier (useful for deep license and copyright analysis of standard OE recipes and detecting embedded OSS). This may require BOM curation to remove duplicates; consider using the [bd\_sig\_filter](https://github.com/blackducksoftware/bd_sig_filter) script.

-----

## Command Line Parameters

```
usage: bd-scan-yocto-via-sbom [-h] [--blackduck_url BLACKDUCK_URL] [--blackduck_api_token BLACKDUCK_API_TOKEN] [--blackduck_trust_cert] [-p PROJECT] [-v VERSION] <OTHER PARAMETERS>

Create BD Yocto project from license.manifest
```

  * `-h, --help`: Show this help message and exit.

### Required:

  * `--blackduck_url BLACKDUCK_URL`: Black Duck server URL (also uses `BLACKDUCK_URL` environment variable).
  * `--blackduck_api_token BLACKDUCK_API_TOKEN`: Black Duck API token (also uses `BLACKDUCK_API_TOKEN` environment variable).
  * `-p PROJECT, --project PROJECT`: Black Duck project to create or update.
  * `-v VERSION, --version VERSION`: Black Duck project version to create or update.
  * `-t TARGET, --target TARGET`: Yocto target (e.g., 'core-image-sato' - single target configuration only supported).

### Optional:

  * `--blackduck_trust_cert`: Trust Black Duck server certificate (also uses `BLACKDUCK_TRUST_CERT` environment variable).

### Yocto Project Configuration Optional:

  * `-l LICENSE_MANIFEST, --license_manifest LICENSE_MANIFEST`: Path to `license.manifest` file. If not specified, the latest file in the standard location will be used.
  * `--process_image_manifest`: Process the `image_license.manifest` file (default location) to include recipes from the core image.
  * `-i IMAGE_LICENSE_MANIFEST, --image_license_manifest IMAGE_LICENSE_MANIFEST`: Specify the path to `image_license.manifest` to process recipes from the core image (usually including the kernel).
  * `--task_depends_dot_file`: Process the `task-depends.dot` file created by `bitbake -g`. If `license.manifest` is *not* also specified, all recipes, including dev dependencies, will be processed.
  * `-b BITBAKE_LAYERS, --bitbake_layers_file BITBAKE_LAYERS`: File containing output of `bitbake-layers show-recipes`. Only suitable if Bitbake cannot be called locally (reduces accuracy and disables other features).
  * `-c CVE_CHECK_FILE, --cve_check_file CVE_CHECK_FILE`: CVE check output file (in `.cve` or `.json` format) to mark locally patched CVEs. The most recent file will be located by default; use this parameter to specify an alternate file.
  * `--build_dir BUILD_DIR`: Alternate Yocto build folder (defaults to `poky/build`).
  * `--download_dir DOWNLOAD_DIR`: Alternate directory where original OSS source is downloaded (defaults to `poky/build/downloads`).
  * `--package_dir PACKAGE_DIR`: Alternate directory where package files are downloaded (e.g., `poky/build/tmp/deploy/rpm/<ARCH>`).
  * `--image_package_type IMAGE_PACKAGE_TYPE`: Package type used for installing packages (specify one of `rpm`, `deb`, or `ipx` - default `rpm`).
  * `--kernel_recipe`: Define a non-standard kernel recipe name (defaults to 'linux-yocto').

### Script Behavior:

  * `--skip_oe_data`: Do not download OE data to check layers, versions, and revisions.
  * `--oe_data_folder OE_DATA_FOLDER`: Folder to contain OE data files. If files don't exist, they will be downloaded; if they exist, they will be used without re-downloading.
  * `--max_oe_version_distance MAX_OE_VERSION_DISTANCE`: When no exact match, use the closest previous recipe version up to the specified distance (e.g., `0.0.1` to `0.0.10` is recommended).
  * `--skip_sig_scan`: Do not signature scan downloads and packages. By default, only recipes not matched from OE data are scanned.
  * `--scan_all_packages`: Signature scan all packages (default: only recipes not matched from OE data are scanned).
  * `--add_comps_by_cpe`: Look up CPEs for packages not mapped in the BOM or discovered by signature scan and add missing packages. Note: not all packages have published CPEs.
  * `--process_kernel_vulns`: Process compiled kernel sources to ignore vulnerabilities affecting modules not compiled into the custom kernel. Requires `--process_image_manifest`.

### Connection & Detect Configuration:

  * `--detect_jar_path DETECT_JAR_PATH`: Path to the Detect JAR file.
  * `--detect_opts DETECT_OPTS`: Additional Detect options (remove leading `--` from Detect options).
  * `--api_timeout`: Specify API timeout in seconds (default 60). Used in Detect as `--detect.timeout`.
  * `--sbom_create_custom_components`: Create custom components when uploading SBOM (default `False`). **USE WITH CAUTION.**
  * `--no_unmap`: Do not unmap previous code locations (scans) when running the initial scan (default is to unmap).

### General:

  * `--recipe_report REPFILE`: Create a report file with a list of recipes, including those not matched in the BOM.
  * `-o OUTPUT, --output OUTPUT`: Specify output SPDX SBOM file for manual upload. If specified, the Black Duck project will not be created automatically, and CVE patching is not supported.
  * `--debug`: Enable debug logging mode.
  * `--logfile LOGFILE`: Output logging to a specified file.

-----

### Minimum Required Parameters

To run the script, you must provide:

`--blackduck_url BD_URL --blackduck_api_token BD_API -p BD_PROJECT -v BD_VERSION -t YOCTO_TARGET`

Optionally, add `--blackduck_trust_cert` to trust the Black Duck server certificate.

Consider using `--oe_data_folder FOLDER` with an existing folder to **cache OE recipe data** on subsequent runs, saving large downloads.

Server credentials can also be specified using the standard environment variables: `BLACKDUCK_URL`, `BLACKDUCK_API_TOKEN`, and `BLACKDUCK_TRUST_CERT`.

-----

### Detailed Description of Parameters

  * **`--blackduck_url`, `--blackduck_api_token`, `--blackduck_trust_cert`**:
      * **REQUIRED** for automatically creating the Black Duck project version and optionally processing CVE patch status. Can be picked up from environment variables. Not required if `--output` is specified.
  * **`--project PROJECT --version VERSION` (`-p`, `-v`)**:
      * **REQUIRED** Black Duck project and version to update or create.
  * **`--license_manifest LICENSE_MANIFEST_FILE` (`-l`)**:
      * Optionally specify the Yocto `license.manifest` file created by Bitbake. Usually located in `tmp/deploy/licenses/<yocto-image>-<yocto-machine>/license.manifest`. The last build location should be determined from the Bitbake environment by default (unless `--skip_bitbake` is used).
  * **`--target TARGET` (`-t`)**:
      * Bitbake target (e.g., `core-image-sato`). Required unless `--skip_bitbake` is used.
  * **`--skip_bitbake`**:
      * Do not extract Bitbake environment and layers information using Bitbake commands. Requires `bitbake-layers` output to be specified and will prevent multiple features from operating, so it's **not advised**.
  * **`--task_depends_dot_file TASK_DEPENDS_FILE`**:
      * Process `task-depends.dot` file created by `bitbake -g`. If `license.manifest` is *not* also specified, all recipes, including dev dependencies, will be processed. `--target` is also required.
  * **`--bitbake_layers_file BITBAKE_OUTPUT_FILE` (`-b`)**:
      * Optionally specify the output of the command `bitbake-layers show-recipes` stored in a file. Should be used with `--skip_bitbake`, but will prevent many other script features from operating, so it's **not recommended**.
  * **`--output SBOM_FILE` (`-o`)**:
      * Create an output SBOM file for manual upload. Does not create a Black Duck project version and skips additional steps. **Use only for debug purposes.**
  * **`--cve_checkfile CVE_CHECK_FILE`**:
      * Optionally specify the output file from `cve_check` (a custom class that generates a list of patched CVEs). Usually located in `build/tmp/deploy/images/XXX`. Should be determined from the Bitbake environment by default (unless `--skip_bitbake` is used).
  * **`--skip_oe_data`**:
      * Do not download layers/recipes/layers from `layers.openembedded.org` APIs. These are used to review origin layers and revisions within recipes to ensure more components are matched against the Black Duck KnowledgeBase (KB). Useful where recipes have been upgraded to new versions against the template recipes provided by OE.
  * **`--oe_data_folder FOLDER`**:
      * Creates OE data files in the specified folder if they don't already exist. If files exist, they are used without re-downloading. This allows offline usage of OE data or reduces large data transfers if the script is run frequently. **RECOMMENDED.**
  * **`--skip_sig_scan`**:
      * Do not run Signature Scan on packages and downloaded archives for unmatched recipes. By default, recipes *not* matched against OE data will be Signature scanned.
  * **`--scan_all_packages`**:
      * Signature scan all recipes, including those matched against OE recipes. By default, only recipes *not* matched against OE data are Signature scanned.
  * **`--max_oe_version_distance MAJOR.MINOR.PATCH`**:
      * Specify a version distance to enable closest (previous) recipe version matching against OE data where exact matches are unavailable. By default, OE recipe versions must match exactly to replace layers and revision values. Setting this value allows close (previous) recipe version matching. The value must be in `MAJOR.MINOR.PATCH` format (e.g., `0.10.0`).
      * **CAUTION**: Setting this value too high may cause components to be matched against older recipes in the OE data, potentially leading to different vulnerability reports. It's generally better to maintain a close relationship between matched versions and project versions. Consider values in the range `0.0.1` to `0.0.10`.
  * **`--process_image_manifest` OR `--image_license_manifest PATH`**:
      * Include processing of the `image_license.manifest` file to add recipes from the core image to the BOM (usually including the Linux kernel). Also specify `--kernel_recipe XXX` if the kernel recipe is not `linux_yocto`.
  * **`--recipe_report REPFILE`**:
      * Create a report of matched and unmatched recipes in the specified `REPFILE`.
  * **`--add_comps_by_cpe`**:
      * For packages not matched by other techniques (OE recipe name lookup or Signature scan), look up CPEs and add matching components. This will not add all missing packages, as CPEs only exist where CVEs have been reported.
  * **`--process_kernel_vulns`**:
      * Process compiled kernel sources to ignore vulnerabilities affecting modules not compiled into the custom kernel. **Requires** using `--process_image_manifest` to include the kernel recipe and `--kernel_recipe XXX` to specify a non-standard kernel recipe.
  * **`--sbom_create_custom_components` (USE WITH CAUTION)**:
      * Creates Custom Components in Black Duck SCA when *all other* scan techniques do not match recipes. The license reported in `license.manifest` will be used. Custom Components are designed for unknown components but lack associated vulnerabilities, deep license data, or copyrights.
      * **Caution**: This parameter creates new, permanent custom components mapped to PURLs. These PURLs will be matched in all future scans, even if new data is added to the KB for the recipe. Use the **Manage --\> Unmatched Origins** view to disassociate PURLs from custom components if you don't want them matched in future scans. Deleting custom components once created and referenced in projects is not possible unless the projects themselves are removed. Do not use this parameter until you fully understand its implications.

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

-----

## Troubleshooting

  * **Ensure required parameters are specified**: Double-check that you've provided all minimum required parameters, including the Yocto target (`-t`).
  * **Verify prerequisites and build status**: Confirm all prerequisites are met and that you have a built Yocto project with a generated `license.manifest` file.
  * **Enable debug logging**: Use the `--debug` parameter to turn on detailed logging.
  * **Check code locations in Black Duck**: After the scan, verify that your Black Duck project's **Source** tab shows 2 or 3 separate code locations: one for the initial SBOM import, one for Signature Scan, and optionally one for CPE matching/custom components.
  * **Review Phase 6 information**: If Phase 6 runs, check the `total components in BOM` against `total recipes in Yocto project`. The `Recipes matched in OE data but not in BOM` count indicates recipes found in OE data but not matched against the Black Duck KB. Review these (also listed in Phase 5) to see if they were identified by subsequent Signature Scan, and consider manually adding the origin OSS components to the Project Version if needed.
  * **Missing packages**: If a specific package appears missing from the project, confirm you are looking for the **recipe name**, not the package name. (See FAQs for an explanation of Yocto recipes vs. packages.) Also, check that the package file was included in the Signature Scan within the **Source** tab.
  * **Linux kernel missing**: Consider using the `--process_image_manifest` or `--image_license_manifest PATH` parameters to include packages in the image manifest, which usually includes the Linux kernel. If the kernel still isn't identified due to a custom name format, consider adding the required kernel version manually to the project.

-----

## How to Report Issues with This Script

If you encounter issues, please **create an issue in GitHub** and include the following information:

  * Your Organization name (to validate your Black Duck license).
  * A clear description of the issue.
  * Yocto version in use (obtain with `bitbake -e | grep DISTRO_CODENAME`).
  * The `license.manifest` file for your build.
  * The output of the command `bitbake-layers show-recipes`.
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
    The licenses reported by Bitbake come directly from the recipe files. However, the true applicable license for each package is the one declared in its origin repository, which may differ. Furthermore, most open-source licenses require the full license text and copyrights in the distribution. Many OSS packages also embed other OSS with different licenses, sometimes with re-licensing restrictions. Black Duck uses licenses from the origin packages, supports full license text and copyrights, and offers optional deep license analysis to identify embedded licenses within packages.

2.  **Can this utility be used on a Yocto image without access to the build environment?**
    Yes, potentially. Use the parameters `--skip_bitbake -l LIC_MANIFEST_FILE --bitbake_layers_file LAYERS_FILE`, where `LIC_MANIFEST_FILE` is the path to your `license.manifest` file and `LAYERS_FILE` contains the output of `bitbake-layers show-recipes`.

3.  **Why can't I simply use the `cve-check` class provided by Yocto to determine unpatched vulnerabilities?**
    The `cve-check` class processes all recipes in the build and attempts to associate CVEs from the NVD using CPEs. This often leads to a large number of false positive CVEs, as it reports all packages (including build dependencies) rather than just those in the distributed image. For example, a sample Yocto 4.1 minimal build might report 160 unpatched CVEs, with 14 for zlib, while Black Duck might show only 3 patched and 0 unpatched for the zlib version in the build.

4.  **Why couldn't I just use the `create-spdx` class provided by Yocto to export a full SBOM?**
    The Yocto `create-spdx` class generates SPDX JSON files for packages, including useful data like file lists and hashes. However, many SPDX fields (e.g., license text, copyrights) are often blank (`NO-ASSERTION`), and packages are not identified by PURL, making effective import into other tools (including Black Duck) difficult.

5.  **I cannot see a specific package in the Black Duck project.**
    Use the `--recipe_report FILE` parameter to list matched and missing recipes. Black Duck reports recipes in the Yocto project, not individual packages. Multiple packages can be combined into a single recipe and are generally considered part of that recipe's main component. Check if the package file was included in the Signature Scan (within the Source tab).

6.  **I cannot see the Linux kernel in the Black Duck project.**
    Consider using the `--process_image_manifest` or `--image_license_manifest PATH` parameters to process packages in the image manifest, which usually includes the Linux kernel. If the kernel still cannot be identified due to a custom name format, consider adding the required kernel version manually to the project.

7.  **I am using another Yocto wrapper like KAS ([https://kas.readthedocs.io/](https://kas.readthedocs.io/)) and cannot run Bitbake, or the script fails for some other reason.**
    Use the parameters `--skip_bitbake -l LIC_MANIFEST_FILE --bitbake_layers_file LAYERS_FILE`, where `LIC_MANIFEST_FILE` is the path to your `license.manifest` file and `LAYERS_FILE` contains the output of `bitbake-layers show-recipes`. Note that this will disable several features, including CVE patching, kernel vulnerability identification, and package scanning.

8.  **I want to scan all recipes, including development dependencies, as opposed to only those in the delivered image.**
    Run the command `bitbake -g` to create a `task-depends.dot` file, then use the parameter `--task_depends_dot_file FILE`, where `FILE` is the path to the generated file.
