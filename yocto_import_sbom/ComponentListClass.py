import logging

class ComponentList:
    components = []

    def __init__(self):
        pass

    def add(self, comp):
        self.components.append(comp)

    def count(self):
        return len(self.components)

    def count_ignored(self):
        count = 0
        for comp in self.components:
            if comp.is_ignored():
                count += 1
        return count

    def check_recipe_in_list(self, recipe_name, recipe_ver):
        try:
            for component in self.components:
                comp_origs = component.get_origins()
                for orig in comp_origs:
                    arr = orig.split('/')
                    if recipe_name == arr[1]:
                        return True
        except IndexError as e:
            logging.error(f"Unable to process origin - {e}")

        return False
