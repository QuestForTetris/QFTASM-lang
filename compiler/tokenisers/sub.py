import tokenize

from tokenisers.dedent import DedentTokeniser
from tokenisers.args import ArgsTokeniser
from tokenisers.type import TypeTokeniser


class SubTokeniser(DedentTokeniser):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.tokens = iter(self.tokens)
        self.parse_declaration(self.tokens)
        print("sub %s%s -> %s"%(self.name, self.args, self.return_type))
        next(self.tokens)
        self.construct(self.tokens)

    def parse_declaration(self, tokens):
        declaration = [next(tokens)]
        while tokenize.tok_name[declaration[-1].type] != "NEWLINE":
            declaration.append(next(tokens))
        self.name, *optional = declaration[:-1]
        self.name = self.name.string
        self.args = []
        self.return_type = None
        if optional:
            optional = iter(optional)
            optional_type = next(optional).string
            if optional_type == "(":
                self.args = ArgsTokeniser(optional)
                if optional:
                    optional_type = next(optional).string
            if optional_type == "->":
               self.return_type = TypeTokeniser(optional)