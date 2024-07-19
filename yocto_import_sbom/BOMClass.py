from .ComponentListClass import ComponentList
from .ComponentClass import Component
from .VulnListClass import VulnList
# from VulnClass import Vuln
from . import global_values
import logging
from blackduck import Client
import sys
import requests
import time


class BOM:
    def __init__(self, proj, ver):
        self.bdprojname = proj
        self.bdvername = ver
        self.complist = ComponentList()
        self.vulnlist = VulnList()
        self.CVEPatchedVulnList = []
        self.bdver_dict = None
        self.projver = None

        self.bd = Client(
            token=global_values.bd_api,
            base_url=global_values.bd_url,
            verify=(not global_values.bd_trustcert),  # TLS certificate verification
            timeout=60
        )

        try:
            self.bd.list_resources()
        except Exception as exc:
            logging.error(f'Unable to connect to Black Duck server - {str(exc)}')
            sys.exit(2)

    def get_proj(self):
        logging.info(f"Working on project '{self.bdprojname}' version '{self.bdvername}'")
        self.bdver_dict = self.get_project()

    def get_data(self):
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

    def get_project(self):
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
            logging.error(f"Version '{self.bdvername}' does not exist in project '{self.bdprojname}'")
            sys.exit(2)

        if ver_dict is None:
            logging.warning(f"Project '{self.bdprojname}' does not exist")
            sys.exit(2)

        return ver_dict

    def get_vulns(self):
        vuln_url = f"{self.projver}/vulnerable-bom-components"
        vuln_arr = self.get_paginated_data(vuln_url, "application/vnd.blackducksoftware.bill-of-materials-6+json")
        self.vulnlist.add_list(vuln_arr)

    # def print_vulns(self):
    #     table, header = self.vulnlist.print(self.bd)
    #     print(tabulate(table, headers=header, tablefmt="tsv"))
    #

    def process_patched_cves(self):
        self.get_vulns()

        count = self.vulnlist.process_patched(self.CVEPatchedVulnList, self.bd)

        logging.info(f"- {count} CVEs marked as patched in BD project")
        return

    def wait_for_bom_completion(self):
        # Check job status
        uptodate = False

        logging.info("Waiting for project BOM processing to complete ...")
        try:
            links = self.bdver_dict['_meta']['links']
            link = next((item for item in links if item["rel"] == "bom-status"), None)

            href = link['href']
            # headers = {'Accept': 'application/vnd.blackducksoftware.internal-1+json'}
            # resp = hub.execute_get(href, custom_headers=custom_headers)
            loop = 0
            while not uptodate and loop < 80:
                # resp = hub.execute_get(href, custom_headers=custom_headers)
                resp = self.bd.get_json(href)
                if 'status' in resp:
                    uptodate = (resp['status'] == 'UP_TO_DATE')
                elif 'upToDate' in resp:
                    uptodate = resp['upToDate']
                else:
                    logging.error('Unable to determine bom status')
                    return False
                if not uptodate:
                    time.sleep(15)
                loop += 1

        except Exception as e:
            logging.error(str(e))
            return False

        logging.info("Project scan processing complete")
        return uptodate

    @staticmethod
    def upload_sbom(bd, sbom_file):
        url = bd.base_url + "/api/scan/data"
        headers = {
            'X-CSRF-TOKEN': bd.session.auth.csrf_token,
            'Authorization': f"Bearer  {bd.session.auth.bearer_token}",
            'Accept': '*/*',
        }

        try:
            files = {'file': (sbom_file, open(sbom_file, 'rb'), 'application/spdx')}
            multipart_form_data = {
                'projectName': global_values.bd_project,
                'versionName': global_values.bd_version
            }
            # headers['Content-Type'] = 'multipart/form-data; boundary=6o2knFse3p53ty9dmcQvWAIx1zInP11uCfbm'
            response = requests.post(url, headers=headers, files=files, data=multipart_form_data,
                                     verify=(not global_values.bd_trustcert))

            if response.status_code == 201:
                return True
            else:
                raise Exception(f"Return code {response.status_code}")

        except Exception as e:
            logging.error("Unable to POST SPDX data")
            logging.error(e)

        return False

    def process_cve_file(self, cve_file, reclist):
        try:
            cvefile = open(cve_file, "r")
            cvelines = cvefile.readlines()
            cvefile.close()
        except Exception as e:
            logging.error("Unable to open CVE check output file\n" + str(e))
            sys.exit(3)

        patched_vulns = []
        pkgvuln = {}
        cves_in_bm = 0
        for line in cvelines:
            arr = line.split(":")
            if len(arr) > 1:
                key = arr[0]
                value = arr[1].strip()
                if key == "PACKAGE NAME":
                    pkgvuln['package'] = value
                elif key == "PACKAGE VERSION":
                    pkgvuln['version'] = value
                elif key == "CVE":
                    pkgvuln['CVE'] = value
                elif key == "CVE STATUS":
                    pkgvuln['status'] = value
                    if pkgvuln['status'] == "Patched":
                        patched_vulns.append(pkgvuln['CVE'])
                        if reclist.check_recipe_exists(pkgvuln['package']):
                            cves_in_bm += 1
                    pkgvuln = {}

        logging.info(f"      {len(patched_vulns)} total patched CVEs identified of which {cves_in_bm}"
                     f" are for recipes in the yocto image")
        self.CVEPatchedVulnList = patched_vulns
        return
