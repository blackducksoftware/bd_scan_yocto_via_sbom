# import logging


class Component:
    def __init__(self, name, version, data):
        self.name = name
        self.version = version
        self.data = data
        self.clean_name, self.clean_ver = self.get_clean_name_ver()

    def get_matchtypes(self):
        try:
            return self.data['matchTypes']
        except KeyError:
            return []

    def is_dependency(self):
        dep_types = ['FILE_DEPENDENCY_DIRECT', 'FILE_DEPENDENCY_TRANSITIVE']
        match_types = self.get_matchtypes()
        for m in dep_types:
            if m in match_types:
                return True
        return False

    def is_signature(self):
        sig_types = ['FILE_EXACT', 'FILE_SOME_FILES_MODIFIED', 'FILE_FILES_ADDED_DELETED_AND_MODIFIED',
                     'FILE_EXACT_FILE_MATCH']
        match_types = self.get_matchtypes()
        for m in sig_types:
            if m in match_types:
                return True
        return False

    def is_ignored(self):
        try:
            return self.data['ignored']
        except KeyError:
            return False

    # def get_origins(self):
    #     origlist = []
    #     try:
    #         if 'origins' not in self.data:
    #             return []
    #         for origin in self.data['origins']:
    #             if 'externalNamespace' in origin and origin['externalNamespace'] == 'openembedded':
    #                 orig = origin['externalId'].split('/')
    #                 origlist.append('/'.join(orig[1:]))
    #             elif 'externalId' in origin:
    #                 origlist.append(origin['externalId'])
    #             elif 'componentName' in self.data and 'componentVersionName' in self.data:
    #                 origlist.append(f"{self.data['componentName']}/{self.data['componentVersionName']}")
    #         return origlist
    #     except KeyError as e:
    #         logging.debug(f"Error processing component {self.name}/{self.version} for origins: {e}")
    #         return []

    def get_clean_name_ver(self):
        if self.data:
            if 'origins' not in self.data or len(self.data['origins']) == 0:
                return self.data['componentName'], self.data['componentVersionName']
            else:
                origin = self.data['origins'][0]
                if 'externalNamespace' in origin and 'externalId' in origin:
                    origarr = origin['externalId'].replace('//', '/').split('/')
                    # print(origin['externalId'])
                    if len(origarr) >= 2:
                        if origin['externalNamespace'] == 'openembedded':
                            return origarr[1], origarr[2]
                        elif origin['externalId'].startswith('git:'):
                            if len(origarr) > 4:
                                return origarr[3], origarr[4]
                        else:
                            return origarr[0], origarr[1]

        return self.name, self.version

    def get_href(self):
        if self.data and 'componentVersion' in self.data:
            return self.data['componentVersion']
