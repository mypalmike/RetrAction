from enum import Enum, auto

import retraction.ast as ast
from retraction.error import IdentifierError


class EntryType(Enum):
    VAR = auto()
    ROUTINE = auto()
    RECORD = auto()


class Entry:
    def __init__(
        self,
        name: str,
        entry_type: EntryType,
        ast_node: ast.Node | None = None,
    ):
        self.name = name
        self.entry_type = entry_type
        self.ast_node = ast_node


class SymTab:
    def __init__(self):
        self.lookup: dict[str, Entry] = {}
        self.parent: SymTab | None = None

    def add_entry(
        self,
        name: str,
        entry_type: EntryType,
        ast_node: ast.Node,
    ):
        if name in self.lookup:
            raise SyntaxError(f"Symbol {name} already exists in this scope")
        self.lookup[name] = Entry(name, entry_type, ast_node)

    def find(self, name: str) -> Entry:
        entry = self.lookup.get(name)
        if entry is None:
            if self.parent is not None:
                return self.parent.find(name)
            raise IdentifierError(f"Identifier {name} not found")
        return entry
