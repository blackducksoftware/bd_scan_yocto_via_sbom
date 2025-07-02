import logging

from .ComponentClass import Component


class ComponentList:
    def __init__(self):
        self.components = []
        self.component_names = []
        pass

    def add(self, comp: Component):
        self.components.append(comp)
        self.component_names.append(comp.clean_name)

    def count(self):
        return len(self.components)

    def count_ignored(self):
        count = 0
        for comp in self.components:
            if comp.is_ignored():
                count += 1
        return count

    def check_recipe_in_list(self, rec: "RecipeClass"):
        try:
            # for component in self.components:
            #     comp_origs = component.get_origins()
            #     if component.name == 'glibc':
            #         print("glibc")
            #     if comp_origs:
            #         for orig in comp_origs:
            #             arr = orig.split('/')
            #             if recipe_name == arr[0]:
            #                 if recipe_ver == '':
            #                     return True
            #                 elif recipe_ver in arr[1]:
            #                     return True
            #     else:
            #         logging.info(f"ComponentList:check_recipe_in_list: unable to process recipe {recipe_name}")
            if rec.cpe_comp_href:
                if rec.cpe_comp_href in self.get_hrefs():
                    return True
            if rec.name in self.component_names:
                index = self.component_names.index(rec.name)
                comp = self.components[index]
                if comp.version == rec.version:
                    return True

        except Exception as e:
            logging.error(f"Error finding recipe {rec.name} - {e}")

        return False

    def check_kernel_in_bom(self):
        for component in self.components:
            if component.name == 'Linux Kernel':
                return True
        return False

    def get_hrefs(self):
        arr = []
        for comp in self.components:
            href = comp.get_href()
            if href:
                arr.append(href)
        return arr
