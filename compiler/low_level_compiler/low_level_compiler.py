from typing import List, Optional

from high_level_compiler.variables import VariableStore, Variable, id_gen
from high_level_compiler.high_level_compiler import ArrayInterpreter


class FileInterpreter:
    opcodes = ["__MNZ__", "__MLZ__", "__ADD__", "__SUB__", "__AND__",
               "__OR__", "__XOR__", "__ANT__", "__SL__", "__SRL__", "__SRA__"]

    def __init__(self, instruction_list, global_store: VariableStore):
        """
        Compile a list of high level instructions into QFTASM code

        :param instruction_list:
        :param global_store:
        """
        self.compilers = {
            "sub": self.sub_compiler,
            "call_sub": self.call_sub_compiler,
            "return": self.return_compiler,
            "assign": self.assign_interpreter,
            "if": self.if_interpreter,
            "while": self.while_interpreter,
        }
        self.global_store = global_store
        self.current_sub = None
        # Set the current value of the stack to the end of the variables
        # This happens to be just after the stack word as it's inserted at the end
        compiled = ["MLZ -1 {} {}".format(self.global_store["<stack>"].offset+1,
                                          self.parse_result(self.global_store["<stack>"]))]
        for instruction in instruction_list:
            #print(instruction)
            # Check the output of the high level compiler can be compiled
            assert instruction[0] in self.compilers, "Cannot compile high level instruction {}".format(instruction)
            # Add the bytecode to the list
            compiled.extend(self.compilers[instruction[0]](*instruction[1:]))
        #print("\n".join(compiled))

        # Strip out the jump label information
        compiled = self.add_jumps(compiled)
        # Make the compiler work with the new version of QFTASM
        #self.compiled = ["0. MNZ 0 0 0;"]+compiled
        self.compiled = compiled
        # Output the complete QFTASM code
        #print("\n".join(compiled))

    def sub_compiler(self, status: str, name: str):
        """
        Add the jump information to the start and end of a subroutine

        :param status:
        :param name:
        :return:
        """
        self.current_sub = name
        if status == "start":
            return ["#Start {}".format(name)]
        elif name == "main":
            # Special case the main subroutine to jump to the end of the script at end
            return ["#End {}".format(name),
                    "MLZ -1 -2 0",
                    "MLZ 0 0 0"]
        else:
            return ["#End {}".format(name)]

    def call_sub_compiler(self, sub_name: str, args: List[Variable], result: Variable):
        """
        Compile all function calls in the high level code

        :param sub_name:
        :param args:
        :param result:
        :return:
        """
        if sub_name in FileInterpreter.opcodes:
            # If we're calling assembly code directly, return a single opcode
            return ["{} {} {} {}".format(sub_name[2:-2], *map(self.parse_variable, args), self.parse_result(result))]
        # Otherwise we're calling a subroutine defined in code
        rtn = []
        # Get all local variables associated with the current subroutine
        variables = self.global_store.filter_subroutine(self.current_sub)
        for var in variables:
            # Push each local to the stack
            rtn.extend(self.push_stack(self.parse_variable(var)))
        # Put all the arguments to the called subroutine into their place in RAM
        for param, arg in zip(args, self.global_store.get_ordered_params(sub_name)):
            #print(param, arg.offset)
            rtn.append("MLZ -1 {} {}".format(self.parse_variable(param),
                                             self.parse_result(arg)))
        uuid = next(id_gen)
        # Create a jump target for returning from the subroutine and push it to the stack
        rtn.extend(self.push_stack("{}", "EndCall {}_{}".format(sub_name, uuid)))
        # Jump to the called subroutine
        rtn.append("MLZ -1 {} 0; Start {}".format("{}", sub_name))
        rtn.append("MNZ 0 0 0")
        # Write the label to jump back to
        rtn.append("#EndCall {}_{}".format(sub_name, uuid))
        # Pop all the variables from the stack into their respective locations
        for var in reversed(variables):
            rtn.extend(self.pop_stack(self.parse_result(var)))
        # Copy the result from the result register to the destination
        rtn.append("MLZ -1 {} {}".format(self.parse_variable(self.global_store["<result>"]),
                                         self.parse_result(result)))
        return rtn

    def return_compiler(self, result):
        """
        Compile a return jump from a subroutine

        :param result:
        :return:
        """
        # Copy the return result to the result register
        rtn = ["MLZ -1 {} {}".format(self.parse_variable(result),
                                     self.parse_result(self.global_store["<result>"]))]
        # Pop the jump target from the stack and put it in the PC
        rtn.extend(self.pop_stack("0"))
        rtn.append("MNZ 0 0 0")
        return rtn

    def assign_interpreter(self, variable, value):
        """
        Assign a variable a value

        :param variable:
        :param value:
        :return:
        """
        if variable.is_array:
            return ["MLZ -1 {} {}".format(val, res) for val, res in zip(self.parse_variable(value), self.parse_result(variable))]
        return ["MLZ -1 {} {}".format(self.parse_variable(value),
                                      self.parse_result(variable))]

    def if_interpreter(self, status, if_id, condition):
        """
        Add the jump information to the start and end of an if statement

        :param status:
        :param if_id:
        :param condition:
        :return:
        """
        if status == "end":
            return ["#End if_{}".format(if_id)]
        condition = self.parse_variable(condition)
        rtn = ["#Start if_{}".format(if_id),
               "MNZ {} {} 0; End if_{}".format(condition, "{}", if_id),
               "MLZ 0 0 0"]
        return rtn

    def while_interpreter(self, status, while_id, condition):
        """
        Add the jump information to the start and end of a while loop
        Also check the condition for continuing

        :param status:
        :param while_id:
        :param condition:
        :return:
        """
        if status == "end":
            condition = self.parse_variable(condition)
            rtn = ["#End while_{}".format(while_id),
                   "MNZ {} {} 0; Start while_{}".format(condition, "{}", while_id),
                   "MLZ 0 0 0"]
            return rtn
        # Jump to the end first so the condition gets checked
        rtn = ["MLZ -1 {} 0; End while_{}".format("{}", while_id),
               "MLZ 0 0 0",
               "#Start while_{}".format(while_id)]
        return rtn

    def pop_stack(self, address: str):
        """
        Push a value onto the stack

        :param address:
        :return:
        """
        return ["SUB {} 1 {}".format(self.parse_variable(self.global_store["<stack>"]),
                                     self.parse_result(self.global_store["<stack>"])),
                "MLZ -1 {} {}".format("B"+str(self.global_store["<stack>"].offset),
                                      address)
                ]

    def push_stack(self, address: str, label: Optional[str] = ""):
        """
        Pop a value from the stack
        Optional label to push a jump target to the stack

        :param address:
        :param label:
        :return:
        """
        if label:
            label = "; " + label
        return ["MLZ -1 {} {}{}".format(address,
                                        self.parse_variable(self.global_store["<stack>"]),
                                        label),
                "ADD {} 1 {}".format(self.parse_variable(self.global_store["<stack>"]),
                                     self.parse_result(self.global_store["<stack>"]))
                ]

    def add_jumps(self, compiled):
        """
        Turn jumps with labels into absolute addresses

        :param compiled:
        :return:
        """
        for i, instruction in enumerate(compiled):
            instruction, semi, jump = instruction.partition(";")
            # If the instruction has a label attached to it
            if semi:
                jump = jump.strip()
                assert jump[0] not in "+-"
                # Find the target to the label
                jump_offset = compiled.index("#"+jump)
                jump_offset -= len([inst for inst in compiled[:jump_offset] if inst.startswith("#")])
                # Replace the instruction with one with the jump target embedded
                compiled[i] = instruction.format(jump_offset-1)
        # compiled = [inst for inst in compiled if not inst.startswith("#")]
        # Add labels back
        temp = []
        for inst in compiled:
            if inst.startswith("#"):
                temp[len(temp)-1] += [inst[1:]]
            else:
                temp += [[inst]]
        compiled = temp
        # Add line numbers
        for i, instruction in enumerate(compiled):
            if len(instruction) == 1:
                compiled[i] = "{}. {};".format(i, compiled[i][0])
            else:
                compiled[i] = "{}. {}; {}".format(i, compiled[i][0], compiled[i][1])
        return compiled

    def parse_variable(self, variable: Variable) -> str:
        """
        Parse a variable that's going to be used as an input to an opcode

        :param variable:
        :return:
        """
        if not isinstance(variable, Variable):
            if isinstance(variable, ArrayInterpreter):
                return [self.parse_variable(var)for var in variable.val]
            return str(variable)
        if variable.is_array:
            return ["A"+str(i+variable.offset)for i in range(variable.size)]
        pointer = "AB"[variable.is_pointer]
        return pointer+str(variable.offset)

    def parse_result(self, variable: Variable) -> str:
        """
        Parse a variable that's going to be used as a result of an opcode

        :param variable:
        :return:
        """
        if variable.is_array:
            return [str(i+variable.offset)for i in range(variable.size)]
        pointer = "A"*variable.is_pointer
        return pointer+str(variable.offset)


