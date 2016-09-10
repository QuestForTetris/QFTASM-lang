import tokenize
from tokenisers.base import BaseTokeniser
from tokenisers.name import NameTokeniser

from itertools import chain

class DedentTokeniser(BaseTokeniser):
    keywords = {}
    def __init__(self, tokens):
        self.tokens = []
        self.get_tokens(tokens)

    def __str__(self):
        rtn = []
        for token in self.tokens:
            rtn.append("%s:\t%s"%(tokenize.tok_name[token.type], token.string))
        return "\n".join(rtn)

    def construct(self, token_generator):
        for token in token_generator:
            if tokenize.tok_name[token.type] == "DEDENT":
                break
            elif tokenize.tok_name[token.type] == "NEWLINE":
                continue
            print("Construct", self.str_token(token))
            self.construct_single(token, token_generator)

    def construct_single(self, token, token_generator):
        assert (tokenize.tok_name[token.type] == "NAME")
        if token.string in DedentTokeniser.keywords:
            return DedentTokeniser.keywords[token.string](token_generator)
        else:
            #Do something with a variable?
            recombined = chain([token], token_generator)
            name = NameTokeniser(recombined)
            print(name)

    def get_tokens(self, token_generator):
        cur_token = next(token_generator)
        cur_indent = 0
        indented = False
        while cur_indent != 0 or not indented:
            self.tokens.append(cur_token)
            cur_token = next(token_generator)
            if tokenize.tok_name[cur_token.type] == "INDENT":
                indented = True
                cur_indent += 1
            elif tokenize.tok_name[cur_token.type] == "DEDENT":
                cur_indent -= 1

    def split_tokens_newline(self, tokens):
        split_tokens = [[]]
        for token in self.tokens:
            if tokenize.tok_name[token.type] == "NEWLINE":
                split_tokens.append([])
            else:
                split_tokens[-1].append(token)
        return split_tokens