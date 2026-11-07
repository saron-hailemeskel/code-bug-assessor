"""
Unit tests for FeatureExtractor.

Verifies the correctness of the 20 AST numerical features, specifically:
- Nesting depth calculation (including the rule: elif is a decision point, not additional depth).
- Cyclomatic complexity conventions (file-level aggregate metric).
- Error handling on invalid Python syntax.
- Empty files and edge cases.
- Preservation of the 20-feature numerical interface.
"""

from pathlib import Path
import sys
import unittest

# Ensure the src directory is available on Python's module search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from feature_extractor import FeatureExtractor


class TestFeatureExtractorNestingDepth(unittest.TestCase):
    """Tests focused on control-flow nesting depth calculation."""

    def setUp(self):
        self.extractor = FeatureExtractor()

    def test_flat_code_depth(self):
        """Sequential statements without control structures must have depth 0."""
        code = """
a = 1
b = 2
c = a + b
print(c)
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["max_nesting_depth"], 0)

    def test_single_if_depth(self):
        """A single if block has a nesting depth of 1."""
        code = """
if True:
    print("inside")
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["max_nesting_depth"], 1)

    def test_nested_if_depth(self):
        """Consecutively nested if statements increase nesting depth incrementally."""
        code = """
if level_1:
    if level_2:
        if level_3:
            print("deep")
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["max_nesting_depth"], 3)

    def test_if_elif_else_depth(self):
        """
        Rule: elif is an additional decision point, but NOT an additional nesting level.
        An if-elif-else chain at the same level must have max_nesting_depth == 1.
        """
        code = """
if status == 200:
    msg = "OK"
elif status == 404:
    msg = "Not Found"
elif status == 500:
    msg = "Server Error"
else:
    msg = "Unknown"
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["max_nesting_depth"], 1)
        self.assertEqual(features["if_count"], 3)  # if + 2 elifs

    def test_nested_inside_elif(self):
        """An if block inside an elif branch must be at depth 2 (1 for elif + 1 for inner if)."""
        code = """
if a:
    x = 1
elif b:
    if c:
        x = 2
else:
    x = 3
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["max_nesting_depth"], 2)

    def test_nested_inside_else(self):
        """A loop inside an else block must be at depth 2 (1 for else + 1 for loop)."""
        code = """
if a:
    x = 1
else:
    for item in items:
        x += item
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["max_nesting_depth"], 2)

    def test_mixed_control_structures_depth(self):
        """Mixed control flow (try -> with -> for -> if) correctly computes depth."""
        code = """
try:
    with open("data.txt") as f:
        for line in f:
            if line.strip():
                print(line)
except IOError:
    pass
"""
        features = self.extractor.extract(code)
        # try (1) -> with (2) -> for (3) -> if (4)
        self.assertEqual(features["max_nesting_depth"], 4)

    def test_complex_processor_file_depth(self):
        """
        Verifies that data/raw/high/complex_processor.py produces a depth of 6,
        fixing the bug where it previously produced 2.
        """
        file_path = PROJECT_ROOT / "data" / "raw" / "high" / "complex_processor.py"
        if file_path.exists():
            code = file_path.read_text(encoding="utf-8")
            features = self.extractor.extract(code)
            self.assertEqual(features["max_nesting_depth"], 6)


class TestFeatureExtractorCyclomaticComplexity(unittest.TestCase):
    """Tests focused on cyclomatic complexity conventions (file-level aggregate)."""

    def setUp(self):
        self.extractor = FeatureExtractor()

    def test_base_complexity(self):
        """A program with no branches has base cyclomatic complexity of 1."""
        code = """
x = 10
y = 20
z = x + y
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["cyclomatic_complexity"], 1)

    def test_if_elif_else_complexity(self):
        """
        Each if and elif adds 1 to cyclomatic complexity.
        Base 1 + 1 (if) + 1 (elif) = 3. Else does not add an extra path beyond the condition.
        """
        code = """
if a:
    x = 1
elif b:
    x = 2
else:
    x = 3
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["cyclomatic_complexity"], 3)

    def test_loops_complexity(self):
        """For and while loops each add 1 to cyclomatic complexity."""
        code = """
for i in range(10):
    pass
while False:
    pass
"""
        features = self.extractor.extract(code)
        # Base 1 + for (1) + while (1) = 3
        self.assertEqual(features["cyclomatic_complexity"], 3)

    def test_bool_operators_complexity(self):
        """Each boolean operator adds a decision path."""
        code = """
if a and b or c:
    pass
"""
        features = self.extractor.extract(code)
        # Base 1 + if (1) + 2 boolean ops ('and', 'or') = 4
        self.assertEqual(features["cyclomatic_complexity"], 4)
        self.assertEqual(features["boolean_operator_count"], 2)

    def test_ternary_expression_complexity(self):
        """Conditional expression (x if c else y) adds 1 to cyclomatic complexity."""
        code = """
val = "yes" if active else "no"
"""
        features = self.extractor.extract(code)
        # Base 1 + ternary (1) = 2
        self.assertEqual(features["cyclomatic_complexity"], 2)

    def test_except_handler_complexity(self):
        """Each except handler adds 1 to cyclomatic complexity."""
        code = """
try:
    do_something()
except ValueError:
    pass
except KeyError:
    pass
"""
        features = self.extractor.extract(code)
        # Base 1 + 2 except handlers = 3
        self.assertEqual(features["cyclomatic_complexity"], 3)
        self.assertEqual(features["except_count"], 2)


class TestFeatureExtractorEdgeCases(unittest.TestCase):
    """Tests focused on edge cases, syntax errors, and empty files."""

    def setUp(self):
        self.extractor = FeatureExtractor()

    def test_invalid_syntax_returns_error_dict(self):
        """Syntax errors must return an error dict and not raise unhandled exceptions."""
        broken_code = """
def broken(
    print("missing closing paren")
"""
        result = self.extractor.extract(broken_code)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid Python syntax")
        self.assertIn("message", result)
        self.assertIn("line", result)
        self.assertGreater(result["loc"], 0)

    def test_empty_string(self):
        """An empty source string must extract valid zeroed features."""
        features = self.extractor.extract("")
        self.assertEqual(features["loc"], 0)
        self.assertEqual(features["function_count"], 0)
        self.assertEqual(features["max_nesting_depth"], 0)
        self.assertEqual(features["cyclomatic_complexity"], 1)

    def test_whitespace_and_comments_only(self):
        """Comments only should result in LOC > 0 but 0 AST functions or structures."""
        code = """
# Just a comment
# Another comment
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["loc"], 2)
        self.assertEqual(features["function_count"], 0)
        self.assertEqual(features["max_nesting_depth"], 0)

    def test_bare_except_detection(self):
        """Detects bare except: while distinguishing it from except SpecificError:."""
        code = """
try:
    pass
except:
    pass
try:
    pass
except Exception:
    pass
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["except_count"], 2)
        self.assertEqual(features["bare_except_count"], 1)


class TestFeatureExtractorMetricsAndInterface(unittest.TestCase):
    """Tests function metrics, operators, and interface preservation."""

    def setUp(self):
        self.extractor = FeatureExtractor()

    def test_20_features_interface(self):
        """The extractor must return exactly the 20 numerical features."""
        expected_keys = {
            "loc",
            "function_count",
            "class_count",
            "if_count",
            "for_count",
            "while_count",
            "try_count",
            "except_count",
            "import_count",
            "return_count",
            "max_nesting_depth",
            "cyclomatic_complexity",
            "average_function_length",
            "maximum_function_length",
            "total_parameter_count",
            "max_parameters",
            "boolean_operator_count",
            "comparison_operator_count",
            "bare_except_count",
            "global_statement_count",
        }
        features = self.extractor.extract("def f(): pass")
        self.assertEqual(set(features.keys()), expected_keys)
        for key, val in features.items():
            self.assertIsInstance(val, (int, float), f"Feature {key} is not numerical")

    def test_function_lengths_and_parameters(self):
        """Tests function lengths and parameter counting across various signature forms."""
        code = """
def short_fn(a, b=1):
    return a + b

def longer_fn(x, y, *args, kw_only=True, **kwargs):
    step1 = x * 2
    step2 = y * 3
    step3 = step1 + step2
    return step3
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["function_count"], 2)
        self.assertEqual(features["return_count"], 2)
        # short_fn has 2 params; longer_fn has 5 params (x, y, *args, kw_only, **kwargs)
        self.assertEqual(features["total_parameter_count"], 7)
        self.assertEqual(features["max_parameters"], 5)
        self.assertEqual(features["maximum_function_length"], 5)

    def test_comparison_operators(self):
        """Chained comparisons count each comparison operator."""
        code = "valid = (0 < x <= 100 == y != z)"
        features = self.extractor.extract(code)
        # 4 comparison operators: <, <=, ==, !=
        self.assertEqual(features["comparison_operator_count"], 4)

    def test_global_statement_count(self):
        """Counts global statement usage."""
        code = """
def modify():
    global counter
    global state
    counter += 1
"""
        features = self.extractor.extract(code)
        self.assertEqual(features["global_statement_count"], 2)


if __name__ == "__main__":
    unittest.main()
