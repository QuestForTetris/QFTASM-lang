import tokenize

from tokenisers.base import BaseTokeniser

class ArgsTokeniser(BaseTokeniser):
    def __init__(self, token_generator):
        self.args = [next(token_generator)]
        while tokenize.tok_name[self.args[-1].exact_type] != "RPAR":
            self.args.append(next(token_generator))
        self.args.pop()

    def __str__(self):
        return "("+", ".join(arg.string for arg in self.args)+")"