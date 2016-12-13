from typing import List
from high_level_compiler.variables import VariableStore, Variable


class FileInterpreter:
    def __init__(self, instruction_list, global_store: VariableStore):
        self.compilers = {
            "sub": self.sub_compiler,
            "call_sub": self.call_sub_compiler,
            "return": self.return_compiler
        }
        self.global_store = global_store
        self.current_sub = None
        self.current_result = None
        compiled = []
        for instruction in instruction_list:
            #print(instruction)
            assert instruction[0] in self.compilers
            compiled.extend(self.compilers[instruction[0]](*instruction[1:]))
        print("\n".join(compiled))

    def sub_compiler(self, status: str, name: str, result: Variable):
        self.current_sub = name
        self.current_result = result
        if status == "start":
            return ["#Start {}".format(name)]
        else:
            return ["#End {}".format(name)]

    def call_sub_compiler(self, sub_name: str, args: List[Variable], result: Variable):
        rtn = []
        variables = self.global_store.filter_subroutine(self.current_sub)
        for var in variables:
            rtn.extend(self.push_stack(self.parse_variable(var)))
        rtn.extend(self.push_stack("{}; +2"))
        rtn.append("#CALL {}".format(sub_name))
        for var in reversed(variables):
            rtn.extend(self.pop_stack(self.parse_result(var)))
        rtn.append("MLZ -1 {} {}".format(self.parse_variable(self.global_store["result"]),
                                         self.parse_result(result)))
        return rtn

    def return_compiler(self, result):
        rtn = ["MLZ -1 {} {}".format(self.parse_variable(result),
                                     self.parse_result(self.global_store["result"]))]
        rtn.extend(self.pop_stack("0"))
        return rtn

    def pop_stack(self, address: str):
        return ["POP {}".format(address)]

    def push_stack(self, address: str):
        return ["PUSH {}".format(address)]

    def parse_variable(self, variable: Variable) -> str:
        if not isinstance(variable, Variable):
            return str(variable)
        pointer = "AB"[variable.is_pointer]
        return pointer+str(variable.offset)

    def parse_result(self, variable: Variable) -> str:
        pointer = "A"*variable.is_pointer
        return pointer+str(variable.offset)


