
import ast


code = """
import json
from pathlib import Path


class Calculator:

    def add(self, x, y):
        if x > 0:
            return x + y

        return x + y


def process(items):
    try:
        for item in items:
            print(item)
            return item
    except ValueError:
        return None

    while False:
        print("running")
"""


class FeatureExtractor(ast.NodeVisitor):

    def __init__(self):
        self.reset_counters()

    def reset_counters(self):
        self.function_count = 0
        self.class_count = 0
        self.if_count = 0
        self.for_count = 0
        self.while_count = 0
        self.try_count = 0
        self.except_count = 0
        self.import_count = 0
        self.return_count = 0

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.class_count += 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.if_count += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.for_count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.while_count += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.try_count += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.except_count += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        self.import_count += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.import_count += 1
        self.generic_visit(node)

    def visit_Return(self, node):
        self.return_count += 1
        self.generic_visit(node)

    def extract(self, code):
        self.reset_counters()

        # Count nonblank physical lines.
        loc = sum(
            1 for line in code.splitlines()
            if line.strip()
        )

        # Parse the source code safely.
        try:
            tree = ast.parse(code)
        except SyntaxError as error:
            return {
                "error": "Invalid Python syntax",
                "message": error.msg,
                "line": error.lineno,
                "loc": loc,
            }

        # Visit the AST nodes.
        self.visit(tree)

        # Return the extracted features.
        return {
            "loc": loc,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "if_count": self.if_count,
            "for_count": self.for_count,
            "while_count": self.while_count,
            "try_count": self.try_count,
            "except_count": self.except_count,
            "import_count": self.import_count,
            "return_count": self.return_count,
        }

if __name__ == "__main__":
    extractor = FeatureExtractor()

    invalid_code = """
def greet(
    print("Hello")
"""

    features = extractor.extract(invalid_code)

    print("Extracted Features:")
    print(features)
