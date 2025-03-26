#!/bin/env python3

from __future__ import annotations

import argparse
import ast
import traceback
from typing import NamedTuple, Sequence

DEBUG_STATEMENTS = {
    "print",
}


class Print(NamedTuple):
    line: int
    col: int
    name: str
    reason: str


class PrintStatementParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.prints: list[Print] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            if isinstance(node.args[0], ast.Constant):
                if node.args[0].value == "INFO":
                    return
            st = Print(node.lineno, node.col_offset, node.func.id, "called")
            self.prints.append(st)
        self.generic_visit(node)


def check_file(filename: str) -> int:
    try:
        with open(filename, "rb") as f:
            ast_obj = ast.parse(f.read(), filename=filename)
    except SyntaxError:
        print(f"{filename} - Could not parse ast")
        print()
        print("\t" + traceback.format_exc().replace("\n", "\n\t"))
        print()
        return 1

    visitor = PrintStatementParser()
    visitor.visit(ast_obj)

    for bp in visitor.prints:
        print(f"{filename}:{bp.line}:{bp.col}: {bp.name} {bp.reason}")

    return int(bool(visitor.prints))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to run")
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        retv |= check_file(filename)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
