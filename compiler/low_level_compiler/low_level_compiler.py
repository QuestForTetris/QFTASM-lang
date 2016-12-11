from high_level_compiler.variables import VariableStore, Variable


class FileInterpreter:
    def __init__(self, instruction_list, global_store: VariableStore):
        #self.compilers = {
        #    "inline": self.inline_compiler
        #}
        self.global_store = global_store
        self.defined_operations = {}
        for inst, *data in instruction_list:
            print(inst, data)