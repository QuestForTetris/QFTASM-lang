from high_level_compiler.variables import VariableStore, Variable

class FileInterpreter:
    def __init__(self, instruction_list, global_store: VariableStore):
        self.opcodes = {
            "sub": self.sub_interpreter,
            "assign": self.assign_interpreter,
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
        compiled = self.add_jumps(compiled)
        print("\n".join(compiled))

    def add_jumps(self, compiled):
        for i, instruction in enumerate(compiled):
            instruction, semi, jump = instruction.partition(";")
            if semi:
                jump = jump.strip()
                if jump[0] not in "+-":
                    jump_offset = compiled.index("#"+jump)
                    jump_offset -= len([inst for inst in compiled[:jump_offset] if inst.startswith("#")])
                    jump_offset += jump.startswith("Start")
                    compiled[i] = instruction % jump_offset
        compiled = [inst for inst in compiled if not inst.startswith("#")]
        for i, instruction in enumerate(compiled):
            instruction, semi, jump = instruction.partition(";")
            if semi:
                compiled[i] = instruction % eval(str(i)+jump)
            compiled[i] = str(i+1)+". "+compiled[i]
        return compiled

    def sub_interpreter(self, status, sub_id, result_var):
        self.current_sub = sub_id
        self.result_var = result_var
        if status == "start":
            return ["#Start "+sub_id]
        else:
            rtn = self.return_interpreter(self.result_var)
            rtn.append("#End "+sub_id)
            return rtn

    def assign_interpreter(self, variable, value):
        return ["MLZ -1 %s %s" % (self.parse_variable(value),
                                  self.parse_result(variable))]

    def if_interpreter(self, status, if_id, condition):
        if status == "end":
            return ["#End if_%s" % if_id]
        condition = self.parse_variable(condition)
        rtn = ["#Start if_%s" % if_id,
               "MNZ %s %%s 0; End if_%s" % (condition, if_id),
               "MLZ 0 0 0"]
        return rtn

    def while_interpreter(self, status, while_id, condition):
        if status == "end":
            condition = self.parse_variable(condition)
            rtn = ["#End while_%s" % while_id,
                   "MNZ %s %%s 0; Start while_%s" % (condition, while_id),
                   "MLZ 0 0 0"]
            return rtn
        rtn = ["MLZ -1 %%s 0; End while_%s" % while_id,
               "MLZ 0 0 0",
               "#Start while_%s" % while_id]
        return rtn

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

    def return_interpreter(self, value):
        rtn = []
        if value is not self.result_var:
            rtn = ["MLZ -1 %s %s" % (self.parse_variable(value),
                                     self.parse_result(self.result_var))]
        rtn.append("#RETURN %s"%value)
        return rtn

    def call_sub_interpreter(self, sub_name, args, result): return ["#CALL SUB %s"%sub_name]

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
        tmp = self.parse_result(self.global_store["operation_tmp_1"])
        pointer_tmp = self.inc_pointer(tmp)
        return ["MLZ -1 %s %s" % (val_1, result),
                "MLZ -1 %s 0; + 2",
                "ADD %s 1 %s" % (pointer_result, tmp),
                "SUB %s %s %s" % (pointer_result, val_2, result),
                "SUB %s %s %s" % (val_2, pointer_result, tmp),
                "SUB %s 1 %s" % (pointer_tmp, tmp),
                "MLZ %s %%s 0; - 4" % (pointer_tmp),
                "MLZ 0 0 0"]

    def inc_pointer(self, val):
        if val[0] in "ABC":
            nxt = {"A": "B", "B": "C"}
            return nxt[val[0]]+val[1:]
        else:
            return "A"+val
