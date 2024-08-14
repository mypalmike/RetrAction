from retraction.tipes import RecordTipe, Tipe, Routine


class Global:
    def __init__(self, name: str, var_tipe: Tipe, value: int = 0):
        self.name = name
        self.var_tipe = var_tipe
        self.value = value


class Local:
    def __init__(self, routine_index: int, name: str, var_tipe: Tipe, value: int = 0):
        self.routine_index = routine_index
        self.name = name
        self.var_tipe = var_tipe
        self.value = value


class SymbolTable:
    def __init__(self):
        self.constants: list[str | int] = []
        self.globals: list[Global] = []
        self.locals: list[Local] = []
        self.routines: list[Routine] = []
        self.tipes: list[RecordTipe] = []
        self.globals_lookup: dict[str, int] = {}
        self.locals_lookup: dict[str, int] = {}
        self.routines_lookup: dict[str, int] = {}
        self.tipes_lookup: dict[str, int] = {}

    def symbol_exists(self, name):
        return (
            name in self.globals_lookup
            or name in self.locals_lookup
            or name in self.routines_lookup
            or name in self.tipes_lookup
        )

    def check_symbol(self, name):
        if not self.symbol_exists(name):
            raise ValueError(f"Symbol {name} not found")

    def check_no_symbol(self, name):
        if self.symbol_exists(name):
            raise ValueError(f"Symbol {name} already exists")

    def declare_global(self, name: str, var_tipe: Tipe, initial_value: int = 0):
        self.check_no_symbol(name)
        next_index = len(self.globals)
        self.globals.append(Global(name, var_tipe, initial_value))
        self.globals_lookup[name] = next_index
        return next_index

    def declare_local(
        self, routine_index: int, name: str, tipe: Tipe, initial_value: int = 0
    ):
        self.check_no_symbol(name)
        next_index = len(self.locals)
        self.locals.append(Local(routine_index, name, tipe, initial_value))
        self.locals_lookup[name] = next_index
        return next_index

    def declare_routine(self, routine_signature: Routine):
        self.check_no_symbol(routine_signature.name)
        next_index = len(self.routines)
        self.routines.append(routine_signature)
        self.routines_lookup[routine_signature.name] = next_index
        return next_index

    def declare_tipe(self, record_tipe: RecordTipe) -> int:
        self.check_no_symbol(record_tipe.name)
        next_index = len(self.tipes)
        self.tipes.append(record_tipe)
        self.tipes_lookup[record_tipe.name] = next_index
        return next_index

    def declare_constant(self, value: str | int):
        index = len(self.constants)
        self.constants.append(value)
        return index
