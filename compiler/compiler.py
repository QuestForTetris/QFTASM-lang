from tree_builder.tree_builder import build_tree, GrammarTree
from variables import VariableStore

class GlobalLocalStoreHelper:
    def __init__(self, global_store: VariableStore, local_store: VariableStore):
        self._global_store = global_store
        self._local_store = local_store

    def get_var(self, variable: GrammarTree):
        assert variable.name == "generic_var"
        if variable in self._global_store:
            return self._global_store["variable"]
        elif variable in self._local_store:
            return self._local_store["variable"]
        assert "type_var" in variable
        type_var = variable["type_var"]
        is_global = type_var["global"]
        if is_global:
            return self._global_store.add_var(type_var)
        return self._local_store.add_var(type_var)


class FileInterpreter:
    def __init__(self, tree: GrammarTree):
        self.file_types = {
            "sub": SubroutineInterpreter,
            "struct": None
        }
        stmts = tree["stmts"]
        self.global_store = VariableStore()
        self.subs = []
        self.structs = []
        self.lists = {"sub": self.subs, "struct": self.structs}
        for stmt in stmts:
            self.lists[stmt["_block_name"]].append(self.file_types[stmt["_block_name"]](self.global_store, stmt))
        print("STRUCTS:", self.structs)
        print("SUBS:", self.subs)


class SubroutineInterpreter:
    def __init__(self, global_store: VariableStore, tree: GrammarTree):
        assert tree["_block_name"] == "sub"
        self.global_store = global_store
        self.local_store = VariableStore()
        self.name = tree["sub"]["name"]
        stmts = tree["sub"]["stmts"]["stmts"]
        self.stmts = []
        for stmt in stmts:
            self.stmts.append(StmtInterpreter(self.global_store, self.local_store, stmt))


class StmtInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.stmt_types = {
            "assign": AssignInterpreter,
            "mod_assign": ModAssignInterpreter
        }
        assert tree["_block_name"] == "stmt"
        tree = tree["simple_stmt"]
        self.stmt_type = tree["_block_name"]
        self.stmt = self.stmt_types[self.stmt_type](self._global_store, self._local_store, tree[self.stmt_type])


class AssignInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.var = self.get_var(tree["generic_var"])
        # print(tree)


class ModAssignInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        # print(tree)


if __name__ == "__main__":
    file_interpreter = FileInterpreter(build_tree("basic.txt"))