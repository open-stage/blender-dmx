#!/bin/env python3
# Copyright (C) 2024 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

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
            if node.args and isinstance(node.args[0], ast.Constant):
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
        print("INFO", f"{filename} - Could not parse ast")
        print("INFO")
        print("INFO", "\t" + traceback.format_exc().replace("\n", "\n\t"))
        print("INFO")
        return 1

    visitor = PrintStatementParser()
    visitor.visit(ast_obj)

    for bp in visitor.prints:
        print("INFO", f"{filename}:{bp.line}:{bp.col}: {bp.name} {bp.reason}")

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
