from tree_builder.tree_builder import GrammarTree

class VariableStore:
    def __init__(self):
        self._vars = {}

    def __contains__(self, item):
        return item in self._vars

    def add_var(self, var: GrammarTree):
        print(var)
