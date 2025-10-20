import logging
import datetime
from enum import Enum


class Vuln:
    class RemediationStatus(str, Enum):
        PATCHED = 'PATCHED'
        IGNORED = 'IGNORED'

    def __init__(self, data):
        self.data = data
        self.cve = ''

    def id(self):
        try:
            return self.data['vulnerabilityWithRemediation']['vulnerabilityName']
        except KeyError:
            return ''

    def status(self):
        try:
            return self.data['vulnerabilityWithRemediation']['remediationStatus']
        except KeyError:
            return ''

    def severity(self):
        try:
            return self.data['vulnerabilityWithRemediation']['severity']
        except KeyError:
            return ''

    def related_vuln(self):
        try:
            return self.data['vulnerabilityWithRemediation']['relatedVulnerability'].split('/')[-1]
        except KeyError:
            return ''

    def component(self):
        try:
            return f"{self.data['componentName']}/{self.data['componentVersionName']}"
        except KeyError:
            return ''

    def get_linked_vuln(self, bd):
        vuln_url = f"{bd.base_url}/api/vulnerabilities/{self.id()}"
        vuln_data = self.get_data(bd, vuln_url, "application/vnd.blackducksoftware.vulnerability-4+json")

        try:
            if vuln_data['source'] == 'BDSA':
                for x in vuln_data['_meta']['links']:
                    if x['rel'] == 'related-vulnerability':
                        if x['label'] == 'NVD':
                            cve = x['href'].split("/")[-1]
                            return cve
                        break
            else:
                return self.id()
        except KeyError:
            return ''

    @staticmethod
    def get_data(bd, url, accept_hdr):
        headers = {
            'accept': accept_hdr,
        }
        res = bd.get_json(url, headers=headers)
        return res

    def get_cve(self, bd):
        if self.data['vulnerabilityWithRemediation']['source'] == 'NVD':
            return self.id()
        elif self.data['vulnerabilityWithRemediation']['source'] == 'BDSA':
            rel_vuln = self.related_vuln()
            if not rel_vuln:
                rel_vuln = self.get_linked_vuln(bd)
            return rel_vuln

        return ''

    def patch(self, bd):
        status = "PATCHED"
        comment = "Patched by bitbake recipe"

        try:
            # vuln_name = comp['vulnerabilityWithRemediation']['vulnerabilityName']
            self.data['remediationStatus'] = status
            self.data['remediationComment'] = comment
            # result = hub.execute_put(comp['_meta']['href'], data=comp)
            href = self.data['_meta']['href']
            # href = '/'.join(href.split('/')[3:])
            r = bd.session.put(href, json=self.data)
            r.raise_for_status()
            if r.status_code != 202:
                raise Exception(f"PUT returned {r.status_code}")

        except Exception as e:
            logging.error("Unable to update vulnerabilities via API\n" + str(e))
            return False

        logging.info(f"Patched vulnerability {self.id()}")
        return True

    def is_remediated(self, remediationStatus):
        try:
            if ('vulnerabilityWithRemediation' in self.data and
                    'remediationStatus' in self.data['vulnerabilityWithRemediation']):
                if self.data['vulnerabilityWithRemediation']['remediationStatus'] == remediationStatus:
                    return True
                else:
                    return False
            if self.data['ignored']:
                return True
        except Exception as e:
            logging.error(f"Error in is_remediated() - {e}")
        return False
    
    def url(self):
        try:
            return self.data['_meta']['href']
        except KeyError:
            return ''
    
    async def async_set_cve(self, conf, session, token):
        self.cve = ''
        if self.data['vulnerabilityWithRemediation']['source'] == 'NVD':
            self.cve = self.id()
        elif self.data['vulnerabilityWithRemediation']['source'] == 'BDSA':
            rel_vuln = self.related_vuln()
            if not rel_vuln:
                if conf.bd_trustcert:
                    ssl = False
                else:
                    ssl = None

                headers = {
                    'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
                    'Authorization': f'Bearer {token}',
                }
                
                async with session.get(self.url(), headers=headers, ssl=ssl) as response:
                    vuln_data = await response.json()
                    
                try:
                    if vuln_data['source'] == 'BDSA':
                        for x in vuln_data['_meta']['links']:
                            if x['rel'] == 'related-vulnerability':
                                if x['label'] == 'NVD':
                                    cve = x['href'].split("/")[-1]
                                    self.cve = cve
                                break
                    else:
                        self.cve = self.id()
                except KeyError:
                    return
            self.cve = rel_vuln
        logging.debug("CVE of " + self.id() + " set to: " + self.cve)


    async def async_remediate_vuln(self, conf, session, token, remediationStatus):
        if conf.bd_trustcert:
            ssl = False
        else:
            ssl = None

        headers = {
            # 'accept': "application/vnd.blackducksoftware.bill-of-materials-6+json",
            'Authorization': f'Bearer {token}',
        }
        # resp = globals.bd.get_json(thishref, headers=headers)
        x = datetime.datetime.now()
        mydate = x.strftime("%x %X")

        payload = self.data
        # payload['remediationJustification'] = "NO_CODE"
        payload['comment'] = f"Remediated by bd_scan_yocto_via_sbom utility {mydate} - fixed locally"
        payload['remediationStatus'] = remediationStatus

        logging.debug(f"{self.id} - {self.url()}")
        async with session.put(self.url(), headers=headers, json=payload, ssl=ssl) as response:
            res = response.status

        return self.id(), res