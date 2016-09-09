from tokeniser_dedent import DedentTokeniser

class SubTokeniser(DedentTokeniser):
    def __init__(self, tokens):
        super().__init__(tokens)
        #print("SUB", self, sep="\n")