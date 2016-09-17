from high_level_compiler.variables import VariableStore, Variable

class FileInterpreter:
    def __init__(self, instruction_list, global_store: VariableStore):
        self.opcodes = {
            "sub": self.sub_interpreter,
            "assign": self.assign_interpreter,
            "for": self.for_interpreter,
            "if": self.if_interpreter,
            "while": self.while_interpreter,
            "operator": self.operator_interpreter,
            "return": self.return_interpreter,
            "call_sub": self.call_sub_interpreter
        }
        self.global_store = global_store
        compiled = []
        for instruction in instruction_list:
            assert instruction[0] in self.opcodes
            compiled.extend(self.opcodes[instruction[0]](*instruction[1:]))
        print(compiled)

    def sub_interpreter(self, status, sub_id):
        self.current_sub = sub_id
        return []

    def assign_interpreter(self, variable, value):
        instruction = "MLZ -1 %s %s"
        var_offset = self.parse_variable(variable)
        if isinstance(value, Variable):
            val = self.parse_variable(value)
        else:
            val = str(value)
        return [instruction % (var_offset, val)]

    def for_interpreter(self, status, for_id, condition): return []
    def if_interpreter(self, status, if_id, condition): return []
    def while_interpreter(self, status, while_id, condition): return []
    def operator_interpreter(self, operator, val_1, val_2, result): return []
    def return_interpreter(self, value): return []
    def call_sub_interpreter(self, sub_name, args, result): return []

    def parse_variable(self, variable: Variable) -> str:
        if not variable.is_global:
            global_name = self.current_sub+"_"+variable.name
            variable = [var for var in self.global_store if var.name == global_name][0]
        pointer = "AB"[variable.is_pointer]
        return pointer+str(variable.offset)
