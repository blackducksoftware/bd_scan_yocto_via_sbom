import logging


class Vuln:
    def __init__(self, data):
        self.data = data

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
