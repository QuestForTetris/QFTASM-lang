from tokenisers.base import BaseTokeniser
from ast import literal_eval

class LiteralTokeniser(BaseTokeniser):
    def __init__(self, tokens):
        self.literal = literal_eval(next(tokens).string)

    def __str__(self):
        return "%s"%(self.name.string)