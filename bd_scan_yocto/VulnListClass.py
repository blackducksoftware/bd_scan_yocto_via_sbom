from .VulnClass import Vuln
import aiohttp
import asyncio


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

    async def async_ignore_vulns(self, conf, bd):
        token = bd.session.auth.bearer_token
        vulns_per_cycle = 250
        ignored_count = 0
        index = 0

        while True:
            async with aiohttp.ClientSession(trust_env=True) as session:
                vuln_tasks = []
                for vuln in self.vulns[index:]:
                    if vuln.is_patched():
                        continue
                    index += 1
                    vuln_task = asyncio.ensure_future(vuln.async_ignore_vuln(conf, session, token))
                    vuln_tasks.append(vuln_task)
                    if len(vuln_tasks) >= vulns_per_cycle:
                        break

                vuln_data = dict(await asyncio.gather(*vuln_tasks))
                await asyncio.sleep(0.250)

            ignored_count += len(vuln_data)
            if index >= len(self.vulns):
                break
        return ignored_count
