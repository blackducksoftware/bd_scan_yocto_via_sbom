from .VulnClass import Vuln


class VulnList:
    def __init__(self):
        self.vulns = []

    def add_list(self, data):
        for vulndata in data:
            vuln = Vuln(vulndata)
            self.vulns.append(vuln)

    def process_patched(self, cve_list, bd):
        patched = 0
        skipped = 0
        for vuln in self.vulns:
            cve = vuln.get_cve(bd)
            if cve in cve_list:
                if vuln.is_patched():
                    skipped += 1
                    continue
                if vuln.patch(bd):
                    patched += 1
        return patched, skipped

    def print(self, bd):
        table = []
        vulnid_list = []
        for vuln in self.vulns:
            if vuln.id() in vulnid_list:
                continue
            vulnid_list.append(vuln.id())
            table.append([vuln.id(), vuln.status(), vuln.severity(), vuln.component(), vuln.get_linked_vuln(bd)])

        return table, ["ID", "Status", "Severity", "Component", "Linked Vuln"]
