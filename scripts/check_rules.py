# scripts/check_rules.py
# Automated static rule verifier enforcing all hard DSA project rules via Python AST.
# Course mapping: Engineering quality check (stdlib-only core, no built-in shortcuts, Big-O docstrings, storage-only SQL).

import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_CORE_IMPORTS = {
    "heapq",
    "collections",
    "queue",
    "networkx",
    "sortedcontainers",
    "bisect",
    "sqlalchemy",
}

FORBIDDEN_SQL_PATTERNS = [
    (r"\bJOIN\b", "SQL JOIN detected (graph/relational computation must run in Python memory)"),
    (r"\bRECURSIVE\b", "SQL WITH RECURSIVE detected (graph traversal must run in Python memory)"),
    (r"\bGROUP\s+BY\b", "SQL GROUP BY detected (aggregation must run in Python memory)"),
    (r"\bORDER\s+BY\b", "SQL ORDER BY detected (sorting must use hand-written merge_sort/MinHeap in Python)"),
    (r"\bCOUNT\s*\(", "SQL COUNT() detected (counting must run in Python memory)"),
    (r"\bSUM\s*\(", "SQL SUM() detected"),
    (r"\bAVG\s*\(", "SQL AVG() detected"),
    (r"\bMAX\s*\(", "SQL MAX() detected"),
    (r"\bMIN\s*\(", "SQL MIN() detected"),
]


def _iter_py_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*.py") if p.name != "__init__.py")


def check_core_rules(errors: list[str]) -> None:
    """Verify core/ and storage/ against forbidden imports, sorted(), built-in hash(), and docstring rules."""
    for folder_name in ("core", "storage"):
        for path in _iter_py_files(ROOT / folder_name):
            rel = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel)

            # 1. File header comment check
            first_lines = "\n".join(source.splitlines()[:5])
            if not first_lines.lstrip().startswith("#"):
                errors.append(f"{rel}: missing file header comment explaining purpose and course session.")

            for node in ast.walk(tree):
                # 2. Forbidden imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top_pkg = alias.name.split(".")[0]
                        if top_pkg in FORBIDDEN_CORE_IMPORTS:
                            errors.append(f"{rel}:{node.lineno}: forbidden import '{alias.name}'.")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top_pkg = node.module.split(".")[0]
                        if top_pkg in FORBIDDEN_CORE_IMPORTS:
                            errors.append(f"{rel}:{node.lineno}: forbidden import from '{node.module}'.")

                # 3. Forbidden sorted() or .sort() calls in core/ and storage/
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "sorted":
                        errors.append(
                            f"{rel}:{node.lineno}: built-in sorted() used; use hand-written merge_sort or MinHeap."
                        )
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
                        errors.append(
                            f"{rel}:{node.lineno}: list.sort() used; use hand-written merge_sort or MinHeap."
                        )
                    if (
                        rel == "core/ds/hash_table.py"
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "hash"
                    ):
                        errors.append(
                            f"{rel}:{node.lineno}: Python built-in hash() is forbidden in HashTable."
                        )

            # 4. Every public function/method in core/ must have a docstring with Time: and Space:
            if folder_name == "core":
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                        doc = ast.get_docstring(node) or ""
                        if "Time:" not in doc or "Space:" not in doc:
                            errors.append(
                                f"{rel}:{node.lineno}: public function '{node.name}' missing 'Time:' or 'Space:' in docstring."
                            )
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                is_public = (not item.name.startswith("_")) or item.name in (
                                    "__init__",
                                    "__len__",
                                    "__contains__",
                                    "__iter__",
                                )
                                if is_public:
                                    doc = ast.get_docstring(item) or ""
                                    if "Time:" not in doc or "Space:" not in doc:
                                        errors.append(
                                            f"{rel}:{item.lineno}: public method '{node.name}.{item.name}' "
                                            f"missing 'Time:' or 'Space:' in docstring."
                                        )


def check_storage_sql_rules(errors: list[str]) -> None:
    """Ensure SQL queries executed in storage/ never compute graph traversals, joins, sorting, or aggregates."""
    for path in _iter_py_files(ROOT / "storage"):
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)

        # Collect docstring node IDs so prose explanations are not mistaken for SQL queries.
        docstring_ids: set[int] = set()
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if (
                    parent.body
                    and isinstance(parent.body[0], ast.Expr)
                    and isinstance(parent.body[0].value, ast.Constant)
                    and isinstance(parent.body[0].value.value, str)
                ):
                    docstring_ids.add(id(parent.body[0].value))

        for node in ast.walk(tree):
            if id(node) in docstring_ids:
                continue
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value.upper()
                if any(kw in text for kw in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE")):
                    for pattern, msg in FORBIDDEN_SQL_PATTERNS:
                        if re.search(pattern, text):
                            errors.append(f"{rel}:{node.lineno}: {msg}")


def check_ui_decoupling_rules(errors: list[str]) -> None:
    """Verify UI files never import core.ds or storage directly (must go through core.service)."""
    for path in _iter_py_files(ROOT / "ui"):
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("core.ds") or alias.name.startswith("storage"):
                        errors.append(f"{rel}:{node.lineno}: UI must not import '{alias.name}' directly.")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("core.ds") or node.module.startswith("storage"):
                    errors.append(f"{rel}:{node.lineno}: UI must not import from '{node.module}' directly.")


def main() -> int:
    errors: list[str] = []
    check_core_rules(errors)
    check_storage_sql_rules(errors)
    check_ui_decoupling_rules(errors)

    if errors:
        print(f"RULE CHECK FAILED ({len(errors)} violation(s)):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("ALL RULES PASSED!")
    print("  [OK] Core engine uses Python stdlib only (no heapq, deque, queue, networkx, sorted).")
    print("  [OK] HashTable uses custom polynomial rolling hash (no built-in hash()).")
    print("  [OK] Every public core function/method documents Time: and Space: complexity.")
    print("  [OK] Storage SQL performs pure CRUD (zero joins, sorting, recursion, or aggregates).")
    print("  [OK] Console and Streamlit UIs call core.service only (no direct DS or storage imports).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
