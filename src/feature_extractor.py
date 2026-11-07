"""
Feature extractor for Python AST analysis.

Extracts 20 structural numerical features from Python code snippets for
evaluating code complexity and anti-pattern risk.

Complexity Conventions:
- Cyclomatic Complexity is calculated as a file-level aggregate metric
  (McCabe convention). It starts with a base value of 1 for the module
  and increments for each decision point across the file:
    * 'if' and 'elif' statements
    * 'for' and 'async for' loops
    * 'while' loops
    * 'except' handlers (ast.ExceptHandler)
    * Boolean operators ('and', 'or') - each additional operand adds a decision path
    * Conditional expressions (ternary 'x if c else y')
  Note: This is a file-level aggregate representing the structural branching
  density of the entire snippet, rather than individual per-function complexity.
  Per-function lengths and parameter counts are tracked separately in
  features 13-16.

Nesting Depth Conventions:
- Nesting depth measures the maximum depth of control-flow blocks.
- Blocks that increase nesting depth (+1):
    * Loops: 'for', 'async for', 'while'
    * Conditional bodies: 'if' body, 'elif' body, 'else' body
    * Exception blocks: 'try', 'try*'
    * Context managers: 'with', 'async with'
- 'elif' chains: An 'elif' represents an alternative branch of the enclosing
  decision structure; it increments cyclomatic complexity (decision point)
  without adding an additional nesting level beyond the initial 'if'.
"""

import ast


class FeatureExtractor(ast.NodeVisitor):

    def __init__(self):
        self.reset_counters()

    def reset_counters(self):
        # Features 1–10: Basic AST metrics
        self.function_count = 0
        self.class_count = 0
        self.if_count = 0
        self.for_count = 0
        self.while_count = 0
        self.try_count = 0
        self.except_count = 0
        self.import_count = 0
        self.return_count = 0

        # Feature 11: Maximum nesting depth
        self.current_depth = 0
        self.max_depth = 0

        # Feature 12: Cyclomatic complexity (file-level aggregate)
        self.cyclomatic_complexity = 1

        # Features 13–14: Function lengths
        self.function_lengths = []

        # Features 15–16: Function parameters
        self.total_parameter_count = 0
        self.max_parameters = 0

        # Feature 17: Boolean operators
        self.boolean_operator_count = 0

        # Feature 18: Comparison operators
        self.comparison_operator_count = 0

        # Feature 19: Bare except handlers
        self.bare_except_count = 0

        # Feature 20: Global statements
        self.global_statement_count = 0

    # ----------------------------------
    # Functions and classes
    # ----------------------------------

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.record_function_metrics(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.function_count += 1
        self.record_function_metrics(node)
        self.generic_visit(node)

    def record_function_metrics(self, node):
        # Function length: physical line span from def to final line.
        if node.end_lineno is not None:
            length = node.end_lineno - node.lineno + 1
            self.function_lengths.append(length)

        # Count positional, keyword-only, *args, and **kwargs.
        args = node.args

        parameter_count = (
            len(args.posonlyargs)
            + len(args.args)
            + len(args.kwonlyargs)
            + (1 if args.vararg else 0)
            + (1 if args.kwarg else 0)
        )

        self.total_parameter_count += parameter_count
        self.max_parameters = max(
            self.max_parameters,
            parameter_count
        )

    def visit_ClassDef(self, node):
        self.class_count += 1
        self.generic_visit(node)

    # ----------------------------------
    # Conditional statements
    # ----------------------------------

    def visit_If(self, node):
        self.if_count += 1
        self.cyclomatic_complexity += 1

        # Evaluate condition at the current nesting depth
        self.visit(node.test)

        # The body of the if block is nested one level deeper
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        for statement in node.body:
            self.visit(statement)
        self.current_depth -= 1

        # Handle elif and else branches
        self._visit_if_orelse(node, node.orelse)

    def visit_elif(self, node):
        """
        Count an elif branch as an additional decision point (cyclomatic complexity + 1)
        without increasing the nesting depth relative to the parent if statement.
        """
        self.if_count += 1
        self.cyclomatic_complexity += 1

        # Evaluate condition at the parent nesting depth
        self.visit(node.test)

        # The body of the elif branch is nested at the same depth as the parent if body (+1)
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        for statement in node.body:
            self.visit(statement)
        self.current_depth -= 1

        # Handle further chained elif branches or a final else block
        self._visit_if_orelse(node, node.orelse)

    def _visit_if_orelse(self, parent_if, orelse):
        """
        Helper method to handle the orelse branch of an if/elif statement.
        Distinguishes an 'elif' statement from a nested 'if' inside an 'else:' block.
        In Python syntax, an 'elif' is placed at the exact same column offset as its parent 'if'.
        An 'if' nested inside an 'else:' block has a strictly greater column offset.
        """
        if not orelse:
            return

        is_elif = (
            len(orelse) == 1
            and isinstance(orelse[0], ast.If)
            and getattr(orelse[0], "col_offset", None) is not None
            and getattr(parent_if, "col_offset", None) is not None
            and orelse[0].col_offset == parent_if.col_offset
        )

        if is_elif:
            self.visit_elif(orelse[0])
        else:
            # A regular 'else:' block introduces a nested block at the same depth as the if body.
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)
            for statement in orelse:
                self.visit(statement)
            self.current_depth -= 1

    # ----------------------------------
    # Loops
    # ----------------------------------

    def visit_For(self, node):
        self.for_count += 1
        self.cyclomatic_complexity += 1
        self.visit_nested(node)

    def visit_AsyncFor(self, node):
        self.for_count += 1
        self.cyclomatic_complexity += 1
        self.visit_nested(node)

    def visit_While(self, node):
        self.while_count += 1
        self.cyclomatic_complexity += 1
        self.visit_nested(node)

    # ----------------------------------
    # Exception handling
    # ----------------------------------

    def visit_Try(self, node):
        self.try_count += 1
        self.visit_nested(node)

    def visit_TryStar(self, node):
        self.try_count += 1
        self.visit_nested(node)

    def visit_ExceptHandler(self, node):
        self.except_count += 1
        self.cyclomatic_complexity += 1

        if node.type is None:
            self.bare_except_count += 1

        self.generic_visit(node)

    # ----------------------------------
    # Context managers
    # ----------------------------------

    def visit_With(self, node):
        self.visit_nested(node)

    def visit_AsyncWith(self, node):
        self.visit_nested(node)

    # ----------------------------------
    # Imports and returns
    # ----------------------------------

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
    # Boolean operators
    # ----------------------------------

    def visit_BoolOp(self, node):
        self.boolean_operator_count += len(node.values) - 1

        # Each additional Boolean operator adds a decision point.
        self.cyclomatic_complexity += len(node.values) - 1

        self.generic_visit(node)

    # ----------------------------------
    # Comparison operators
    # ----------------------------------

    def visit_Compare(self, node):
        self.comparison_operator_count += len(node.ops)
        self.generic_visit(node)

    # ----------------------------------
    # Global statements
    # ----------------------------------

    def visit_Global(self, node):
        # Count each global declaration statement.
        self.global_statement_count += 1
        self.generic_visit(node)

    # ----------------------------------
    # Conditional expressions
    # ----------------------------------

    def visit_IfExp(self, node):
        # Example: result = "yes" if condition else "no"
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    # ----------------------------------
    # Nesting-depth calculation
    # ----------------------------------

    def visit_nested(self, node):
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

        # Feature 1: Nonblank physical lines.
        loc = sum(
            1 for line in code.splitlines()
            if line.strip()
        )

        try:
            tree = ast.parse(code)
        except SyntaxError as error:
            return {
                "error": "Invalid Python syntax",
                "message": error.msg,
                "line": error.lineno,
                "loc": loc,
            }

        self.visit(tree)

        average_function_length = (
            sum(self.function_lengths) / len(self.function_lengths)
            if self.function_lengths
            else 0
        )

        maximum_function_length = (
            max(self.function_lengths)
            if self.function_lengths
            else 0
        )

        return {
            # Features 1–10
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

            # Feature 11
            "max_nesting_depth": self.max_depth,

            # Feature 12
            "cyclomatic_complexity": self.cyclomatic_complexity,

            # Features 13–14
            "average_function_length": average_function_length,
            "maximum_function_length": maximum_function_length,

            # Features 15–16
            "total_parameter_count": self.total_parameter_count,
            "max_parameters": self.max_parameters,

            # Feature 17
            "boolean_operator_count": self.boolean_operator_count,

            # Feature 18
            "comparison_operator_count": self.comparison_operator_count,

            # Feature 19
            "bare_except_count": self.bare_except_count,

            # Feature 20
            "global_statement_count": self.global_statement_count,
        }


# ----------------------------------
# Basic tests
# ----------------------------------

if __name__ == "__main__":

    extractor = FeatureExtractor()

    test_code = """
import os

global_value = 10

def example(x, y, *args, **kwargs):
    global global_value

    try:
        if x > 0 and y < 10:
            for item in args:
                print(item)
    except:
        return None

    result = "positive" if x > 0 else "non-positive"
    return result
"""

    features = extractor.extract(test_code)

    print("Extracted Features:")
    for name, value in features.items():
        print(f"{name}: {value}")

    # Basic assertions for selected features.
    assert features["function_count"] == 1
    assert features["class_count"] == 0
    assert features["if_count"] == 1
    assert features["for_count"] == 1
    assert features["try_count"] == 1
    assert features["except_count"] == 1
    assert features["bare_except_count"] == 1
    assert features["total_parameter_count"] == 4
    assert features["max_parameters"] == 4
    assert features["boolean_operator_count"] == 1
    assert features["comparison_operator_count"] == 3
    assert features["global_statement_count"] == 1
    assert features["max_nesting_depth"] == 3
    assert features["cyclomatic_complexity"] == 6

    print("\nSelected feature tests passed!")

