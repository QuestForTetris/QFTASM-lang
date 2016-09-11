import tokenize
from xml.etree import ElementTree

from typing import Optional


class GrammarParser:
    def __init__(self, filename="tree_builder/grammar.xml"):
        self.grammar_xml = ElementTree.parse(filename).getroot()
        assert self.grammar_xml.tag == "grammar"
        self.start_stmt = self.grammar_xml.attrib["start"]
        self.stmts = {}
        for stmt_definition in self.grammar_xml:
            self.stmts[stmt_definition.attrib["name"]] = DefineParser(stmt_definition)
        assert self.start_stmt in self.stmts

    def accepts(self, tokens) -> Optional["GrammarTree"]:
        new_tokens, accepts = self.stmts[self.start_stmt].accepts(tokens)
        if accepts:
            return accepts


class DefineParser:
    def __init__(self, root):
        self._root = root
        assert self._root.tag == "define"
        self.name = self._root.attrib["name"]
        self.blocks = [BlockParser(block) for block in self._root.findall("block")]

    def accepts(self, tokens):
        # print("StartDef", self.name)
        # if self.name == "if":
        #    print("Tokens", [tokenize.tok_name[token.exact_type]for token in tokens])
        #    print("Tokens", [token.string for token in tokens])
        for block in self.blocks:
            new_tokens, accepts = block.accepts(tokens)
            # print("B", block, "A", accepts)
            if accepts:
                grammar_tree = GrammarTree(self.name, accepts)
                # print("EndDef", self.name)
                return new_tokens, grammar_tree
        # print("FailDef", self.name)
        return tokens, False


class BlockParser:
    def __init__(self, root):
        self.parsers = {
            "repeat": RepeatParser,
            "token": TokenParser,
            "stmt": StmtParser,
            "optional": OptionalParser
        }

        self._root = root
        self.stmts = []
        for stmt in self._root:
            self.stmts.append(self.parsers[stmt.tag](stmt))
        assert self._root.tag == "block"

    def __repr__(self):
        return str(self.stmts)

    def accepts(self, tokens):
        stmts = []
        for statement in self.stmts:
            new_tokens, accepts = statement.accepts(tokens)
            if not accepts:
                return tokens, False
            if isinstance(statement, RepeatParser):
                accepts = [GrammarTree(statement.name+"_"+str(i), stmt) for i, stmt in enumerate(accepts) if stmt is not True]
                accepts = (statement.name, accepts)
                stmts.append(accepts)
            elif isinstance(statement, OptionalParser):
                stmts.extend(accepts)
            else:
                stmts.append(accepts)
            tokens = new_tokens
        if "name" in self._root.attrib:
            name = self._root.attrib["name"]
            stmts.append(("_block_name", name))
            if name == "_":
                return tokens, True
        return tokens, stmts


class RepeatParser:
    def __init__(self, root):
        self._root = root
        assert self._root.tag == "repeat"
        self.blocks = [BlockParser(block) for block in self._root.findall("block")]
        self.name = self._root.attrib["name"]

    def accepts(self, tokens, accepts=None):
        if accepts == None:
            accepts = []
        for block in self.blocks:
            new_tokens, block_accepts = block.accepts(tokens)
            if block_accepts:
                accepts.append(block_accepts)
                return self.accepts(new_tokens, accepts)
        if accepts:
            return tokens, accepts
        else:
            return tokens, False


class TokenParser:
    def __init__(self, root):
        self._root = root
        assert self._root.tag == "token"
        self.attrib = self._root.attrib

    def __repr__(self):
        return "TokenParser%s"%self.attrib

    def accepts(self, tokens):
        for attr in self.attrib:
            if attr == "var":
                continue
            token_value = getattr(tokens[0], attr)
            if attr in ("exact_type", "type"):
                token_value = tokenize.tok_name[token_value]
            if token_value != self.attrib[attr]:
                #print("TokenFAIL", attr, self.attrib[attr], "was", token_value)
                return tokens, False
        if "var" in self.attrib:
            return tokens[1:], (self.attrib["var"], tokens[0].string)
        return tokens[1:], True


class StmtParser:
    def __init__(self, root):
        self._root = root
        assert self._root.tag == "stmt"
        self.name = self._root.attrib["name"]

    def __repr__(self):
        return "StmtParser(%s)"%self.name

    def accepts(self, tokens):
        new_tokens, accepts = grammar_parser.stmts[self.name].accepts(tokens)
        if accepts:
            return new_tokens, (self.name, accepts)
        return tokens, False

class OptionalParser(BlockParser):
    def __init__(self, root):
        try:
            super().__init__(root)
        except AssertionError: pass
        self._root = root
        self.name = self._root.attrib["name"]
        assert self._root.tag == "optional"

    def accepts(self, tokens):
        tokens, accepts = super().accepts(tokens)
        if not accepts: accepts = [True]
        return tokens, accepts


class GrammarTree:
    def __init__(self, name, vars):
        self.name = name
        self._list = []
        self._dict = {}
        for var in vars:
            if var is True: continue
            key, value = var
            self._dict[key] = value

    def __repr__(self):
        rtn = "\n".join(repr(key)+": "+repr(value) for key, value in self._dict.items()).splitlines()
        rtn = "\n".join("\t"+i for i in rtn)
        return "GrammarTree %s\n%s\n"%(self.name, rtn)


def tokenise(inp):
    tokens = tokenize.tokenize(inp.readline)
    next(tokens)
    tokens = list(tokens)
    for i, token in enumerate(tokens):
        if tokenize.tok_name[token.exact_type] == "NL":
            tokens[i] = type(token)(tokenize.NEWLINE, token.string, token.start, token.end, token.line)
    return tokens

if __name__ == "__main__":
    grammar_parser = GrammarParser()
    with open("primes.txt", "rb") as inp:
        tokens = tokenise(inp)
        #print([tokenize.tok_name[token.type]for token in tokens])
        #print([tokenize.tok_name[token.exact_type]for token in tokens])
        #print([token.string for token in tokens])
        print(grammar_parser.accepts(tokens))