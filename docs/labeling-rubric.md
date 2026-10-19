# Code Risk Labeling Rubric

## Purpose
This document defines the initial criteria used to categorize Python code examples in the Code Bug & Anti-Pattern Severity Assessor project.

The initial labels represent structural risk categories. They do not establish that a program contains a confirmed bug.

## Labels

### Low
Code with relatively few structural warning signs.

Typical indicators:

- Low cyclomatic complexity.
- Shallow nesting.
- Short, focused functions.
- Few decision branches.

### Medium
Code with some structural concerns that may make maintenance or review more difficult.

Typical indicators:

- Moderate cyclomatic complexity.
- Several decision branches.
- Some nested control flow.
- Functions that handle multiple responsibilities.

### High
Code with substantial structural concerns that deserve closer review.

Typical indicators:

- High cyclomatic complexity.
- Deeply nested control flow.
- Very long functions.
- Excessive branching or multiple interacting control structures.

## Labeling Principles

1. Labels describe structural risk, not confirmed defect severity.
2. High complexity alone does not prove that code is defective.
3. Simple code may still contain serious logical or security bugs.
4. Examples should represent different programming styles and problem types.
5. Labels should be assigned using documented criteria rather than changed merely to improve model accuracy.
6. Examples derived from public repositories should record their source and licensing information.

## Current Limitations
The initial dataset is small and illustrative.

It must not be used to claim that the model can reliably detect bugs or predict real-world defect severity.

A larger, more diverse dataset and independent evaluation are required before drawing conclusions about model performance.
