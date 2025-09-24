from .VulnClass import Vuln
import aiohttp
import asyncio
import logging


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
            if cve and cve in cve_list:
                if vuln.is_remediated(vuln.RemediationStatus.PATCHED):
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

    async def async_ignore_vulns(self, conf, bd, cve_list):
        token = bd.session.auth.bearer_token
        logging.info("- Remediate locally ignored vulnerabilities ...")

        async with aiohttp.ClientSession(trust_env=True) as session:
            vuln_tasks = []
            for vuln in self.vulns:
                cve = vuln.related_vuln()
                if cve not in cve_list or vuln.is_remediated(vuln.RemediationStatus.IGNORED):
                    continue
                vuln_task = asyncio.ensure_future(vuln.async_remediate_vuln(conf, session, token,
                                                                            vuln.RemediationStatus.IGNORED))
                vuln_tasks.append(vuln_task)

            vuln_data = dict(await asyncio.gather(*vuln_tasks))
            await asyncio.sleep(0.250)

        return len(vuln_data)

    async def async_patch_vulns(self, conf, bd, cve_list):
        token = bd.session.auth.bearer_token
        logging.info("- Remediate locally patched vulnerabilities ...")

        async with aiohttp.ClientSession(trust_env=True) as session:
            vuln_tasks = []
            for vuln in self.vulns:
                cve = vuln.related_vuln()
                if cve not in cve_list or vuln.is_remediated(vuln.RemediationStatus.PATCHED):
                    continue
                vuln_task = asyncio.ensure_future(vuln.async_remediate_vuln(conf, session, token,
                                                                            vuln.RemediationStatus.PATCHED))
                vuln_tasks.append(vuln_task)

            vuln_data = dict(await asyncio.gather(*vuln_tasks))
            await asyncio.sleep(0.250)

        return len(vuln_data)
