try:
    from high_level_compiler.variables import VariableStore, Variable, ScratchVariable, CustomVariable, _id_gen
except ImportError:
    from variables import VariableStore, Variable, ScratchVariable, CustomVariable, _id_gen
from tree_builder.tree_builder import build_tree, GrammarTree
import copy
import itertools

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class GlobalLocalStoreHelper:
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines):
        self._global_store = global_store
        self._local_store = local_store
        self._inlines = inlines

    def get_var(self, variable: GrammarTree):
        assert variable.name == "generic_var"
        if variable in self._global_store:
            return self._global_store[variable]
        elif variable in self._local_store:
            return self._local_store[variable]
        assert "type_var" in variable, "Variable `{}` has no type at definition".format(VariableStore.get_name(variable))
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
            return ArithmeticInterpreter(self._global_store, self._local_store, self._inlines, tree)
        elif tree["_block_name"] == "sub_call":
            return SubCallInterpreter(self._global_store, self._local_store, self._inlines, tree["sub_call"])
        elif tree["_block_name"] == "single":
            return SingleInterpreter(self._global_store, self._local_store, self._inlines, tree)
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

    def free_scratch(self, scratch):
        if isinstance(scratch, ScratchVariable):
            scratch.free()

    def collect_value(self, value):
        if isinstance(value, LiteralInterpreter):
            return [], value.val
        if isinstance(value, Variable):
            return [], value
        if isinstance(value, (ArithmeticInterpreter, SingleInterpreter)):
            return value.compile(), value.result
        if isinstance(value, SubCallInterpreter):
            return value.compile(), value.result
        raise SyntaxError("Unable to collect value from %s" % value.__class__.__name__)

    def inline_operator(self, instruction):
        operator, *vars = instruction
        rtn = []
        for inline in self._inlines:
            if inline.operator == operator:
                skip = False
                for var, cmp_var in zip(vars, inline.args+[inline.rtn_type]):
                    try:
                        var_type = var.type
                    except AttributeError:
                        var_type = type(var).__name__
                    try:
                        cmp_type = cmp_var.type
                    except AttributeError:
                        cmp_type = cmp_var
                    if var_type != cmp_type:
                        skip = True
                if skip:
                    continue
                #Now replace the variables and replace it
                *compiled, (rtn_stmt, result) = inline.compile()
                assert rtn_stmt == "return", "operator's must have a return as last statement"
                if inline.unsafe:
                    rtn.extend(self.replace_variables(compiled, inline.args, vars[:2]))
                    rtn.append(("assign", vars[2], result))
                else:
                    inline_vars = inline.args + [result]
                    rtn.extend(self.replace_variables(compiled, inline_vars, vars))
                break
        else:
            raise NotImplementedError("Operator `{}` not implemented for vars `{}` and result `{}`".format(operator,
                                                                                                           [var.type for var in vars[:-1]],
                                                                                                           vars[-1].type))

        return rtn

    @staticmethod
    def replace_variables(instructions, find, replace):
        zipped_args = dict(zip(map(id, find), replace))
        modded_operation = []
        for inst in instructions:
            modded_instruction = []
            if inst[0] == "call_sub":
                inst = list(inst)
                inst[2] = [zipped_args.get(id(operand), operand) for operand in inst[2]]
            for operand in inst:
                if operand in find:
                    modded_instruction.append(zipped_args[id(operand)])
                else:
                    modded_instruction.append(operand)
            modded_operation.append(tuple(modded_instruction))
        return modded_operation


class FileInterpreter:
    def __init__(self, tree: GrammarTree):
        self.file_types = {
            "sub": SubroutineInterpreter,
            "inline": InlineInterpreter,
            "struct": None,
            "newline": DummyInterpreter
        }
        stmts = tree["stmts"]
        self.global_store = VariableStore()
        self.subs = []
        self.structs = []
        self.inlines = []
        self.lists = {"sub": self.subs,
                      "struct": self.structs,
                      "inline": self.inlines,
                      "newline": []}
        for stmt in stmts:
            self.lists[stmt["_block_name"]].append(self.file_types[stmt["_block_name"]](self.global_store, self.inlines, stmt))
        assert "main" in [sub.name for sub in self.subs]

    def __repr__(self):
        #print("STRUCTS:", self.structs)
        rtn = "\n\n".join(str(sub) for sub in self.subs)
        return rtn

    def compile(self):
        rtn = []
        for sub in sorted(self.subs, key=lambda sub: sub.name == "main", reverse=True):
            rtn.extend(sub.compile())
        for sub in self.subs:
            sub.local_store.finalise()
            for var in sub.local_store.offsets:
                new = copy.deepcopy(var)
                new.name = sub.name + "_" + new.name
                new.sub = sub.name
                if new.name not in self.global_store:
                    self.global_store.add_named(new)
                rtn = GlobalLocalStoreHelper.replace_variables(rtn, [var], [new])
        for inline in self.inlines:
            for arg in inline.args:
                inline.local_store.remove(arg)
            #if "rtn" in inline.local_store:
            #    inline.local_store.remove("rtn")
            inline.local_store.finalise()
            for var in inline.local_store.offsets:
                new = copy.deepcopy(var)
                new.name = "op({}:{})".format(inline.operator, new.name)
                new.sub = "op({})".format(inline.operator)
                if new.name not in self.global_store:
                    self.global_store.add_named(new)
                rtn = GlobalLocalStoreHelper.replace_variables(rtn, [var], [new])
        self.global_store.add_subroutine(CustomVariable(name="result",
                                                        is_pointer=False,
                                                        is_global=True))
        self.global_store.add_subroutine(CustomVariable(name="stack",
                                                        is_pointer=True,
                                                        is_global=True))
        self.global_store.finalise()
        print(self.global_store)
        return rtn


class SubroutineInterpreter:
    def __init__(self, global_store: VariableStore, inlines, tree: GrammarTree):
        assert tree["_block_name"] == "sub"
        self.global_store = global_store
        self.local_store = VariableStore()
        self.inlines = inlines
        tree = tree["sub"]
        self.name = tree["name"]
        stmts = tree["stmts"]["stmts"]
        self.params = []
        if tree["_parameters"]:
            params = tree["typed_parameters"]
            self.add_params(params)
        self.rtn_type = "null"
        if tree["_rtn_type"]:
            self.rtn_type = tree["rtn_type"]
        self.stmts = []
        for stmt in stmts:
            self.stmts.append(StmtInterpreter(self.global_store, self.local_store, inlines, stmt))

    def __str__(self):
        pre = "sub %s"%self.name
        if self.params:
            params = "("+", ".join(repr(param) for param in self.params)+")"
            pre += params
        if self.rtn_type is not None:
            pre += " -> " + str(self.rtn_type)
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\n\t"+"\n\t".join(rtn)
        return pre+rtn

    def add_params(self, tree: GrammarTree):
        if "type_var" in tree:
            self.params.append(self.local_store.add_var(tree["type_var"]))
            if tree["_further_params"]:
                self.add_params(tree["typed_arg_list"])

    def compile(self):
        rtn = []
        rtn.append(("sub", "start", self.name))
        for stmt in self.stmts:
            rtn.extend(stmt.stmt.compile())
        rtn.append(("sub", "end", self.name))
        return rtn


class InlineInterpreter:
    def __init__(self, global_store: VariableStore, inlines, tree: GrammarTree):
        assert tree["_block_name"] == "inline"
        self.global_store = global_store
        self.local_store = VariableStore()
        tree = tree["inline"]
        if tree["_block_name"] == "two_op" or ("_block_name_2" in tree and tree["_block_name_2"] == "two_op"):
            self.operator = tree["operator"]["_block_name"]
            args = [tree["type_var"], tree["type_var_2"]]
        else:
            self.operator = tree["single_op"]["_block_name"]
            args = [tree["type_var"]]
        self.args = [self.local_store.add_var(var) for var in args]
        self.unsafe = tree["_unsafe"]
        stmts = tree["stmts"]["stmts"]
        self.rtn_type = tree["rtn_type"]
        self.stmts = []
        for stmt in stmts:
            self.stmts.append(StmtInterpreter(self.global_store, self.local_store, inlines, stmt))

    def __str__(self):
        return "operator({}, {}, {})".format(self.operator, self.args, self.rtn_type)

    def compile(self):
        rtn = []
        for stmt in self.stmts:
            rtn.extend(stmt.stmt.compile())
        return rtn


class StmtInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.stmt_types = {
            "assign": AssignInterpreter,
            "mod_assign": ModAssignInterpreter,
            "while_do": WhileInterpreter,
            "for": ForInterpreter,
            "if": IfInterpreter,
            "return": ReturnInterpreter,
            "sub_call": SubCallInterpreter
        }
        assert tree["_block_name"] == "stmt"
        tree = tree["simple_stmt"]
        self.stmt_type = tree["_block_name"]
        self.stmt = self.stmt_types[self.stmt_type](self._global_store, self._local_store, inlines, tree[self.stmt_type])

    def __str__(self):
        return str(self.stmt)


class AssignInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.var = self.get_var(tree["generic_var"])
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return str(self.var) + " = " + str(self.value)

    def compile(self):
        rtn, scratch = self.collect_value(self.value)
        if not rtn:
            rtn.append(("assign", self.var, self.value))
        rtn = self.replace_variables(rtn, [scratch], [self.var])
        self.free_scratch(scratch)
        return rtn


class ModAssignInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.var = self.get_var(tree["generic_var"])
        self.operator = tree["aug_assign"]["_block_name"]
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return " ".join([str(self.var), str(self.operator), str(self.value)])

    def compile(self):
        rtn, scratch = self.collect_value(self.value)
        rtn.extend(self.inline_operator([self.operator[:-1], self.var, scratch, self.var]))
        return rtn


class ForInterpreter(GlobalLocalStoreHelper):

    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.id = next(WhileInterpreter.id_gen)
        self.setup = AssignInterpreter(global_store, local_store, inlines, tree.get_stmt("setup"))
        self.condition = self.parse_generic_value(tree.get_stmt("condition"))
        self.final = ModAssignInterpreter(global_store, local_store, inlines, tree.get_stmt("final"))
        self.stmts = []
        for stmt in tree["stmts"]["stmts"]:
            self.stmts.append(StmtInterpreter(self._global_store, self._local_store, inlines, stmt))

    def __repr__(self):
        pre = "for (%s; %s; %s)\n"%(self.setup, self.condition, self.final)
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\t"+"\n\t".join(rtn)
        return pre+rtn

    def compile(self):
        rtn = self.setup.compile()
        extend, scratch = self.collect_value(self.condition)
        rtn.extend(extend)
        rtn.append(("while", "start", self.id, "for"))
        for stmt in self.stmts:
            rtn.extend(stmt.stmt.compile())
        rtn.extend(self.final.compile())
        rtn.extend(extend)
        rtn.append(("while", "end", self.id, scratch))
        self.free_scratch(scratch)
        return rtn


class IfInterpreter(GlobalLocalStoreHelper):
    id_gen = _id_gen()

    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.id = next(IfInterpreter.id_gen)
        self.condition = self.parse_generic_value(tree.get_stmt("condition"))
        self.stmts = []
        for stmt in tree["stmts"]["stmts"]:
            self.stmts.append(StmtInterpreter(self._global_store, self._local_store, inlines, stmt))

    def __repr__(self):
        pre = "if %s\n"%self.condition
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\t"+"\n\t".join(rtn)
        return pre+rtn

    def compile(self):
        rtn = []
        extend, scratch = self.collect_value(self.condition)
        rtn.extend(extend)
        rtn.extend(self.inline_operator(["not", scratch, scratch]))
        rtn.append(("if", "start", self.id, scratch))
        for stmt in self.stmts:
            rtn.extend(stmt.stmt.compile())
        rtn.append(("if", "end", self.id, None))
        self.free_scratch(scratch)
        return rtn


class WhileInterpreter(GlobalLocalStoreHelper):
    id_gen = _id_gen()

    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.id = next(WhileInterpreter.id_gen)
        self.condition = self.parse_generic_value(tree.get_stmt("condition"))
        self.stmts = []
        for stmt in tree["stmts"]["stmts"]:
            self.stmts.append(StmtInterpreter(self._global_store, self._local_store, inlines, stmt))

    def __repr__(self):
        pre = "while %s do\n"%self.condition
        rtn = "\n".join(str(stmt) for stmt in self.stmts).splitlines()
        rtn = "\t"+"\n\t".join(rtn)
        return pre+rtn

    def compile(self):
        rtn = []
        extend, scratch = self.collect_value(self.condition)
        rtn.extend(extend)
        rtn.append(("while", "start", self.id, "while"))
        for stmt in self.stmts:
            rtn.extend(stmt.stmt.compile())
        rtn.extend(extend)
        rtn.append(("while", "end", self.id, scratch))
        self.free_scratch(scratch)
        return rtn


class ReturnInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        assert tree.name == "return"
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return "return %s"%self.value

    def compile(self):
        rtn, scratch = self.collect_value(self.value)
        rtn.append(("return", scratch))
        self.free_scratch(scratch)
        return rtn


class LiteralInterpreter:
    def __init__(self, tree: GrammarTree):
        assert tree.name == "generic_literal"
        if tree["_block_name"] == "number":
            self.val = int(tree["value"])
        else:
            raise SyntaxError("Literal not a number")

    def __repr__(self):
        return repr(self.val)


class ArithmeticInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        assert tree["_block_name"] == "arith"
        self.value_1 = self.parse_var_literal(tree["var_literal"])
        self.operator = tree["operator"]["_block_name"]
        self.value_2 = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return " ".join([str(self.value_1), self.operator, str(self.value_2)])

    def compile(self):
        rtn, scratch_1 = self.collect_value(self.value_1)
        extend, scratch_2 = self.collect_value(self.value_2)
        if isinstance(scratch_1, ScratchVariable):
            self.result = scratch_1
            self.free_scratch(scratch_2)
        elif isinstance(scratch_2, ScratchVariable):
            self.result = scratch_2
            self.free_scratch(scratch_1)
        else:
            self.result = self._global_store.add_scratchpad()
            self.free_scratch(scratch_1)
            self.free_scratch(scratch_2)
        rtn.extend(extend)
        rtn.extend(self.inline_operator([self.operator, scratch_1, scratch_2, self.result]))
        return rtn


class SingleInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
        self.operator = tree["single_op"]["_block_name"]
        self.value = self.parse_generic_value(tree["generic_value"])

    def __repr__(self):
        return "%s %s" % (self.operator, self.value)

    def compile(self):
        rtn, scratch = self.collect_value(self.value)
        if isinstance(scratch, ScratchVariable):
            self.result = scratch
        else:
            self.result = self._global_store.add_scratchpad()
            self.free_scratch(scratch)
        rtn.extend(self.inline_operator([self.operator, scratch, self.result]))
        return rtn


class SubCallInterpreter(GlobalLocalStoreHelper):
    def __init__(self, global_store: VariableStore, local_store: VariableStore, inlines, tree: GrammarTree):
        super().__init__(global_store, local_store, inlines)
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
        if "generic_value" in tree:
            self.params.append(self.parse_generic_value(tree["generic_value"]))
            if tree["_further_params"]:
                self.add_params(tree["arg_list"])

    def compile(self):
        rtn = []
        scratches = []
        for param in self.params:
            extend, new_scratch = self.collect_value(param)
            rtn.extend(extend)
            scratches.append(new_scratch)
        self.result = self._global_store.add_scratchpad()
        rtn.append(("call_sub", self.sub_name, scratches, self.result))
        for scratch in scratches:
            self.free_scratch(scratch)
        return rtn


class DummyInterpreter:
    def __init__(self, global_store: VariableStore, inlines, tree: GrammarTree):
        pass

if __name__ == "__main__":
    file_interpreter = FileInterpreter(build_tree("basic.txt"))
    # print(file_interpreter)
    file_interpreter.compile()
