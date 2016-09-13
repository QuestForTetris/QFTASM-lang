from tree_builder.tree_builder import build_tree, GrammarTree
from variables import VariableStore


class GlobalLocalStoreHelper:
    def __init__(self, global_store: VariableStore, local_store: VariableStore):
        self._global_store = global_store
        self._local_store = local_store

    def get_var(self, variable: GrammarTree):
        assert variable.name == "generic_var"
        if variable in self._global_store:
            return self._global_store[variable]
        elif variable in self._local_store:
            return self._local_store[variable]
        assert "type_var" in variable, "Variable, %s, has no type at definition" % VariableStore.get_name(variable)
        type_var = variable["type_var"]
        is_global = type_var["_global"]
        if is_global:
            return self._global_store.add_var(type_var)
        return self._local_store.add_var(type_var)

    def parse_generic_value(self, tree):
        assert tree.name == "generic_value"
        if tree["_block_name"] == "var_literal":
            return self.parse_var_literal(tree["var_literal"])
        elif tree["_block_name"] == "arith":
            return ArithmeticInterpreter(self._global_store, self._local_store, tree)
        elif tree["_block_name"] == "sub_call":
            return SubCallInterpreter(self._global_store, self._local_store, tree["sub_call"])
        elif tree["_block_name"] == "not":
            return NotInterpreter(self._global_store, self._local_store, tree)
        assert False, "Failed to assign generic_value %s"%tree["_block_name"]

    def parse_var_literal(self, tree: GrammarTree):
        assert tree.name == "var_literal"
        if tree["_block_name"] == "brackets":
            return self.parse_generic_value(tree["generic_value"])
        if tree["_block_name"] == "literal":
            return LiteralInterpreter(tree["generic_literal"])
        if tree["_block_name"] == "var":
            return self.get_var(tree["generic_var"])
        assert False, "Failed to assign var_literal"


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
        for sub in self.subs:
            print(sub)
            print()


class SubroutineInterpreter:
    def __init__(self, global_store: VariableStore, tree: GrammarTree):
        assert tree["_block_name"] == "sub"
        self.global_store = global_store
        self.local_store = VariableStore()
        tree = tree["sub"]
        self.name = tree["name"]
        stmts = tree["stmts"]["stmts"]
        self.params = []
        if tree["_parameters"]:
            params = tree["typed_parameters"]
            self.add_params(params)
        self.rtn_type = None
        if tree["_rtn_type"]:
            self.rtn_type = tree["rtn_type"]
        self.stmts = []
        for stmt in stmts:
            self.stmts.append(StmtInterpreter(self.global_store, self.local_store, stmt))

    def __str__(self):
        pre = "struct %s"%self.name
        if self.params:
            params = "("+", ".join(repr(param) for param in self.params)+")"
            pre += params
        if self.rtn_type is not None:
            pre += " -> " + str(self.rtn_type)
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\n\t"+"\n\t".join(rtn)
        return pre+rtn

    def add_params(self, tree: GrammarTree):
        self.params.append(self.local_store.add_var(tree["type_var"]))
        if tree["_further_params"]:
            self.add_params(tree["typed_arg_list"])


class StmtInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.stmt_types = {
            "assign": AssignInterpreter,
            "mod_assign": ModAssignInterpreter,
            "while_do": WhileInterpreter,
            "for": ForInterpreter,
            "if": IfInterpreter,
            "return": ReturnInterpreter
        }
        assert tree["_block_name"] == "stmt"
        tree = tree["simple_stmt"]
        self.stmt_type = tree["_block_name"]
        self.stmt = self.stmt_types[self.stmt_type](self._global_store, self._local_store, tree[self.stmt_type])

    def __str__(self):
        return str(self.stmt)


class AssignInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.var = self.get_var(tree["generic_var"])
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return str(self.var) + " = " + str(self.value)


class ModAssignInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.var = self.get_var(tree["generic_var"])
        self.operator = tree["aug_assign"]["_block_name"]
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return " ".join([str(self.var), str(self.operator), str(self.value)])


class ForInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.setup = AssignInterpreter(global_store, local_store, tree.get_stmt("setup"))
        self.condition = self.parse_generic_value(tree.get_stmt("condition"))
        self.final = ModAssignInterpreter(global_store, local_store, tree.get_stmt("final"))
        self.stmts = []
        for stmt in tree["stmts"]["stmts"]:
            self.stmts.append(StmtInterpreter(self._global_store, self._local_store, stmt))

    def __repr__(self):
        pre = "for (%s; %s; %s)\n"%(self.setup, self.condition, self.final)
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\t"+"\n\t".join(rtn)
        return pre+rtn


class IfInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.condition = self.parse_generic_value(tree.get_stmt("condition"))
        self.stmts = []
        for stmt in tree["stmts"]["stmts"]:
            self.stmts.append(StmtInterpreter(self._global_store, self._local_store, stmt))

    def __repr__(self):
        pre = "if %s\n"%self.condition
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\t"+"\n\t".join(rtn)
        return pre+rtn


class WhileInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        self.condition = self.parse_generic_value(tree.get_stmt("condition"))
        self.stmts = []
        for stmt in tree["stmts"]["stmts"]:
            self.stmts.append(StmtInterpreter(self._global_store, self._local_store, stmt))

    def __repr__(self):
        pre = "while %s do\n"%self.condition
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\t"+"\n\t".join(rtn)
        return pre+rtn


class ReturnInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        assert tree.name == "return"
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return "return %s"%self.value


class LiteralInterpreter:
    def __init__(self, tree: GrammarTree):
        assert tree.name == "generic_literal"
        if tree["_block_name"] == "number":
            self.val = int(tree["value"])

    def __repr__(self):
        return repr(self.val)


class ArithmeticInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        assert tree["_block_name"] == "arith"
        self.value_1 = self.parse_var_literal(tree["var_literal"])
        self.operator = tree["operator"]["_block_name"]
        self.value_2 = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return " ".join([str(self.value_1), self.operator, str(self.value_2)])


class NotInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        assert tree["_block_name"] == "not"
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return "not %s"%self.value


class SubCallInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, tree: GrammarTree):
        super().__init__(global_store, local_store)
        assert tree.name == "sub_call"
        self.sub_name = tree["sub_name"]
        self.params = []
        self.add_params(tree["parameters"])

    def __repr__(self):
        pre = str(self.sub_name)
        if self.params:
            params = "("+", ".join(str(param) for param in self.params)+")"
            pre += params
        return pre


    def add_params(self, tree: GrammarTree):
        self.params.append(self.parse_generic_value(tree["generic_value"]))
        if tree["_further_params"]:
            self.add_params(tree["arg_list"])


if __name__ == "__main__":
    file_interpreter = FileInterpreter(build_tree("basic.txt"))