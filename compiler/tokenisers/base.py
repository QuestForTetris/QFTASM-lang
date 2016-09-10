import tokenize

class BaseTokeniser:
    def str_token(self, token):
        return "%s:\t%s"%(tokenize.tok_name[token.type], token.string)