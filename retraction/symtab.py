from enum import Enum, auto

from retraction.types import Type, Routine, RecordType


class VariableScope(Enum):
    LOCAL = auto()
    PARAM = auto()
    GLOBAL = auto()


class InitOpts:
    def __init__(self, initial_value: int = 0, is_address: bool = False):
        self.initial_value = initial_value
        self.is_address = is_address


class Variable:
    def __init__(
        self,
        name: str,
        var_t: Type,
        init_opts: InitOpts,
        address: int = 0,
        routine_index: int | None = None,
    ):
        self.name = name
        self.var_t = var_t
        self.init_opts = init_opts
        self.address = address  # Relative for locals, absolute for globals
        self.routine_index = routine_index

    def get_scope(self):
        raise NotImplementedError("get_scope not implemented for base class Variable")


class Global(Variable):
    """
    Global variable addresses are absolute
    """

    # def __init__(self, name: str, var_t: Type, initial_value: intaddress: int):
    #     super().__init__(name, var_t, address)

    def get_scope(self):
        return VariableScope.GLOBAL


class Local(Variable):
    """
    Local variable addresses are relative to the routine's local pointer
    i.e. 0-based index
    """

    # def __init__(
    #     self,
    #     name: str,
    #     var_t: Type,
    #     initial_value: int,
    #     address: int,
    #     routine_index: int,
    # ):
    #     super().__init__(name, var_t, address, routine_index)

    def get_scope(self):
        return VariableScope.LOCAL


class Param(Variable):
    """
    Param variable addresses are relative to the routine's param pointer
    i.e. 0-based index
    """

    # def __init__(self, name: str, var_t: Type, address: int, routine_index: int):
    #     super().__init__(name, var_t, address, routine_index)

    def get_scope(self):
        return VariableScope.PARAM


class SymbolTable:
    def __init__(self):
        self.numerical_constants: list[int] = []
        self.string_constants: list[str] = []
        self.globals: list[Global] = []
        self.locals: list[Local] = []
        self.params: list[Param] = []
        self.routines: list[Routine] = []
        self.record_types: list[RecordType] = []
        self.globals_lookup: dict[str, int] = {}
        self.locals_lookup: dict[tuple[int, str], int] = {}
        self.params_lookup: dict[tuple[int, str], int] = {}
        self.routines_lookup: dict[str, int] = {}
        self.record_types_lookup: dict[str, int] = {}

    def symbol_exists(self, name):
        return (
            name in self.globals_lookup
            or name in self.locals_lookup
            or name in self.params_lookup
            or name in self.routines_lookup
            or name in self.record_types_lookup
        )

    def check_symbol(self, name):
        if not self.symbol_exists(name):
            raise ValueError(f"Symbol {name} not found")

    def check_no_symbol(self, name):
        if self.symbol_exists(name):
            raise ValueError(f"Symbol {name} already exists")

    def declare_global(self, name: str, var_t: Type, init_opts: InitOpts):
        self.check_no_symbol(name)
        next_index = len(self.globals)
        self.globals.append(Global(name, var_t, init_opts))
        self.globals_lookup[name] = next_index
        return next_index

    def declare_local(
        self, routine_index: int, name: str, local_t: Type, init_opts: InitOpts
    ):
        self.check_no_symbol(name)
        next_index = len(self.locals)
        self.locals.append(Local(name, local_t, init_opts, routine_index))
        self.locals_lookup[(next_index, name)] = next_index
        return next_index

    def declare_param(
        self, routine_index: int, name: str, param_t: Type, init_opts: InitOpts
    ):
        self.check_no_symbol(name)
        next_index = len(self.params)
        self.params.append(Param(name, param_t, init_opts, routine_index))
        self.params_lookup[(next_index, name)] = next_index
        return next_index

    def declare_routine(self, routine_signature: Routine):
        self.check_no_symbol(routine_signature.name)
        next_index = len(self.routines)
        self.routines.append(routine_signature)
        self.routines_lookup[routine_signature.name] = next_index
        return next_index

    def declare_record_type(self, record_t: RecordType) -> int:
        self.check_no_symbol(record_t.name)
        next_index = len(self.record_types)
        self.record_types.append(record_t)
        self.record_types_lookup[record_t.name] = next_index
        return next_index

    def declare_constant(self, value: str | int):
        index = len(self.numerical_constants)
        self.numerical_constants.append(value)
        return index
