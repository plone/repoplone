from rich import print  # noQA: A004
from rich.prompt import Confirm
from rich.table import Table

import textwrap


__all__ = ["print", "table"]


def table(title: str, columns: list[dict], rows: list) -> Table:
    table = Table(title=title)
    for column in columns:
        table.add_column(**column)
    for row in rows:
        table.add_row(*row)
    return table


def indented_print(text: str, prefix: str = "   "):
    print(textwrap.indent(text, prefix))


def confirm(question: str, prefix: str = "   ") -> bool:
    question = textwrap.indent(question, prefix)
    return bool(Confirm.ask(question, default=True))
