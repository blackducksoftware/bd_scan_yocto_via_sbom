import logging
from blackduck import Client
import sys
import requests
import time
import os
from pathlib import Path

from .ComponentListClass import ComponentList
from .ComponentClass import Component
from .VulnListClass import VulnList


class BOM:
    def __init__(self, conf):
        self.bdprojname = conf.bd_project
        self.bdvername = conf.bd_version
        self.complist = ComponentList()
        self.vulnlist = VulnList()
        self.CVEPatchedVulnList = []
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

    def count_comps(self):
        return self.complist.count()

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
    def upload_sbom(conf, bom, sbom):
        url = bom.bd.base_url + "/api/scan/data"
        headers = {
            'X-CSRF-TOKEN': bom.bd.session.auth.csrf_token,
            'Authorization': f"Bearer  {bom.bd.session.auth.bearer_token}",
            'Accept': '*/*',
        }

        try:
            files = {'file': (sbom.file, open(sbom.file, 'rb'), 'application/spdx')}
            multipart_form_data = {
                'projectName': conf.bd_project,
                'versionName': conf.bd_version,
                'autocreate': conf.sbom_custom_components
            }
            # headers['Content-Type'] = 'multipart/form-data; boundary=6o2knFse3p53ty9dmcQvWAIx1zInP11uCfbm'
            response = requests.post(url, headers=headers, files=files, data=multipart_form_data,
                                     verify=(not conf.bd_trustcert))

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

    def run_detect_sigscan(self, conf, tdir):
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
    def get_detect(conf):
        cmd = ''
        if not conf.detect_jar:
            tdir = os.path.join(str(Path.home()), "synopsys-detect")
            if not os.path.isdir(tdir):
                os.mkdir(tdir)
            tdir = os.path.join(tdir, "download")
            if not os.path.isdir(tdir):
                os.mkdir(tdir)
            if not os.path.isdir(tdir):
                logging.error("Cannot create synopsys-detect folder in $HOME")
                sys.exit(2)
            shpath = os.path.join(tdir, 'detect9.sh')

            j = requests.get("https://detect.synopsys.com/detect9.sh")
            if j.ok:
                open(shpath, 'wb').write(j.content)
                if not os.path.isfile(shpath):
                    logging.error("Cannot download Synopsys Detect shell script -"
                                  " download manually and use --detect-jar-path option")
                    sys.exit(2)

                cmd = "/bin/bash " + shpath + " "
        else:
            cmd = "java " + conf.detect_jar

        return cmd

    def check_recipe_in_bom(self, name, ver):
        return self.complist.check_recipe_in_list(name, ver)
