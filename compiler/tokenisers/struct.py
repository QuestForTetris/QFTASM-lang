import tokenize

from tokenisers.dedent import DedentTokeniser
from tokenisers.pointer import PointerTokeniser
from tokenisers.name import NameTokeniser

class StructTokeniser(DedentTokeniser):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.name = self.tokens[0]
        self.tokens = self.tokens[3:-1]
        self.contents = []
        split_tokens = self.split_tokens_newline(self.tokens)
        for token_list in split_tokens:
            token_type = tokenize.tok_name[token_list[0].exact_type]
            assert token_type in ["NAME", "STAR"]
            if token_type == "NAME":
                self.contents.append(NameTokeniser(iter(token_list)))
            elif token_type == "STAR":
                self.contents.append(PointerTokeniser(iter(token_list[1:])))
        #print(self)

    def __str__(self):
        rtn = ["{"]
        for token in self.contents:
            rtn.append("    "+str(token))
        rtn.append("}")
        return "\n".join(rtn)