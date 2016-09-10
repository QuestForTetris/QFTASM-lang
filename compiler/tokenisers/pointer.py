from tokenisers.base import BaseTokeniser

class PointerTokeniser(BaseTokeniser):
    def __init__(self, tokens):
        self.points_to = next(tokens)
        self.name = next(tokens)

    def __str__(self):
        return "Pointer[%s] %s"%(self.points_to.string, self.name.string)