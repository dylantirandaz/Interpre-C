import re
import sys

# Define tokens
class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

# Tokenizer (Lexical Analysis)
class Tokenizer:
    def __init__(self, code):
        self.code = code
        self.position = 0
        self.current_char = self.code[self.position] if self.position < len(self.code) else None

    def advance(self):
        self.position += 1
        if self.position < len(self.code):
            self.current_char = self.code[self.position]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def get_next_token(self):
        self.skip_whitespace()

        if self.current_char is None:
            return Token('EOF', None)

        if self.current_char.isdigit():
            return self.number()

        if self.current_char.isalpha():
            return self.identifier()

        if self.current_char == '+':
            self.advance()
            return Token('PLUS', '+')

        if self.current_char == '-':
            self.advance()
            return Token('MINUS', '-')

        if self.current_char == '*':
            self.advance()
            return Token('MUL', '*')

        if self.current_char == '/':
            self.advance()
            return Token('DIV', '/')

        if self.current_char == '=':
            self.advance()
            return Token('ASSIGN', '=')

        if self.current_char == '(':
            self.advance()
            return Token('LPAREN', '(')

        if self.current_char == ')':
            self.advance()
            return Token('RPAREN', ')')

        if self.current_char == '{':
            self.advance()
            return Token('LBRACE', '{')

        if self.current_char == '}':
            self.advance()
            return Token('RBRACE', '}')

        if self.current_char == ',':
            self.advance()
            return Token('COMMA', ',')

        raise Exception(f"Illegal character '{self.current_char}'")

    def number(self):
        num = ''
        while self.current_char and self.current_char.isdigit():
            num += self.current_char
            self.advance()
        return Token('NUMBER', int(num))

    def identifier(self):
        id_str = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()
        if id_str == 'if':
            return Token('IF', 'if')
        elif id_str == 'else':
            return Token('ELSE', 'else')
        elif id_str == 'while':
            return Token('WHILE', 'while')
        elif id_str == 'function':
            return Token('FUNCTION', 'function')
        return Token('ID', id_str)

    def peek(self):
        peek_pos = self.position + 1
        if peek_pos < len(self.code):
            return self.code[peek_pos]
        return None

# Abstract Syntax Tree (AST) Nodes
class AST:
    pass

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Var(AST):
    def __init__(self, token):
        self.token = token
        self.name = token.value

class Assign(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class If(AST):
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition
        self.true_body = true_body
        self.false_body = false_body

class While(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class FunctionDef(AST):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FunctionCall(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args

# Parser (Syntax Analysis)
class Parser:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.current_token = self.tokenizer.get_next_token()

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.tokenizer.get_next_token()
        else:
            raise Exception(f"Expected {token_type}, found {self.current_token.type}")

    def factor(self):
        token = self.current_token
        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return Num(token)
        elif token.type == 'ID':
            self.eat('ID')
            return Var(token)
        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node

    def term(self):
        node = self.factor()
        while self.current_token.type in ('MUL', 'DIV'):
            token = self.current_token
            if token.type == 'MUL':
                self.eat('MUL')
            elif token.type == 'DIV':
                self.eat('DIV')
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in ('PLUS', 'MINUS'):
            token = self.current_token
            if token.type == 'PLUS':
                self.eat('PLUS')
            elif token.type == 'MINUS':
                self.eat('MINUS')
            node = BinOp(left=node, op=token, right=self.term())
        return node

    def assignment_statement(self):
        left = Var(self.current_token)
        self.eat('ID')
        self.eat('ASSIGN')
        right = self.expr()
        return Assign(left, right)

    def statement(self):
        if self.current_token.type == 'ID':
            next_char = self.tokenizer.peek()
            if next_char == '=':
                return self.assignment_statement()
            else:
                return self.expr()
        else:
            return self.expr()

    def parse(self):
        return self.statement()

# Interpreter (Evaluation)
class Interpreter:
    def __init__(self, parser):
        self.parser = parser
        self.variables = {}

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op.type == 'PLUS':
            return left + right
        elif node.op.type == 'MINUS':
            return left - right
        elif node.op.type == 'MUL':
            return left * right
        elif node.op.type == 'DIV':
            return left / right

    def visit_Num(self, node):
        return node.value

    def visit_Var(self, node):
        var_name = node.name
        if var_name not in self.variables:
            raise Exception(f"Undefined variable '{var_name}'")
        return self.variables[var_name]

    def visit_Assign(self, node):
        var_name = node.left.name
        value = self.visit(node.right)
        self.variables[var_name] = value
        return value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

# Memory Management
class Memory:
    def __init__(self):
        self.variables = {}

    def set_var(self, name, value):
        self.variables[name] = value

    def get_var(self, name):
        return self.variables.get(name, None)

# Main execution
def main():
    interpreter = Interpreter(None)
    while True:
        try:
            text = input('c-interpreter> ')
            if text.strip() == 'exit':
                break

            tokenizer = Tokenizer(text)
            parser = Parser(tokenizer)
            interpreter.parser = parser
            result = interpreter.interpret()
            print(f"Result: {result}")
            print(f"Variables: {interpreter.variables}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
