import ast


class FeatureExtractor(ast.NodeVisitor):

    def __init__(self):
        self.reset_counters()

    def reset_counters(self):
        # Existing features
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

        # Feature 12: Cyclomatic complexity
        self.cyclomatic_complexity = 1

        # Features 13 and 14: Function length
        self.function_lengths = []

    # ----------------------------------
    # Functions and classes
    # ----------------------------------

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.record_function_length(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.function_count += 1
        self.record_function_length(node)
        self.generic_visit(node)

    def record_function_length(self, node):
        """Record physical line span for a function."""
        start_line = node.lineno
        end_line = node.end_lineno

        if end_line is not None:
            length = end_line - start_line + 1
            self.function_lengths.append(length)

    def visit_ClassDef(self, node):
        self.class_count += 1
        self.generic_visit(node)

    # ----------------------------------
    # Conditional statements
    # ----------------------------------

    def visit_If(self, node):
        self.if_count += 1
        self.cyclomatic_complexity += 1

        self.visit(node.test)

        for statement in node.body:
            self.visit(statement)

        for statement in node.orelse:
            if isinstance(statement, ast.If):
                self.visit_elif(statement)
            else:
                self.visit(statement)

    def visit_elif(self, node):
        """Count an elif branch without treating it as deeper nesting."""
        self.if_count += 1
        self.cyclomatic_complexity += 1

        self.visit(node.test)

        for statement in node.body:
            self.visit(statement)

        for statement in node.orelse:
            if isinstance(statement, ast.If):
                self.visit_elif(statement)
            else:
                self.visit(statement)

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
        self.cyclomatic_complexity += len(node.values) - 1
        self.generic_visit(node)

    # ----------------------------------
    # Nes

