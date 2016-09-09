from tokeniser_dedent import DedentTokeniser

class StructTokeniser(DedentTokeniser):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.name = self.tokens[0]
        self.tokens = self.tokens[3:]
        print("STRUCT", self, sep="\n")
