import unittest
import sys
sys.path.insert(0, '..')
from interpreter.interpreter import Interpreter

class TestInterpreter(unittest.TestCase):
    def setUp(self):
        super(TestInterpreter, self).setUp()
        self.interpreter = Interpreter("")

    def run_prg(self, inp):
        self.interpreter.__init__(inp)
        self.interpreter.run()
        self.ram = self.interpreter.ram

    def test_semicolon(self):
        with self.assertRaises(SyntaxError):
            self.run_prg("0. MLZ -1 -1 -1")

    def test_mov_not_zero(self):
        self.run_prg("""0. MNZ 0 3 1;
                        1. MNZ 1 4 2;
                        2. MNZ -1 5 3;""")
        self.assertEqual(self.ram[1:5], [0,4,5,0])

    def test_mov_less_zero(self):
        self.run_prg("""0. MLZ 1 3 1;
                        1. MLZ 0 4 2;
                        2. MLZ -1 5 3;""")
        self.assertEqual(self.ram[1:5], [0,0,5,0])

    def test_add(self):
        self.run_prg("""0. ADD 1 3 1;
                        1. ADD 1 -3 3;
                        2. ADD -1 -3 4;""")
        self.assertEqual(self.ram[1:5], [4, 0, 65534, 65532])

    def test_sub(self):
        self.run_prg("""0. SUB 5 -3 1;
                        1. SUB 5 3 2;
                        2. SUB -3 -3 3;
                        3. SUB -3 5 4;""")
        self.assertEqual(self.ram[1:5], [8, 2, 0, 65528])

    def test_and(self):
        self.run_prg("""0. AND -5 -4 1;
                        1. AND 32768 -4 2;
                        2. AND 32768 4 3;""")
        self.assertEqual(self.ram[1:4], [65528, 32768, 0])

    def test_or(self):
        self.run_prg("""0. OR 2 4 1;
                        1. OR 15 32 2;")
                        2. OR 2 2 3;""")
        self.assertEqual(self.ram[1:4], [6, 47, 2])

    def test_xor(self):
        self.run_prg("""0. XOR 2 4 1;
                        1. XOR 15 32 2;
                        2. XOR 2 2 3;
                        3. XOR 2 3 4;""")
        self.assertEqual(self.ram[1:5], [6, 47, 0, 1])

    def test_and_not(self):
        self.run_prg("""0. ANT 16 16 1;
                        1. ANT 15 16 2;
                        2. ANT 31 16 3;
                        3. ANT -31 16 4;""")
        self.assertEqual(self.ram[1:5], [0, 15, 15, 65505])

    def test_shift_left(self):
        self.run_prg("""0. SL 3 2 1;
                        1. SL 12 -2 2;
                        2. SL -1 1 3;""")
        self.assertEqual(self.ram[1:4], [12, 0, 65534])

    def test_shift_right_logic(self):
        self.run_prg("""0. SRL -1 1 1;
                        1. SRL -1 3 2;
                        2. SRL 63 3 3;""")
        self.assertEqual(self.ram[1:4], [65535, 65535, 7])

    def test_shift_right_arithmetic(self):
        pass

    def test_IP(self):
        self.run_prg("""0. MNZ 0 3 1;
                        1. MNZ 1 4 2;
                        2. MNZ -1 A0 3;
                        4. MNZ -1 1 5;""")
        self.assertEqual(self.ram[:6], [4, 0, 4, 2, 0, 1])

if __name__ == '__main__':
    unittest.main()
