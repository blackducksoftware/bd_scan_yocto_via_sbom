import logging
from blackduck import Client
import sys
import requests
import time
import os
import json
from pathlib import Path
import platform
import asyncio

from .ComponentListClass import ComponentList
from .ComponentClass import Component
from .VulnListClass import VulnList
from .RecipeClass import Recipe
# from .RecipeListClass import RecipeList
# from .ConfigClass import Config
# from .SBOMClass import SBOM


class BOM:
    def __init__(self, conf: "Config"):
        self.bdprojname = conf.bd_project
        self.bdvername = conf.bd_version
        self.complist = ComponentList()
        self.vulnlist = VulnList()
        self.CVEPatchedVulnDict = {}
        self.CVEIgnoredVulnDict = {}
        self.CVEProductCPEDict = {}
        self.bdver_dict = None
        self.projver = None

        self.bd = Client(
            token=conf.bd_api,
            base_url=conf.bd_url,
            verify=(not conf.bd_trustcert),  # TLS certificate verification
            timeout=conf.api_timeout
        )

        try:
            self.bd.list_resources()
        except Exception as exc:
            logging.error(f'Unable to connect to Black Duck server - {str(exc)}')
            sys.exit(2)

    def get_proj(self):
        logging.info(f"Working on project '{self.bdprojname}' version '{self.bdvername}'")
        self.bdver_dict = self.get_projdata()
        if not self.bdver_dict:
            return False
        return True

    def _get_codelocations(self):
        links = self.bdver_dict['_meta']['links']
        cl_link = next((item for item in links
                         if item["rel"] in ("codelocations", "codeLocations", "code-locations")), None)
        if not cl_link:
            logging.debug(f"No codelocations link on project version - available rels: "
                          f"{[item.get('rel') for item in links]}")
            return None

        return self.get_paginated_data(
            cl_link['href'], "application/vnd.blackducksoftware.internal-1+json")

    def unmap_codelocations(self):
        num_unmapped = 0
        try:
            codelocations = self._get_codelocations()
            if codelocations is None:
                logging.warning("Unable to unmap code locations - no codelocations link found on project version")
                return num_unmapped

            for codelocation in codelocations:
                url = codelocation['_meta']['href']
                codelocation['mappedProjectVersion'] = None
                res = self.bd.session.put(url, json=codelocation)
                if res.ok:
                    num_unmapped += 1
                else:
                    logging.warning(f"Unable to unmap code location '{codelocation.get('name')}' - "
                                    f"status code {res.status_code}")
        except Exception as exc:
            logging.warning(f"Unable to unmap code locations - {exc}")
            return num_unmapped

        logging.info(f"- Unmapped {num_unmapped} code location(s) from project '{self.bdprojname}' "
                     f"version '{self.bdvername}'")
        return num_unmapped

    def get_comps(self):
        self.complist = ComponentList()  # Reset component list

        res = self.bd.list_resources(self.bdver_dict)
        self.projver = res['href']
        thishref = f"{self.projver}/components"

        bom_arr = self.get_paginated_data(thishref, "application/vnd.blackducksoftware.bill-of-materials-6+json")

        for comp in bom_arr:
            if 'componentVersion' not in comp:
                continue
            # compver = comp['componentVersion']

            compclass = Component(comp['componentName'], comp['componentVersionName'], comp)
            self.complist.add(compclass)

        return

    def get_data(self, url, accept_hdr):
        try:
            headers = {
                'accept': accept_hdr,
            }
            res = self.bd.get_json(url, headers=headers)
            return res['items']
        except KeyError as e:
            logging.exception(f"Unable to get_data() - {e}")
        return []

    def get_paginated_data(self, url, accept_hdr):
        headers = {
            'accept': accept_hdr,
        }
        url = url + "?limit=1000"
        res = self.bd.get_json(url, headers=headers)
        if 'totalCount' in res and 'items' in res:
            total_comps = res['totalCount']
        else:
            return []

        ret_arr = []
        downloaded_comps = 0
        while downloaded_comps < total_comps:
            downloaded_comps += len(res['items'])

            ret_arr += res['items']

            newurl = f"{url}&offset={downloaded_comps}"
            res = self.bd.get_json(newurl, headers=headers)
            if 'totalCount' not in res or 'items' not in res:
                break

        return ret_arr

    def count_comps(self):
        return self.complist.count()

    def get_projdata(self):
        params = {
            'q': "name:" + self.bdprojname,
            'sort': 'name',
        }

        ver_dict = None
        projects = self.bd.get_resource('projects', params=params)
        for p in projects:
            if p['name'] == self.bdprojname:
                versions = self.bd.get_resource('versions', parent=p, params=params)
                for v in versions:
                    if v['versionName'] == self.bdvername:
                        ver_dict = v
                        break
                break
        else:
            logging.warning(f"Project '{self.bdprojname}' does not exist")
            return None

        if ver_dict is None:
            logging.warning(f"Version '{self.bdvername}' does not exist in project '{self.bdprojname}'")
            return None

        return ver_dict

    def get_vulns(self):
        vuln_url = f"{self.projver}/vulnerable-bom-components"
        vuln_arr = self.get_paginated_data(vuln_url, "application/vnd.blackducksoftware.bill-of-materials-6+json")
        self.vulnlist.add_list(vuln_arr)
        return len(vuln_arr)

    # def print_vulns(self):
    #     table, header = self.vulnlist.print(self.bd)
    #     print(tabulate(table, headers=header, tablefmt="tsv"))
    #

    def process_patched_cves(self, conf: "Config"):
        num = self.get_vulns()
        logging.info(f"- {num} vulns reported in BD project")

        logging.info("- Getting detailed data for linked vulnerabilities ...")
        self.process_vulns_async(conf)

        # patched, skipped = self.vulnlist.process_patched(self.CVEPatchedVulnList, self.bd)
        # logging.info(f"- {patched} CVEs marked as patched in BD project ({skipped} already patched)")

        #DEBUG

        patched = self.patch_vulns_async(conf, self.CVEPatchedVulnDict)
        ignored = self.ignore_vulns_async(conf, self.CVEIgnoredVulnDict)
        logging.info("")
        logging.info("CVE SUMMARY:")
        logging.info(f"- {patched} CVEs marked as PATCHED in BD project")
        logging.info(f"- {ignored} CVEs marked as IGNORED in BD project")
        return

    def _find_scan_id_for_sbom(self, sbom_filename):
        # Try to identify the code location/scan created by uploading sbom_filename, so its
        # own bom-status/{scanId} can be polled instead of the project-version aggregate
        # bom-status, which can read UP_TO_DATE before this scan's processing has even started.
        # Black Duck names SPDX-import code locations after the project/version (e.g.
        # "<project>-<version>-1.0 spdx/sbom"), not after the uploaded file, so match on that.
        try:
            codelocations = self._get_codelocations()
            if codelocations is None:
                return None

            prefix = f"{self.bdprojname}-{self.bdvername}"
            matches = [cl for cl in codelocations if cl.get('name', '').startswith(prefix)]
            if not matches:
                logging.debug(f"No codelocation found matching project/version prefix '{prefix}'")
                return None

            matches.sort(key=lambda cl: cl.get('updatedAt', cl.get('createdAt', '')), reverse=True)
            cl = matches[0]

            # bom-status/{scanId} expects the scan-summary id, not the codelocation's own id -
            # fetch the codelocation's scan-summaries to get it.
            scans_link = next((item for item in cl.get('_meta', {}).get('links', [])
                                if item["rel"] == "scans"), None)
            if not scans_link:
                logging.debug(f"No scans link on codelocation '{cl.get('name')}'")
                return None

            scan_summaries = self.get_paginated_data(scans_link['href'], "application/json")
            if not scan_summaries:
                logging.debug(f"No scan summaries found for codelocation '{cl.get('name')}'")
                return None

            scan_summaries.sort(key=lambda s: s.get('createdAt', ''), reverse=True)
            scan_id = scan_summaries[0]['_meta']['href'].rstrip('/').split('/')[-1]
            logging.debug(f"Resolved codelocation '{cl.get('name')}' for uploaded SBOM "
                          f"'{os.path.basename(sbom_filename)}' -> scan id {scan_id}")
            return scan_id

        except Exception as e:
            logging.debug(f"Unable to resolve scan-specific BOM status for '{sbom_filename}' - {e}")
            return None

    def wait_for_bom_completion(self, sbom_filename=None):
        # Check job status
        uptodate = False

        logging.info("Waiting for project BOM processing to complete ...")
        try:
            time.sleep(5)
            links = self.bdver_dict['_meta']['links']
            link = next((item for item in links if item["rel"] == "bom-status"), None)

            agg_href = link['href']
            scan_href = None
            if sbom_filename:
                scan_id = self._find_scan_id_for_sbom(sbom_filename)
                if scan_id:
                    scan_href = f"{agg_href}/{scan_id}"

            href = scan_href or agg_href
            confirmations_needed = 1 if scan_href else 2
            confirmed = 0

            loop = 0
            while not uptodate and loop < 80:
                resp = self.bd.get_json(href)

                if href == scan_href:
                    status = resp.get('status')
                    if status == 'SUCCESS':
                        uptodate = True
                    elif status == 'FAILURE':
                        logging.error("BOM processing failed for uploaded SBOM (scan status FAILURE)")
                        return False
                    elif status in ('NOT_INCLUDED', 'BUILDING'):
                        uptodate = False
                    else:
                        logging.warning(f"Unexpected scan bom-status value '{status}' - falling back "
                                        f"to aggregate BOM status")
                        href = agg_href
                        confirmations_needed = 2
                        confirmed = 0
                        continue
                else:
                    if 'status' in resp:
                        is_up_to_date = (resp['status'] == 'UP_TO_DATE')
                    elif 'upToDate' in resp:
                        is_up_to_date = resp['upToDate']
                    else:
                        logging.error('Unable to determine bom status')
                        return False

                    confirmed = confirmed + 1 if is_up_to_date else 0
                    uptodate = confirmed >= confirmations_needed

                if not uptodate:
                    time.sleep(5)
                loop += 1

        except Exception as e:
            logging.error(str(e))
            return False

        return uptodate

    def upload_sbom(self, conf: "Config", sbom: "SBOM", allow_create_custom_comps=False):
        url = self.bd.base_url + "/api/scan/data"
        headers = {
            'X-CSRF-TOKEN': self.bd.session.auth.csrf_token,
            'Authorization': f"Bearer {self.bd.session.auth.bearer_token}",
            'Accept': '*/*',
        }

        create_custom_comps = conf.run_custom_components
        if not allow_create_custom_comps:
            create_custom_comps = False

        try:
            with open(sbom.file, 'rb') as sbom_fh:
                files = {'file': (sbom.file, sbom_fh, 'application/spdx')}
                multipart_form_data = {
                    'projectName': conf.bd_project,
                    'versionName': conf.bd_version,
                    'autocreate': create_custom_comps
                }
                # headers['Content-Type'] = 'multipart/form-data; boundary=6o2knFse3p53ty9dmcQvWAIx1zInP11uCfbm'
                response = requests.post(url, headers=headers, files=files, data=multipart_form_data,
                                         verify=(not conf.bd_trustcert))

            if response.status_code == 201:
                return True
            else:
                # Try to extract meaningful error message
                repjson = response.content.decode('utf8')
                err = json.loads(repjson)
                err_text = err['errorMessage']

                raise Exception(f"Return code {response.status_code} - error {err_text}")

        except Exception as e:
            logging.error("Unable to POST SPDX data")
            logging.error(e)

        return False

    def process_cve_file(self, cve_file, reclist: "RecipeList"):
        if cve_file.endswith('.cve'):
            return self.process_cve_file_cve(cve_file, reclist)

        elif cve_file.endswith('.json'):
            return self.process_cve_file_json(cve_file, reclist)
        return False

    def process_cve_file_cve(self, cve_file, reclist: "RecipeList"):
        try:
            cvefile = open(cve_file, "r")
            cvelines = cvefile.readlines()
            cvefile.close()
        except Exception as e:
            logging.error("Unable to open CVE check output file\n" + str(e))
            return False

        lookup_dict = {
            'PACKAGE NAME': 'package',
            'PACKAGE VERSION': 'version',
            'CVE': 'CVE',
            'CVE STATUS': 'status',
            'CVE DETAIL': 'detail',
            'CVE DESCRIPTION': 'description'
        }
        patched_vulns = {}
        ignored_vulns = {}
        pkgvuln = {}
        for line in cvelines:
            arr = line.split(":")
            if len(arr) > 1:
                field = arr[0]
                value = arr[1].strip()

                if field in lookup_dict:
                    # check if key seen before
                    pkgvuln_key = lookup_dict[field]
                    if 'CVE' in pkgvuln and pkgvuln_key in pkgvuln:
                        # Duplicate entry - indicates New record
                        if reclist.check_recipe_exists(pkgvuln.get('package', '')):
                            if pkgvuln.get('status') == 'Patched':
                                patched_vulns[pkgvuln['CVE']] = pkgvuln
                            elif pkgvuln.get('status') == 'Ignored':
                                ignored_vulns[pkgvuln['CVE']] = pkgvuln
                        pkgvuln = {}
                    pkgvuln[pkgvuln_key] = value

                # if key == "PACKAGE NAME":
                #     pkgvuln['package'] = value
                # elif key == "PACKAGE VERSION":
                #     pkgvuln['version'] = value
                # elif key == "CVE":
                #     pkgvuln['CVE'] = value
                # elif key == "CVE STATUS":
                #     pkgvuln['status'] = value
                #     if pkgvuln['status'] == "Patched":
                #         cve = pkgvuln['CVE']
                #         if reclist.check_recipe_exists(pkgvuln['package']) and cve not in patched_vulns:
                #             patched_vulns.append(cve)
                #     elif pkgvuln['status'] == "Ignored":
                #         cve = pkgvuln['CVE']
                #         if reclist.check_recipe_exists(pkgvuln['package']) and cve not in ignored_vulns:
                #             ignored_vulns.append(cve)
                #     pkgvuln = {}
                # elif key == "CVE DETAIL":
                #     pkgvuln['detail'] = value
                # elif key == "CVE DESCRIPTION":
                #     pkgvuln['description'] = value

        logging.info(f"      {len(patched_vulns) + len(ignored_vulns)} total patched and ignored CVEs loaded from "
                     f"cve_check file (CVEs not identified in project yet)")
        self.CVEPatchedVulnDict = patched_vulns
        self.CVEIgnoredVulnDict = ignored_vulns
        if len(patched_vulns) > 0 or len(ignored_vulns) > 0:
            return True
        return False

    def process_cve_file_json(self, cve_file, reclist: "RecipeList"):
        try:
            data = None
            with open(cve_file, "r") as cf:
                data = json.load(cf)

            logging.info(f"- loaded CVEs from cve_check file {cve_file}")

            patched_vulns = {}
            ignored_vulns = {}
            product_cpes = {}

            if data and 'package' in data:
                # Parse each JSON object separately
                for obj in data['package']:
                    pkg_name = obj.get('name', '')
                    products = obj.get('products', [])
                    if pkg_name and products:
                        cpes = []
                        for prod in products:
                            prod_str = prod.get('product', '') if isinstance(prod, dict) else ''
                            if not prod_str:
                                continue
                            cpe = self._build_cpe_from_product(prod_str, obj.get('version', ''))
                            if cpe not in cpes:
                                cpes.append(cpe)
                        if cpes:
                            product_cpes[pkg_name] = cpes

                    if 'issue' in obj:
                        issues = obj['issue']
                        for issue in issues:
                            if 'id' not in issue:
                                continue
                            pkgvuln = {
                                'CVE': issue.get('id'),
                                'detail': issue.get('detail', ''),
                                'description': issue.get('description', ''),
                                'package': obj.get('name', ''),
                                'status': issue.get('status', '')
                            }

                            if pkgvuln["status"] == "Patched":
                                if reclist.check_recipe_exists(pkgvuln['package']) and pkgvuln['CVE'] not in patched_vulns:
                                    patched_vulns[pkgvuln['CVE']] = pkgvuln
                            elif pkgvuln["status"] == "Ignored":
                                if reclist.check_recipe_exists(pkgvuln['package']) and pkgvuln['CVE'] not in ignored_vulns:
                                    ignored_vulns[pkgvuln['CVE']] = pkgvuln

                self.CVEPatchedVulnDict = patched_vulns
                self.CVEIgnoredVulnDict = ignored_vulns
                self.CVEProductCPEDict = product_cpes
                logging.info(f"      {len(product_cpes)} package(s) with product/CPE data loaded from cve_check file")

            logging.info(f"      {len(patched_vulns) + len(ignored_vulns)} total patched and ignored CVEs loaded from "
                         f"cve_check file (CVEs not identified in project yet)")
            if len(patched_vulns) > 0 or len(ignored_vulns) > 0:
                return True

        except Exception as e:
            logging.error(f"Unable to process CVE file {cve_file}: {e}")
        return False

    @staticmethod
    def _build_cpe_from_product(product_str, version):
        # cve_check 'products' entries are CVE_PRODUCT values - either 'product' or
        # 'vendor:product' - build a CPE 2.2 URI binding e.g. cpe:/a:vendor:product:version
        # (BD sbom-fields endpoint expects this format, not the 2.3 formatted-string style
        # used elsewhere in this script for /api/cpes searches)
        if ':' in product_str:
            vendor, product = product_str.split(':', 1)
        else:
            vendor, product = product_str, product_str

        cpe = f"cpe:/a:{vendor}:{product}"
        if version:
            cpe += f":{Recipe.clean_version(version)}"
        return cpe

    def _put_component_cpe(self, component_version_href, cpe):
        url = f"{component_version_href}/sbom-fields"
        headers = {
            'Accept': 'application/vnd.blackducksoftware.component-detail-5+json',
            'Content-Type': 'application/vnd.blackducksoftware.component-detail-5+json',
        }
        try:
            res = self.bd.session.put(url, json={'cpe': cpe}, headers=headers)
            if res.ok:
                return True
            logging.warning(f"- Unable to set CPE on component '{component_version_href}' - "
                            f"status code {res.status_code}")
        except Exception as e:
            logging.warning(f"- Error setting CPE on component '{component_version_href}' - {e}")
        return False

    def update_custom_component_cpes(self, conf: "Config", reclist: "RecipeList"):
        # PHASE 7 - update custom components with CPEs extracted from the cve_check file.
        # By default only applied to custom components created earlier in this run
        # (recipe.custom_component); --create_customcomp_cpes extends this to custom
        # components that already existed in the project before this run.
        if not self.CVEProductCPEDict:
            logging.info("- No product/CPE data available from cve_check file (not present in a text-format "
                         "'.cve' file, or no products reported) - skipping")
            return 0

        updated = 0
        skipped = 0
        for recipe in reclist.recipes:
            if recipe.custom_component:
                is_target = True
            elif conf.create_customcomp_cpes and recipe.matched_in_bom and not recipe.cpe_component:
                comp = self.complist.find_component_by_name(recipe.compname)
                is_target = comp is not None and comp.is_custom()
            else:
                is_target = False

            if not is_target:
                continue

            cpes = self.CVEProductCPEDict.get(recipe.name)
            if not cpes:
                continue

            comp = self.complist.find_component_by_name(recipe.compname)
            if comp is None:
                logging.warning(f"- Unable to find component for custom component recipe "
                                f"'{recipe.name}/{recipe.version}' - skipping CPE update")
                skipped += 1
                continue

            href = comp.get_href()
            if not href:
                logging.warning(f"- No component-version href available for custom component "
                                f"'{recipe.name}/{recipe.version}' - skipping CPE update")
                skipped += 1
                continue

            cpe = cpes[0]
            if len(cpes) > 1:
                logging.debug(f"Recipe '{recipe.name}' has {len(cpes)} CPE candidates from cve_check file - "
                              f"using first: '{cpe}'")

            if self._put_component_cpe(href, cpe):
                logging.info(f"- Set CPE '{cpe}' on custom component '{recipe.name}/{recipe.version}'")
                updated += 1
            else:
                skipped += 1

        logging.info(f"- {updated} custom component(s) updated with CPE from cve_check file ({skipped} skipped)")
        return updated

    def run_detect_sigscan(self, conf: "Config", tdir, extra_opt=''):
        import shutil

        cmd = self.get_detect(conf)

        detect_cmd = cmd
        detect_cmd += f" --detect.source.path='{tdir}' --detect.project.name='{conf.bd_project}' " + \
                      f"--detect.project.version.name='{conf.bd_version}' "
        detect_cmd += f"--blackduck.url={conf.bd_url} "
        detect_cmd += f"--blackduck.api.token={conf.bd_api} "
        if conf.bd_trustcert:
            detect_cmd += "--blackduck.trust.cert=true "
        detect_cmd += "--detect.wait.for.results=true "
        if 'detect.timeout' not in conf.detect_opts:
            detect_cmd += f"--detect.timeout={conf.api_timeout} "
        if extra_opt != '':
            detect_cmd += f"{extra_opt} "

        if conf.detect_opts:
            detect_cmd += conf.detect_opts

        logging.debug(f"Detect Sigscan cmd '{detect_cmd}'")
        # output = subprocess.check_output(detect_cmd, stderr=subprocess.STDOUT)
        # mystr = output.decode("utf-8").strip()
        # lines = mystr.splitlines()
        retval = os.system(detect_cmd)
        shutil.rmtree(tdir)

        if retval != 0:
            logging.error("Unable to run Detect Signature scan on package files")
            return False
        else:
            logging.info("Detect scan for Bitbake dependencies completed successfully")

        return True

    @staticmethod
    def get_detect(conf: "Config"):
        cmd = ''
        if not conf.detect_jar:
            tdir = os.path.join(str(Path.home()), "bd-detect")
            if not os.path.isdir(tdir):
                os.mkdir(tdir)
            tdir = os.path.join(tdir, "download")
            if not os.path.isdir(tdir):
                os.mkdir(tdir)
            if not os.path.isdir(tdir):
                logging.error("Cannot create bd-detect folder in $HOME")
                sys.exit(2)
            shpath = os.path.join(tdir, 'detect11.sh')

            j = requests.get("https://detect.blackduck.com/detect11.sh")
            if j.ok:
                with open(shpath, 'wb') as f:
                    f.write(j.content)
                if not os.path.isfile(shpath):
                    logging.error("Cannot download BD Detect shell script -"
                                  " download manually and use --detect-jar-path option")
                    sys.exit(2)

                cmd = "/bin/bash " + shpath + " "
        else:
            cmd = "java -jar " + conf.detect_jar

        return cmd

    def check_recipe_in_bom(self, rec: "RecipeClass"):
        return self.complist.check_recipe_in_list(rec)

    def check_kernel_in_bom(self):
        return self.complist.check_kernel_in_bom()

    # def add_manual_comp(self, comp_url):
    #     try:
    #         posturl = self.projver + "/components"
    #         custom_headers = {
    #             'Content-Type': 'application/vnd.blackducksoftware.bill-of-materials-6+json'
    #         }
    #
    #         postdata = {
    #             "component": comp_url,
    #             "componentPurpose": "Added by CPE (bd_scan_yocto_via_sbom)",
    #             "componentModified": False,
    #             "componentModification": ""
    #         }
    #
    #         r = self.bd.session.post(posturl, data=json.dumps(postdata), headers=custom_headers)
    #         # r.raise_for_status()
    #         if r.status_code == 200:
    #             logging.debug(f"Created manual component {comp_url}")
    #             return True
    #         else:
    #             raise Exception(f"PUT returned {r.status_code}")
    #
    #     except Exception as e:
    #         logging.exception(f"Error creating manual component - {e}")
    #     return False

    def ignore_vulns_async(self, conf: "Config", cve_dict):
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        count = asyncio.run(self.vulnlist.async_ignore_vulns(conf, self.bd, cve_dict))
        return count

    def patch_vulns_async(self, conf: "Config", cve_dict):
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        count = asyncio.run(self.vulnlist.async_patch_vulns(conf, self.bd, cve_dict))
        return count

    def process(self, reclist: "RecipeListClass", sbom_filename=None):
        if not self.wait_for_bom_completion(sbom_filename):
            logging.warning("BOM processing completion could not be confirmed - recipe match "
                            "results below may be based on a partially-processed BOM")
        self.get_comps()
        reclist.mark_recipes_in_bom(self)

    def process_vulns_async(self, conf):
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self.vulnlist.add_relatedvuln_data(asyncio.run(self.vulnlist.async_get_bdsa_data(self.bd, conf)))
