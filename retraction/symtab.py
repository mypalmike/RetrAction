from enum import Enum, auto
from typing import Self

import retraction.ast as ast
from retraction.error import IdentifierError, InternalError


class Node:
    pass


class EntryType(Enum):
    VAR = auto()
    ROUTINE = auto()
    RECORD = auto()


class Entry:
    def __init__(
        self,
        name: str,
        entry_type: EntryType,
        node: Node | None = None,
    ):
        self.name = name
        self.entry_type = entry_type
        self.node = node


class SymTab:
    def __init__(self, parent: Self | None = None):  # type: ignore
        self.lookup: dict[str, Entry] = {}
        self.parent = parent
        self.depth = 0
        curr_parent = parent
        while curr_parent is not None:
            self.depth += 1
            curr_parent = curr_parent.parent

    def add_entry(
        self,
        name: str,
        entry_type: EntryType,
        node: Node,
    ):
        if name in self.lookup:
            raise SyntaxError(f"Symbol {name} already exists in this scope")
        self.lookup[name] = Entry(name, entry_type, node)

    def find(self, name: str) -> tuple[Entry, int]:
        entry = self.lookup.get(name)
        if entry is None:
            if self.parent is not None:
                return self.parent.find(name)
            raise IdentifierError(f"Identifier {name} not found")
        return entry, self.depth

    def get_last_routine(self) -> Entry:
        for entry in reversed(self.lookup.values()):
            if entry.entry_type == EntryType.ROUTINE:
                return entry
        # if self.parent is not None:
        #     return self.parent.get_last_routine()
        raise InternalError("No routine found in symbol table")
