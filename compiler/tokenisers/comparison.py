from tokenisers.base import BaseTokeniser

class ComparisonTokeniser(BaseTokeniser):
    def __init__(self, tokens):
        self.val_1 = next(tokens)
        self.comparison = next(tokens)
        self.val_2 = next(tokens)

    def __str__(self):
        return "%s %s %s"%(self.val_1.string, self.comparison.string, self.val_2.string)