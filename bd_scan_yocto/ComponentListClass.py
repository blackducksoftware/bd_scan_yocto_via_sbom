import logging

from .ComponentClass import Component


class ComponentList:
    def __init__(self):
        self.components = []
        pass

    def add(self, comp: Component):
        self.components.append(comp)

    def count(self):
        return len(self.components)

    def count_ignored(self):
        count = 0
        for comp in self.components:
            if comp.is_ignored():
                count += 1
        return count

    def check_recipe_in_list(self, recipe_name, recipe_ver=''):
        try:
            for component in self.components:
                comp_origs = component.get_origins()
                for orig in comp_origs:
                    arr = orig.split('/')
                    if recipe_name == arr[0]:
                        if recipe_ver == '':
                            return True
                        elif recipe_ver in arr[1]:
                            return True
        except IndexError as e:
            logging.error(f"Error checking recipe {recipe_name} - {e}")

        return False

    def check_kernel_in_bom(self):
        for component in self.components:
            if component.name == 'Linux Kernel':
                return True
        return False
