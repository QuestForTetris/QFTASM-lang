from tree_builder.tree_builder import build_tree
from high_level_compiler.high_level_compiler import FileInterpreter as HighLevelFileInterpreter
from low_level_compiler.low_level_compiler import FileInterpreter as LowLevelFileInterpreter

if __name__ == "__main__":
    high_level_file_interpreter = HighLevelFileInterpreter(build_tree("primes.txt"))
    compiled = high_level_file_interpreter.compile()
    low_level_file_interpreter = LowLevelFileInterpreter(compiled,
                                                         high_level_file_interpreter.global_store)