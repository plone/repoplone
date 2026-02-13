from rich import print  # noQA: A004
from rich import print_json
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.table import Table

import textwrap


__all__ = ["print", "print_json", "table"]


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


def choice(prompt: str, options: list[dict[str, str]], prefix: str = "") -> str:
    """Prompt the user to choose from several options.

    The first item will be returned if no input happens.

    :param prompt: The prompt message to display to the user
    :param options: Sequence of options that are available to select from
    :param prefix: Prefix to display before the prompt message
    :return: The key for the selected option
    """
    if not options:
        raise ValueError

    choices = []
    choice_map = {}
    choices_text = []
    for idx, option in enumerate(options, start=1):
        for key, value in option.items():
            choices.append(f"{idx}")
            choice_map[str(idx)] = key
            choices_text.append(f"    [bold magenta]{idx}[/] - [bold]{value}[/]")

    prompt = "\n".join((
        f"{prefix}{prompt}",
        "\n".join(choices_text),
        "    Choose from",
    ))

    user_choice = Prompt.ask(prompt, choices=list(choices), default=next(iter(choices)))
    return choice_map[user_choice]
