import unittest
import sys
sys.path.insert(1,'..')

from compiler import Compiler
from interpreter.interpreter import Interpreter

class TestCompiler(unittest.TestCase):
    def setUp(self):
        super(TestCompiler, self).setUp()

    def run_prg(self, filename):
        self.file_interpreter = Compiler(filename).low_level_file_interpreter
        compiled = "\n".join(self.file_interpreter.compiled)
        #print(compiled)
        interpreter = Interpreter("")
        interpreter.__init__(compiled)
        interpreter.run()
        self.ram = interpreter.ram

    def get_ram(self, variables):
        rtn = []
        for variable in variables:
            var = self.file_interpreter.global_store["main_"+variable]
            extra = None
            if var.is_array:
                extra = self.ram[slice(var.offset, var.offset+var.size)]
            else:
                extra = self.ram[var.offset]
            rtn.append(extra)
        return rtn
        #return [self.ram[self.file_interpreter.global_store["main_"+variable].offset] for variable in variables]

    def test_assign(self):
        self.run_prg("tests/test_assign.txt")
        self.assertEqual(self.get_ram("a"), [7])

    def test_assign_multi(self):
        self.run_prg("tests/test_assign_multi.txt")
        self.assertEqual(self.get_ram("abc"), [7,3,1337])

    def test_if(self):
        self.run_prg("tests/test_if.txt")
        self.assertEqual(self.get_ram("a"), [5])

    def test_if_multi(self):
        self.run_prg("tests/test_if_multi.txt")
        self.assertEqual(self.get_ram("ab"), [5,3])

    def test_stdint(self):
        self.run_prg("tests/test_stdint.txt")
        self.assertEqual(self.get_ram("abcdefghij"), [31,65162,32204,1,0,0,1,65504,1,0])

    def test_stdint_complex(self):
        self.run_prg("tests/test_stdint_complex.txt")
        self.assertEqual(self.get_ram("ab"), [5472,151])

    def test_factorial(self):
        self.run_prg("tests/test_factorial.txt")
        self.assertEqual(self.get_ram("a"), [120])

    def test_prime(self):
        self.run_prg("tests/test_prime.txt")
        self.assertEqual(self.get_ram(["cur_prime"]), [73])

    def test_recursion(self):
        self.run_prg("tests/test_recursion.txt")
        self.assertEqual(self.get_ram("a"), [120])

    def test_complex(self):
        self.run_prg("tests/test_complex.txt")
        self.assertEqual(self.get_ram("caefb"), [2,[6,3,1213],1213,5,[6,3,9]])

if __name__ == '__main__':
    unittest.main()
