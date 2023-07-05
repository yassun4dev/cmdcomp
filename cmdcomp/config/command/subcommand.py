from functools import reduce
from operator import add
from typing import Annotated, NewType, OrderedDict

from pydantic import BaseModel, ConfigDict, Field

from cmdcomp.config.command.option import Options, OptionType, StrOption
from cmdcomp.config.command.option.command_option import CommandOption
from cmdcomp.config.command.option.file_option import FileOption

SubcommandName = NewType("SubcommandName", str)

Candidate = SubcommandName | StrOption
Candidates = list[Candidate] | list[dict[OptionType, str]]

Completions = Candidates | dict[str, "Completions"]  # type: ignore


class Subcommand(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    alias: Annotated[
        str | list[str],
        Field(
            title="alias of the command.",
            default_factory=list,
        ),
    ]

    options: Annotated[
        Options,
        Field(
            title="options of the command.",
            default_factory=list,
        ),
    ]

    subcommands: OrderedDict[SubcommandName, "Subcommand"] = Field(
        title="subcommands of the command.",
        default_factory=OrderedDict,
    )

    @property
    def aliases(self) -> list[str]:
        if isinstance(self.alias, str):
            return [self.alias]
        else:
            return self.alias

    @property
    def candidates(self) -> Candidates:
        return get_candidates(self.subcommands, self.options)


Subcommands = OrderedDict[SubcommandName, Subcommand]


def get_targets(name: SubcommandName, subcommand: Subcommand) -> list[str]:
    return [name] + subcommand.aliases


def get_candidates(
    subcommands: Subcommands, options: Options | None = None
) -> Candidates:
    if options is None:
        return []

    elif isinstance(options, str):
        return [options]

    elif isinstance(options, list):
        return reduce(
            add,
            [get_targets(name, subcommand) for name, subcommand in subcommands.items()],
            [],
        )

    elif isinstance(options, CommandOption):
        command: OptionType = "command"
        return [{command: f"$({options.execute})"}]

    elif isinstance(options, FileOption):
        file: OptionType = "file"
        return [{file: options.base_path}]

    else:
        raise Exception("never reach.")


class SubCommandDefineError(Exception):
    def __init__(
        self,
        subcommands: Subcommands,
        options: Options | None,
    ):
        self.subcommands = subcommands
        self.options = options

    def __str__(self):
        return (
            f"this 'options' and 'subcommand' cannot be used at the same time.\n"
            f"    'options': {self.options}\n"
            f"    'subcommand': {list(self.subcommands.keys())}"
        )


class CommandOptionNotFoundError(Exception):
    def __init__(self, options: Options):
        self._options = options

    def __str__(self):
        return f"Unknown command type: {self._options}"
