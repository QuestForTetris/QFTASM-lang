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
        self.current_sub = None
        compiled = []
        for instruction in instruction_list:
            assert instruction[0] in self.opcodes
            compiled.extend(self.opcodes[instruction[0]](*instruction[1:]))
        print("\n".join(compiled))

    def sub_interpreter(self, status, sub_id, result_var):
        self.current_sub = sub_id
        if status == "start":
            return ["#Start "+sub_id]
        else:
            return self.return_interpreter(result_var)

    def assign_interpreter(self, variable, value):
        return ["MLZ -1 %s %s" % (self.parse_variable(value),
                                  self.parse_result(variable))]

    def for_interpreter(self, status, for_id, condition): return []
    def if_interpreter(self, status, if_id, condition): return []
    def while_interpreter(self, status, while_id, condition): return []

    def operator_interpreter(self, operator, val_1, val_2, result):
        result = self.parse_result(result)
        if operator in "+-|&^":
            opcode = {
                "+": "ADD",
                "-": "SUB",
                "|": "OR",
                "&": "AND",
                "^": "XOR",
            }
            return [opcode[operator] + " %s %s %s" % (self.parse_variable(val_1),
                                                      self.parse_variable(val_2),
                                                      result)]
        if operator == "~":
            return self.parse_complement(self.parse_variable(val_1),
                                 result)
        if operator == "not":
            return self.parse_not(self.parse_variable(val_1),
                                 result)
        if operator == "<":
            return self.parse_lt(self.parse_variable(val_1),
                                 self.parse_variable(val_2),
                                 result)
        if operator == ">":
            return self.parse_gt(self.parse_variable(val_1),
                                 self.parse_variable(val_2),
                                 result)
        if operator == "<=":
            return self.parse_lt_eq(self.parse_variable(val_1),
                                    self.parse_variable(val_2),
                                    result)
        if operator == ">=":
            return self.parse_gt_eq(self.parse_variable(val_1),
                                    self.parse_variable(val_2),
                                    result)
        if operator == "%":
            return self.parse_modulo(self.parse_variable(val_1),
                                     self.parse_variable(val_2),
                                     result)
        else:
            assert False, operator + " isn't defined"

    def return_interpreter(self, value): return []
    def call_sub_interpreter(self, sub_name, args, result): return []

    def parse_variable(self, variable) -> str:
        if not isinstance(variable, Variable):
            return str(variable)
        if not variable.is_global:
            global_name = self.current_sub+"_"+variable.name
            variable = [var for var in self.global_store if var.name == global_name][0]
        pointer = "AB"[variable.is_pointer]
        return pointer+str(variable.offset)

    def parse_result(self, variable: Variable) -> str:
        if not variable.is_global:
            global_name = self.current_sub+"_"+variable.name
            variable = [var for var in self.global_store if var.name == global_name][0]
        pointer = "A"*variable.is_pointer
        return pointer+str(variable.offset)

    @staticmethod
    def parse_complement(val_1, result):
        return ["ANT -1 %s %s" % (val_1, result)]

    @staticmethod
    def parse_not(val_1, result):
        return ["ANT 1 %s %s" % (val_1, result)]

    def parse_lt(self, val_1, val_2, result):
        if result[0] in "ABC":
            nxt = {"A": "B", "B": "C"}
            pointer_result = nxt[result[0]]+result[1:]
        else:
            pointer_result = "A"+result
        return ["SUB %s %s %s" % (val_1, val_2, result),
                "ADD %s 1 %s" % (pointer_result, result),
                "MLZ %s 0 %s" % (pointer_result, result),
                "MNZ %s 1 %s" % (pointer_result, result),
                "XOR %s 1 %s" % (pointer_result, result)]

    def parse_gt(self, val_1, val_2, result):
        return self.parse_lt(val_2, val_1, result)

    def parse_lt_eq(self, val_1, val_2, result):
        pointer_result = self.inc_pointer(result)
        return ["SUB %s %s %s" % (val_1, val_2, result),
                "MLZ %s 0 %s" % (pointer_result, result),
                "MNZ %s 1 %s" % (pointer_result, result),
                "XOR %s 1 %s" % (pointer_result, result)]

    def parse_gt_eq(self, val_1, val_2, result):
        return self.parse_lt_eq(val_2, val_1, result)

    def parse_modulo(self, val_1, val_2, result):
        if val_2[0] not in "ABC":
            num = int(val_2)
            is_pow_2 = num and not num & (num - 1)
            if is_pow_2:
                return self.parse_and(val_1, str(num-1), result)
        pointer_result = self.inc_pointer(result)
        tmp = self.parse_variable(self.global_store["operation_tmp_1"])
        return ["MLZ -1 %s %s"%(val_1, result),
                "MLZ -1 %s 0; +4" ,
                "ADD %s 1 %s" % (pointer_result, tmp),
                "SUB %s %s %s" % (pointer_result, val_2, result),
                "ADD %s 1 %s" % (pointer_result, tmp),
                "SUB %s %s %s" % (val_2, pointer_result, tmp),
                "MLZ %s %%s 0; -3" % (tmp)]

    def inc_pointer(self, val):
        if val[0] in "ABC":
            nxt = {"A": "B", "B": "C"}
            return nxt[val[0]]+val[1:]
        else:
            return "A"+val
