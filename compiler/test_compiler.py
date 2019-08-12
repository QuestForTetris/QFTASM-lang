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
        #compiled = "0. MLZ 0 0 0;\n"+"\n".join(self.file_interpreter.compiled)
        compiled = "\n".join(self.file_interpreter.compiled)
        interpreter = Interpreter("")
        interpreter.__init__(compiled)
        interpreter.run()
        self.ram = interpreter.ram

    def get_ram(self, variables):
        return [self.ram[self.file_interpreter.global_store[variable].offset] for variable in variables]

    def test_assign(self):
        self.run_prg("tests/test_assign.txt")
        self.assertEqual(self.get_ram(["main_a"]), [7])

    def test_assign_multi(self):
        self.run_prg("tests/test_assign_multi.txt")
        self.assertEqual(self.get_ram(["main_a","main_b","main_c"]), [7,3,1337])

    def test_if(self):
        self.run_prg("tests/test_if.txt")
        self.assertEqual(self.get_ram(["main_a"]), [5])

    def test_if_multi(self):
        self.run_prg("tests/test_if_multi.txt")
        self.assertEqual(self.get_ram(["main_a","main_b"]), [5,3])

if __name__ == '__main__':
    unittest.main()
