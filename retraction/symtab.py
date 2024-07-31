from enum import Enum


class EntryType(Enum):
    GLOBAL = 1
    LOCAL = 2
    RECORD_TYPE = 3


class TableEntry:
    def __init__(self, entry_type: EntryType):
        self.entry_type = entry_type


class Variable(TableEntry):
    def __init__(self, entry_type: EntryType, type_name: str, value: str | None = None):
        super(TableEntry, self).__init__(entry_type)
        self.type_name = type_name
        self.value = value


class RecordType(TableEntry):
    def __init__(self):
        super(TableEntry, self).__init__(EntryType.RECORD_TYPE)
        self.fields: dict[str, tuple[str, int]] = {}

    def add_field(self, name: str, field_type: str, offset: int):
        self.fields[name] = (field_type, offset)


class SymTab:
    def __init__(self):
        self.globals: dict[str, Variable | RecordType] = {}
        self.locals: dict[str, Variable] = {}

    def declare_global(self, name: str, variable: Variable):
        if name in self.globals:
            raise ValueError(f"Duplicate name {name}")
        self.globals[name] = variable

    def set_global(self, name: str, variable: Variable):
        if name not in self.globals:
            raise ValueError(f"Variable {name} not found in globals")
        self.globals[name] = variable

    def get_global(self, name) -> Variable:
        return self.globals.get(name)

    def declare_record_type(self, name: str, record_type: RecordType):
        if name in self.globals:
            raise ValueError(f"Duplicate name {name}")
        self.globals[name] = record_type

    def get_record_type(self, name: str) -> RecordType:
        return self.globals.get(name)

    def set_record_type(self, name: str, record_type: RecordType):
        if name not in self.globals:
            raise ValueError(f"Record type {name} not found in globals")
        self.globals[name] = record_type
