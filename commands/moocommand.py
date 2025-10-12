import shlex
from evennia.commands.command import Command as BaseCommand
from optparse import OptionParser, Option
from world.utils.ordinalparser import OrdinalParser


class Command(BaseCommand):
    """
    A hybrid Evennia command class that emulates LambdaMOO-style parsing
    while supporting traditional command-line options.

    This command parser provides flexible input handling similar to LambdaMOO's
    native command parser, where user input is split into direct and indirect
    objects (dobject/iobject) with an optional preposition. For example:

    > put shotgun on 2nd rack

    In addition, this implementation extends standard MOO parsing with
    UNIX-like option flags (e.g. `--debug`, `--verbose`, `--limit=10`),
    allowing commands to behave more like traditional shell utilities,
    and ordinal parsing for the smooth handling of multiple objects
    with similar names.

    ---
    **Parsing Flow**

    1. The full command string is split into arguments via `shlex.split`
       to respect quoted arguments (e.g. `take 'red book'`).
    2. It extracts any CLI-style flags defined in `self.options` or
       dynamically injected by subclasses.
    3. The command string is then analyzed for prepositions (e.g. from, on,
       in) to separate the direct and indirect object strings.
    4. Both dobject and iobject strings are resolved into actual in-game objects
       via `get_object()`, which uses the `OrdinalParser` to support
       ordinal-based object references such as:
           - "first shotgun"
           - "2nd grenade"
           - "last painkiller"
    5. Parsed information is stored in `self.info`, a debug-friendly list
       of tuples representing each parsed component.

    ---
    **Properties**

        - `op`: The command operator (typically `self.caller`).
        - `args`: List of argument tokens from the input string.
        - `argstring`: The raw argument string after parsing.
        - `parser`: `OptionParser` instance for CLI-style flags.
        - `options`: Namespace of parsed options and their values.
        - `prepstring`: The preposition (if any) separating dobject/iobject.
        - `dobjstring` / `iobjstring`: The raw strings for direct and indirect
          objects before resolution.
        - `dobject` / `iobject`: The resolved Evennia objects.
        - `info`: A structured collection of parsed and resolved data,
          primarily used for debugging.

    ---
    **Example Usage**

    > count --debug corpse
    [DEBUG] OPERATOR <class 'typeclasses.characters.Character'> => Kreator
    [DEBUG] CMDSTRING <class 'str'> => count
    [DEBUG] ALIASES <class 'str'> =>
    [DEBUG] ARGSTRING <class 'str'> => corpse
    [DEBUG] ARGS <class 'list'> => ['corpse']
    [DEBUG] PREPSTRING <class 'str'> =>
    [DEBUG] DOBJSTRING <class 'str'> => corpse
    [DEBUG] DOBJECT <class 'typeclasses.corpse.Corpse'> => fresh corpse
    [DEBUG] IOBJSTRING <class 'str'> =>
    [DEBUG] IOBJECT <class 'NoneType'> => None
    [DEBUG] DEBUG <class 'bool'> => True
    You count 28 'corpse'
      first                            decomposing remains
      second                           decomposing remains
      third                            decomposing remains
      fourth                           decomposing remains
      fifth                            decomposing remains
      sixth                            decomposing remains
      seventh                          decomposing remains
      eighth                           decomposing remains
      ninth                            decomposing remains
      tenth                            decomposing remains
      ...

    ---
    **Extending the Command**

    Subclasses can define additional CLI flags by appending to
    `self.options` before `super().__init__()` is called, e.g.:

    class MyCommand(Command):
        options = [
            Option("-v", "--verbose", action="store_true", dest="verbose"),
            Option("--limit", type="int", dest="limit", default=10),
        ]

    This design enables MOO-style contextual object parsing and CLI-style
    flag parsing to coexist in the same command handler.
    """

    op = None
    args = []
    dobject = None
    iobject = None
    argstring = ""
    dobjstring = ""
    iobjstring = ""
    prepstring = ""
    parser = None
    options = []
    info = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ordinal_parser = OrdinalParser()
        self.parser = OptionParser(prog=self.key)
        self.parser.add_options([
            Option("--debug", action="store_true", dest="debug"),
            *self.options,
        ])

    def get_object(self, string):
        ordinal, obj = self.ordinal_parser.parse(string)
        candidates = self.op.search(obj, quiet=True)

        if not candidates:
            return None

        if ordinal:
            position = ordinal - 1 if ordinal > 0 else ordinal
            position = max(-len(candidates), min(position, len(candidates) - 1))
            return candidates[position]
        else:
            return candidates[0]

    def parse(self):
        self.op = self.caller
        self.argstring = self.args.strip()
        self.args = shlex.split(self.argstring)

        if self.parser:
            options, args = self.parser.parse_args(self.args)

            self.args = args
            self.argstring = shlex.join(args)
            self.options = options

        if self.prepstring and self.prepstring in self.argstring:
            if self.prepstring in self.args[0]:
                self.iobjstring = shlex.join(self.args[1:])
            else:
                position = self.args.index(self.prepstring)
                self.dobjstring = shlex.join(self.args[:position])
                self.iobjstring = shlex.join(self.args[position + 1:])
        else:
            self.dobjstring = shlex.join(self.args)

        if self.dobjstring:
            self.dobject = self.get_object(self.dobjstring)

        if self.iobjstring:
            self.iobject = self.get_object(self.iobjstring)

        self.info = [
            ("operator", self.op),
            ("cmdstring", self.cmdstring),
            ("aliases", "; ".join(self.aliases)),
            ("argstring", self.argstring),
            ("args", self.args),
            ("prepstring", self.prepstring),
            ("dobjstring", self.dobjstring),
            ("dobject", self.dobject),
            ("iobjstring", self.iobjstring),
            ("iobject", self.iobject),
        ]

        if self.options:
            self.info = [
                *self.info,
                *[(attr, value) for attr, value in vars(self.options).items()],
            ]

            if self.options.debug:
                for option, value in self.info:
                    self.msg(f"|Y[DEBUG]|n |r{option.upper()}|n |C{type(value)}|n |Y=>|n |w{value}|n")
