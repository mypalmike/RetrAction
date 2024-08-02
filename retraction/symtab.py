from retraction.tipes import RecordTipe, Tipe, RoutineSignature


class SymbolTable:
    def __init__(self):
        self.constants: list[str | int] = []
        self.globals: list[tuple[str, Tipe]] = []
        self.locals: list[tuple[int, str, Tipe]] = []
        self.routines = list[RoutineSignature]
        self.types: list[RecordTipe] = []
        self.globals_lookup: dict[str, int] = {}
        self.locals_lookup: dict[str, int] = {}
        self.routines_lookup: dict[str, int] = {}
        self.types_lookup: dict[str, int] = {}

    def symbol_exists(self, name):
        return (
            name in self.globals_lookup
            or name in self.locals_lookup
            or name in self.routines_lookup
            or name in self.types_lookup
        )

    def check_symbol(self, name):
        if not self.symbol_exists(name):
            raise ValueError(f"Symbol {name} not found")

    def check_no_symbol(self, name):
        if self.symbol_exists(name):
            raise ValueError(f"Symbol {name} already exists")

    def declare_global(self, name: str, var_type: Tipe):
        self.check_no_symbol(name)
        next_index = len(self.globals)
        self.globals.append((name, var_type))
        self.globals_lookup[name] = next_index
        return next_index

    def declare_local(self, routine_index: int, name: str, type: Tipe):
        self.check_no_symbol(name)
        next_index = len(self.locals)
        self.locals.append((routine_index, name, type))
        self.locals_lookup[name] = next_index
        return next_index

    def declare_routine(self, name, routine: RoutineSignature):
        self.check_no_symbol(name)
        next_index = len(self.routines)
        self.routines.append(routine)
        self.routines_lookup[name] = next_index
        return next_index

    def declare_type(self, record_type: RecordTipe) -> int:
        self.check_no_symbol(record_type.name)
        next_index = len(self.types)
        self.types.append(record_type)
        self.types_lookup[record_type.name] = next_index
        return next_index

    def declare_constant(self, value: str | int):
        index = len(self.constants)
        self.constants.append(value)
        return index
