from enum import Enum, auto

from retraction.types import Type, Routine, RecordType


class VariableScope(Enum):
    LOCAL = auto()
    PARAM = auto()
    GLOBAL = auto()


class Variable:
    def __init__(
        self,
        name: str,
        var_t: Type,
        address: int = 0,
        routine_index: int | None = None,
    ):
        self.name = name
        self.var_t = var_t
        self.address = address  # Relative for locals, absolute for globals
        self.routine_index = routine_index

    def get_scope(self):
        raise NotImplementedError("get_scope not implemented for base class Variable")


class Global(Variable):
    """
    Global variable addresses are absolute
    """

    def __init__(self, name: str, var_t: Type, address: int):
        super().__init__(name, var_t, address)

    def get_scope(self):
        return VariableScope.GLOBAL


class Local(Variable):
    """
    Local variable addresses are relative to the routine's local pointer
    i.e. 0-based index
    """

    def __init__(self, name: str, var_tipe: Type, address: int, routine_index: int):
        super().__init__(name, var_tipe, address, routine_index)

    def get_scope(self):
        return VariableScope.LOCAL


class Param(Variable):
    """
    Param variable addresses are relative to the routine's param pointer
    i.e. 0-based index
    """

    def __init__(self, name: str, var_tipe: Type, address: int, routine_index: int):
        super().__init__(name, var_tipe, address, routine_index)

    def get_scope(self):
        return VariableScope.PARAM


class SymbolTable:
    def __init__(self):
        self.constants: list[str | int] = []
        self.globals: list[Global] = []
        self.locals: list[Local] = []
        self.params: list[Param] = []
        self.routines: list[Routine] = []
        self.tipes: list[RecordType] = []
        self.globals_lookup: dict[str, int] = {}
        self.locals_lookup: dict[tuple[int, str], int] = {}
        self.params_lookup: dict[tuple[int, str], int] = {}
        self.routines_lookup: dict[str, int] = {}
        self.tipes_lookup: dict[str, int] = {}

    def symbol_exists(self, name):
        return (
            name in self.globals_lookup
            or name in self.locals_lookup
            or name in self.params_lookup
            or name in self.routines_lookup
            or name in self.tipes_lookup
        )

    def check_symbol(self, name):
        if not self.symbol_exists(name):
            raise ValueError(f"Symbol {name} not found")

    def check_no_symbol(self, name):
        if self.symbol_exists(name):
            raise ValueError(f"Symbol {name} already exists")

    def declare_global(self, name: str, var_tipe: Type, initial_value: int = 0):
        self.check_no_symbol(name)
        next_index = len(self.globals)
        self.globals.append(Global(name, var_tipe, initial_value))
        self.globals_lookup[name] = next_index
        return next_index

    def declare_local(
        self, routine_index: int, name: str, tipe: Type, initial_value: int = 0
    ):
        self.check_no_symbol(name)
        next_index = len(self.locals)
        self.locals.append(Local(routine_index, name, tipe, initial_value))
        self.locals_lookup[(next_index, name)] = next_index
        return next_index

    def declare_param(
        self, routine_index: int, name: str, tipe: Type, initial_value: int = 0
    ):
        self.check_no_symbol(name)
        next_index = len(self.params)
        self.params.append(Param(routine_index, name, tipe, initial_value))
        self.params_lookup[(next_index, name)] = next_index
        return next_index

    def declare_routine(self, routine_signature: Routine):
        self.check_no_symbol(routine_signature.name)
        next_index = len(self.routines)
        self.routines.append(routine_signature)
        self.routines_lookup[routine_signature.name] = next_index
        return next_index

    def declare_tipe(self, record_tipe: RecordType) -> int:
        self.check_no_symbol(record_tipe.name)
        next_index = len(self.tipes)
        self.tipes.append(record_tipe)
        self.tipes_lookup[record_tipe.name] = next_index
        return next_index

    def declare_constant(self, value: str | int):
        index = len(self.constants)
        self.constants.append(value)
        return index
