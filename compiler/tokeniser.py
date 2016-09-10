import tokenize
from tokenisers.struct import StructTokeniser
from tokenisers.sub import SubTokeniser
from tokenisers.dedent import DedentTokeniser
from tokenisers.for_loop import ForTokeniser


DedentTokeniser.keywords["for"] = ForTokeniser

struct_tokens = {"struct": StructTokeniser,
                 "sub": SubTokeniser}


def tokenise(inp):
    tokens = tokenize.tokenize(inp.readline)
    next(tokens)
    for token in tokens:
        if tokenize.tok_name[token.type] in ["NL", "ENDMARKER"]:
            pass
        else:
            yield token

if __name__ == "__main__":
    with open("primes.txt", "rb") as inp:
        tokens = tokenise(inp)
        for token in tokens:
            assert(tokenize.tok_name[token.type] == "NAME")
            struct_tokens[token.string](tokens)

