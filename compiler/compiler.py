import sys

from tree_builder.tree_builder import build_tree
from high_level_compiler.high_level_compiler import FileInterpreter as HighLevelFileInterpreter
from low_level_compiler.low_level_compiler import FileInterpreter as LowLevelFileInterpreter

class Compiler:
    def __init__(self, filename):
        high_level_file_interpreter = HighLevelFileInterpreter(build_tree(filename))
        compiled = high_level_file_interpreter.compile()
        self.low_level_file_interpreter = LowLevelFileInterpreter(compiled,
                                                                  high_level_file_interpreter.global_store)

if __name__ == "__main__":
    #"""
    compiler = Compiler(sys.argv[1])
    print("\n".join(compiler.low_level_file_interpreter.compiled))
    """
    high_level_file_interpreter = HighLevelFileInterpreter(build_tree(sys.argv[1]))
    compiled = high_level_file_interpreter.compile()
    for c in compiled:
        print(c)
    #print(compiled)
    #"""
