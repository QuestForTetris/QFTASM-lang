import unittest
from interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    def setUp(self):
        super(TestInterpreter, self).setUp()
        self.interpreter = Interpreter("")
        self.ram = self.interpreter.ram

    def test_semicolon(self):
        with self.assertRaises(SyntaxError):
            self.interpreter.tokenise("0. MLZ -1 -1 -1")

    def test_mov_not_zero(self):
        self.interpreter.tokenise("0. MNZ 0 3 1;")()
        self.assertEquals(self.ram[2], 0)
        self.interpreter.tokenise("0. MNZ 1 3 2;")()
        self.assertEquals(self.ram[2], 3)
        self.interpreter.tokenise("0. MNZ -1 3 3;")()
        self.assertEquals(self.ram[3], 3)

    def test_mov_less_zero(self):
        self.interpreter.tokenise("0. MLZ 1 3 1;")()
        self.assertEquals(self.ram[2], 0)
        self.interpreter.tokenise("0. MLZ 0 3 1;")()
        self.assertEquals(self.ram[2], 0)
        self.interpreter.tokenise("0. MLZ -1 3 2;")()
        self.assertEquals(self.ram[2], 3)
        self.interpreter.tokenise("0. MLZ -1 3 3;")()
        self.assertEquals(self.ram[3], 3)

    def test_add(self):
        self.interpreter.tokenise("0. ADD 1 3 1;")()
        self.assertEquals(self.ram[1], 4)
        self.interpreter.tokenise("0. ADD 1 -3 1;")()
        self.assertEquals(self.ram[1], 65534)
        self.interpreter.tokenise("0. ADD -1 -3 1;")()
        self.assertEquals(self.ram[1], 65532)

    def test_sub(self):
        self.interpreter.tokenise("0. SUB 5 -3 1;")()
        self.assertEquals(self.ram[1], 8)
        self.interpreter.tokenise("0. SUB 5 3 1;")()
        self.assertEquals(self.ram[1], 2)
        self.interpreter.tokenise("0. SUB -3 -3 1;")()
        self.assertEquals(self.ram[1], 0)
        self.interpreter.tokenise("0. SUB -3 5 1;")()
        self.assertEquals(self.ram[1], 65528)

    def test_and(self):
        self.interpreter.tokenise("0. AND -5 -4 1;")()
        self.assertEquals(self.ram[1], 65528)
        self.interpreter.tokenise("0. AND 32768 -4 1;")()
        self.assertEquals(self.ram[1], 32768)
        self.interpreter.tokenise("0. AND 32768 4 1;")()
        self.assertEquals(self.ram[1], 0)

    def test_or(self):
        self.interpreter.tokenise("0. OR 2 4 1;")()
        self.assertEquals(self.ram[1], 6)
        self.interpreter.tokenise("0. OR 15 32 1;")()
        self.assertEquals(self.ram[1], 47)
        self.interpreter.tokenise("0. AND 2 2 1;")()
        self.assertEquals(self.ram[1], 2)

    def test_xor(self):
        self.interpreter.tokenise("0. XOR 2 4 1;")()
        self.assertEquals(self.ram[1], 6)
        self.interpreter.tokenise("0. XOR 15 32 1;")()
        self.assertEquals(self.ram[1], 47)
        self.interpreter.tokenise("0. XOR 2 2 1;")()
        self.assertEquals(self.ram[1], 0)
        self.interpreter.tokenise("0. XOR 2 3 1;")()
        self.assertEquals(self.ram[1], 1)

    def test_and_not(self):
        self.interpreter.tokenise("0. ANT 16 16 1;")()
        self.assertEquals(self.ram[1], 0)
        self.interpreter.tokenise("0. ANT 15 16 1;")()
        self.assertEquals(self.ram[1], 15)
        self.interpreter.tokenise("0. ANT 31 16 1;")()
        self.assertEquals(self.ram[1], 15)
        self.interpreter.tokenise("0. ANT -31 16 1;")()
        self.assertEquals(self.ram[1], 65505)

    def test_shift_left(self):
        self.interpreter.tokenise("0. SL 3 2 1;")()
        self.assertEquals(self.ram[1], 12)
        self.interpreter.tokenise("0. SL 12 -2 1;")()
        self.assertEquals(self.ram[1], 0)
        self.interpreter.tokenise("0. SL -1 1 1;")()
        self.assertEquals(self.ram[1], 65534)

    def test_shift_right_logic(self):
        self.interpreter.tokenise("0. SRL -1 1 1;")()
        self.assertEquals(self.ram[1], 65535)
        self.interpreter.tokenise("0. SRL -1 3 1;")()
        self.assertEquals(self.ram[1], 65535)
        self.interpreter.tokenise("0. SRL 63 3 1;")()
        self.assertEquals(self.ram[1], 7)

    def test_shift_right_arithmetic(self):
        pass


if __name__ == '__main__':
    unittest.main()