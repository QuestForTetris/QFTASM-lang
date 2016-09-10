import tokenize

from tokenisers.dedent import DedentTokeniser
from tokenisers.name import NameTokeniser
from tokenisers.literal_value import LiteralTokeniser
from tokenisers.comparison import ComparisonTokeniser

class ForTokeniser(DedentTokeniser):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.tokens = iter(self.tokens)
        self.parse_declaration(self.tokens)

    def parse_declaration(self, tokens):
        declaration = [next(tokens)]
        while tokenize.tok_name[declaration[-1].type] != "NEWLINE":
            declaration.append(next(tokens))
        declaration.pop()
        if declaration[0].string != "(" or declaration[-1].string != ")":
            raise SyntaxError("For loops must have brackets")
        declaration = iter(declaration[1:-1])
        self.variable = NameTokeniser(declaration)
        assert next(declaration).string == "="
        self.default_value = LiteralTokeniser(declaration)
        assert next(declaration).string == ";"
        self.comparison = ComparisonTokeniser(declaration)
        assert next(declaration).string == ";"
        self.construct_single(next(declaration), declaration)
        print(next(declaration))
