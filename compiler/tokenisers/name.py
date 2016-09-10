from tokenisers.base import BaseTokeniser
from tokenisers.type import TypeTokeniser

class NameTokeniser(BaseTokeniser):
    def __init__(self, tokens):
        potential_type = next(tokens)
        self.type = None
        if potential_type.string in TypeTokeniser.types:
            self.type = potential_type
            self.name = next(tokens)
        else:
            self.name = potential_type

    def __str__(self):
        if self.type is None:
            return "Name: %s" %self.name.string
        return "Name: %s (%s)"%(self.name.string, self.type.string)