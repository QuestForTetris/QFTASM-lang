from tokenisers.base import BaseTokeniser


class TypeTokeniser(BaseTokeniser):
    types = ["int", "bool", "null"]
    def __init__(self, tokens):
        self.type = next(tokens)

    def __str__(self):
        return "Bare Type: %s"%self.type.string