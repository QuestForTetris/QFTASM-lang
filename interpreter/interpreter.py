import sys

class Interpreter:
    def __init__(self, inp: str):
        self.opcodes = {"MNZ": self.mov_not_zero,
                        "MLZ": self.mov_less_zero,
                        "ADD": self.add,
                        "SUB": self.sub,
                        "AND": self._and,
                        "OR": self._or,
                        "XOR": self.xor,
                        "ANT": self.and_not,
                        "SL": self.shift_left,
                        "SRL": self.shift_right_logic,
                        "SRA": self.shift_right_arith,
                        }
        self.ram = RAM()
        self.tokens = [self.tokenise(line) for line in inp.splitlines()]

    def tokenise(self, line):
        # Remove comments
        code, semicolon, comment = line.partition(";")
        # Lines must have a semicolon
        if not semicolon:
            raise SyntaxError("%s: No semicolon ending"%(line))
        line_no, opcode_id, *operands = code.split()
        line_no = int(line_no.rstrip("."))
        opcode = self.opcodes[opcode_id]
        operands = list(map(self.parse_operand, operands))
        return opcode, operands

    def parse_operand(self, operand: str) -> "RamLocation":
        return RamLocation(self.ram, operand)

    def mov_not_zero(self, test: int, value: int, dest: int):
        if test != 0:
            self.ram[dest] = value

    def mov_less_zero(self, test: int, value: int, dest: int):
        if not self.ram.is_non_neg(test):
            self.ram[dest] = value

    def add(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 + val2

    def sub(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 - val2

    def _and(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 & val2

    def _or(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 | val2

    def xor(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 ^ val2

    def and_not(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 & ~val2

    def shift_left(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 << val2

    def shift_right_logic(self, val1: int, val2: int, dest: int):
        self.ram[dest] = self.ram.unfix_value(val1) >> val2

    def shift_right_arith(self, val1: int, val2: int, dest: int):
        self.ram[dest] = val1 >> val2

    def run(self):
        len_tokens = len(self.tokens)
        # the operation in queue

        opcode = None

        while 1:
            if self.ram._contents[0] >= len_tokens:
                qopcode = None
            else:
                qopcode, qoperands = self.tokens[self.ram._contents[0]]

            # starting condition
            if opcode is not None:
                opcode(*operands)
            print(self.ram)

            # ending condition
            if qopcode is None:
                break

            # read into memory
            qoperands = list(map(RamLocation.__call__, qoperands))
            opcode, operands = qopcode, qoperands
            self.ram._contents[0]+=1

        print("Done!")


class RAM():
    address_size = 16
    negative_bit = 1 << (address_size - 1)
    max_value = (1 << address_size) - 1

    def __init__(self):
        self._contents = {0:0}

    def __repr__(self):
        return repr(self._contents)

    def __str__(self):
        rtn = ["RAMDUMP"]
        for key in sorted(self._contents.keys()):
            rtn.append("%d: %d"%(key, self._contents[key]))
        return "\n".join(rtn)

    def __getitem__(self, item):
        try:
            return self._contents[item]
        except KeyError:
            return 0

    def __setitem__(self, key, value):
        self._contents[key] = self.fix_value(value)
        if key == 1:
            print("Set 1 to", self._contents[key])
            if self._contents[key] == 211:
                exit()
        if value == 0:
            del self._contents[key]

    def fix_value(self, value):
        if value < 0:
            value = self.max_value+value+1
        return value & self.max_value

    def unfix_value(self, value):
        if not self.is_non_neg(value):
            value -= self.max_value + 1
        return value

    def is_non_neg(self, value):
        return value & self.negative_bit == 0


class RamLocation():
    def __init__(self, ram: RAM, address: str):
        self.ram = ram
        self.layers = "ABC".find(address[0]) + 1
        self.address = self.ram.fix_value(int(address[self.layers > 0:]))
        self.range_layers = list(range(self.layers))

    def __call__(self):
        if self.layers == 0:
            return self.address
        value = self.address
        for i in self.range_layers:
            value = self.ram[value]
        return value

if __name__ == "__main__":
    with open(sys.argv[1]) as assembly_file:
        interpreter = Interpreter(assembly_file.read())
        interpreter.run()
