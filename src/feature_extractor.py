
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

        # Nesting-depth tracking
        self.current_depth = 0
        self.max_depth = 0

    # ----------------------------------
    # AST visitor methods for counting
    # ----------------------------------

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.function_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.class_count += 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.if_count += 1

        # Visit the condition.
        self.visit(node.test)

        # Visit the body at the current nesting depth.
        for statement in node.body:
            self.visit(statement)

        # An elif is represented as an If inside orelse.
        # Visit elif branches without increasing nesting depth.
        for statement in node.orelse:
            if isinstance(statement, ast.If):
                self.visit_elif(statement)
            else:
                self.visit(statement)

    def visit_elif(self, node):
        """Count and visit an elif branch without adding nesting depth."""
        self.if_count += 1

        self.visit(node.test)

        for statement in node.body:
            self.visit(statement)

        for statement in node.orelse:
            if isinstance(statement, ast.If):
                self.visit_elif(statement)
            else:
                self.visit(statement)

    def visit_For(self, node):
        self.for_count += 1
        self.visit_nested(node)

    def visit_AsyncFor(self, node):
        self.for_count += 1
        self.visit_nested(node)

    def visit_While(self, node):
        self.while_count += 1
        self.visit_nested(node)

    def visit_Try(self, node):
        self.try_count += 1
        self.visit_nested(node)

    def visit_TryStar(self, node):
        # Handles try/except* statements in Python 3.11+.
        self.try_count += 1
        self.visit_nested(node)

    def visit_With(self, node):
        self.visit_nested(node)

    def visit_AsyncWith(self, node):
        self.visit_nested(node)

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

    # ----------------------------------
    # Nesting-depth calculation
    # ----------------------------------

    def visit_nested(self, node):
        """Track the maximum nesting depth of supported structures."""

        self.current_depth += 1

        self.max_depth = max(
            self.max_depth,
            self.current_depth
        )

        self.generic_visit(node)

        self.current_depth -= 1

    # ----------------------------------
    # Feature extraction
    # ----------------------------------

    def extract(self, code):
        self.reset_counters()

        # Count nonblank physical lines.
        loc = sum(
            1
            for line in code.splitlines()
            if line.strip()
        )

        # Parse source code safely.
        try:
            tree = ast.parse(code)

        except SyntaxError as error:
            return {
                "error": "Invalid Python syntax",
                "message": error.msg,
                "line": error.lineno,
                "loc": loc,
            }

        # Visit AST nodes and calculate features.
        self.visit(tree)

        # Return extracted features.
        return {
            "loc": loc,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "if_count": self.if_count,
            "for_count": self.for_count,
            "while_count": self.while_count,
            "try_count": self.try_count,
        }