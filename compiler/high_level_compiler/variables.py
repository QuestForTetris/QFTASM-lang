from tree_builder.tree_builder import GrammarTree


def _id_gen():
    i = 0
    while 1:
        i += 1
        yield i
id_gen = _id_gen()


class VariableStore:
    def __init__(self):
        self._vars = {}
        self._scratchpads = []

    def __contains__(self, item):
        try:
            return VariableStore.get_name(item) in self._vars
        except TypeError:
            return item in self._vars

    def __getitem__(self, item):
        try:
            return self._vars[VariableStore.get_name(item)]
        except TypeError:
            try:
                return self._vars[item]
            except KeyError:
                for var in self._scratchpads:
                    if var.name == item:
                        return var

    def __repr__(self):
        try:
            return repr([(0,0)]+[(var.offset, var)for var in self.offsets])
            #return repr(list(enumerate([0]+self.offsets)))
        except AttributeError:
            return repr(list(enumerate([0]+self._vars)))

    def __iter__(self):
        return iter(self.offsets)

    @staticmethod
    def get_name(var: GrammarTree):
        return var[var["_block_name"]]["name"]

    def remove(self, var):
        try:
            del self._vars[var.name]
        except AttributeError:
            del self._vars[var]

    def filter_subroutine(self, sub_name):
        rtn = []
        for variable in self._vars.values():
            if variable.sub == sub_name:
                rtn.append(variable)
        for scratchpad in self._scratchpads:
            if scratchpad.name in ["<stack>", "<result>"]:
                continue
            rtn.append(scratchpad)
        return rtn

    def get_ordered_params(self, sub_name):
        var_dict = {}
        for variable in self._vars.values():
            if variable.sub == sub_name and variable.param_var is not None:
                var_dict[variable.param_var] = variable
        rtn = []
        for i in sorted(var_dict.keys()):
            assert len(rtn) == i, "Want to convert a dict of indices to a list with corresponding values here"
            rtn.append(var_dict[i])
        return rtn

    def add_var(self, var: GrammarTree, param_var=None):
        rtn = Variable(var, param_var=param_var)
        self._vars[var["name"]] = rtn
        return rtn

    def add_scratchpad(self, type="int"):
        for scratchpad in self._scratchpads:
            if scratchpad.being_used is False:
                scratchpad.being_used = True
                return scratchpad
        rtn = ScratchVariable(type)
        self._scratchpads.append(rtn)
        return rtn

    def add_subroutine(self, variable: "CustomVariable"):
        self._scratchpads.append(variable)

    def add_named(self, variable: "Variable"):
        self._vars[variable.name] = variable

    def assert_scratch_free(self):
        for scratchpad in self._scratchpads:
            if isinstance(scratchpad, ScratchVariable):
                assert scratchpad.being_used is False

    def finalise(self):
        self.assert_scratch_free()
        self.offsets = []
        for var in self._vars:
            self.offsets.append(self._vars[var])
        for var in self._scratchpads:
            self.offsets.append(var)
        cur_offset = 1
        for variable in self.offsets:
            variable.set_offset(cur_offset)
            cur_offset += variable.size
        return self.offsets


class Variable:
    def __init__(self, var: GrammarTree, param_var):
        self.type = var["type"]
        self.name = var["name"]
        self.sub = None
        self.is_pointer = var["_block_name"] == "pointer_type"
        self.is_global = var["_global"]
        self.is_array = var["_block_name"] == "array_type"
        self.size = 1
        if self.is_array:
            assert isinstance(var["size"][1], int), "Array size cannot be variable"
            self.size = var["size"][1]
        self.offset = None
        self.param_var = param_var

    def __str__(self):
        return self.name

    def __repr__(self):
        rtn = []
        if self.is_global:
            rtn.append("global ")
        if self.is_pointer:
            rtn.append("*")
        rtn.append(self.type+" ")
        rtn.append(self.name)
        return "".join(rtn)

    def set_offset(self, offset):
        self.offset = offset


class ScratchVariable(Variable):
    def __init__(self, type):
        self.type = type
        self.name = "scratch_%s"%next(id_gen)
        self.is_pointer = False
        self.is_global = True
        self.is_array = False
        self.size = 1
        self.being_used = True

    def free(self):
        assert self.being_used, "Attempted to free an already freed scratchpad"
        self.being_used = False


class CustomVariable(Variable):
    def __init__(self,
                 name: str,
                 type: str = "int",
                 is_pointer: bool = False,
                 is_global: bool = False,
                 is_array: bool = False,
                 size: int = 1):
        self.type = type
        self.name = name
        self.is_pointer = is_pointer
        self.is_global = is_global
        self.is_array = is_array
        self.size = size

