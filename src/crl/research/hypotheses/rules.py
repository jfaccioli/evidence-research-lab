"""Safe-ish boolean rule evaluation over feature columns.

Only allows: column names, numbers, comparisons, and/or/not, parentheses.
No arbitrary Python eval of user code beyond this restricted grammar.
"""

from __future__ import annotations

import ast
import operator
from typing import Any

import pandas as pd

OPS = {
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


class RuleError(ValueError):
    pass


def _eval_node(node: ast.AST, row: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, row)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_eval_node(v, row) for v in node.values)
        if isinstance(node.op, ast.Or):
            return any(_eval_node(v, row) for v in node.values)
        raise RuleError("Unsupported boolean operator")
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _eval_node(node.operand, row)
        if isinstance(node.op, ast.USub):
            return -_eval_node(node.operand, row)
        if isinstance(node.op, ast.UAdd):
            return +_eval_node(node.operand, row)
        raise RuleError("Unsupported unary operator")
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, row)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval_node(comp, row)
            fn = OPS.get(type(op))
            if fn is None:
                raise RuleError(f"Unsupported compare: {type(op)}")
            if left is None or right is None:
                return False
            try:
                if pd.isna(left) or pd.isna(right):
                    return False
            except TypeError:
                pass
            if not fn(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Name):
        if node.id not in row:
            raise RuleError(f"Unknown feature: {node.id}")
        return row[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    # Python 3.8+ uses Constant; Num removed in 3.14
    if hasattr(ast, "Num") and isinstance(node, ast.Num):  # pragma: no cover
        return node.n
    raise RuleError(f"Unsupported syntax: {type(node)}")


def eval_rule(expression: str, row: dict[str, Any]) -> bool:
    expr = expression.strip()
    if not expr:
        return False
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise RuleError(f"Invalid rule: {expression}") from e
    # Reject function calls, attributes, etc.
    for n in ast.walk(tree):
        if isinstance(n, (ast.Call, ast.Attribute, ast.Subscript, ast.Lambda, ast.ListComp)):
            raise RuleError("Disallowed construct in rule")
    return bool(_eval_node(tree, row))


def eval_rule_series(expression: str, df: pd.DataFrame) -> pd.Series:
    cols = set(df.columns)
    # quick name check
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as e:
        raise RuleError(str(e)) from e
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id not in cols and n.id not in ("True", "False"):
            # True/False are constants in modern ast
            if n.id not in df.columns:
                raise RuleError(f"Unknown feature in rule: {n.id}")
    flags = []
    records = df.to_dict(orient="records")
    for row in records:
        flags.append(eval_rule(expression, row))
    return pd.Series(flags, index=df.index, dtype=bool)
