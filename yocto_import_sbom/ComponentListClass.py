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
