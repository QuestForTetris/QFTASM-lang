import tokenize


class DedentTokeniser:
    def __init__(self, tokens):
        self.tokens = []
        self.get_tokens(tokens)

    def __str__(self):
        rtn = []
        for token in self.tokens:
            rtn.append("%s:\t%s"%(tokenize.tok_name[token.type], token.string))
        return "\n".join(rtn)

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