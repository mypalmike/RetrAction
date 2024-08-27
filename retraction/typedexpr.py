from enum import Enum, auto

from retraction.bytecode import ByteCodeOp
from retraction.codegen import ByteCodeGen
from retraction.error import InternalError
from retraction.symtab import SymbolTable
from retraction.types import Type, binary_expression_type


class TypedExpressionOp(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MOD = auto()
    LSH = auto()
    RSH = auto()
    EQ = auto()
    NE = auto()
    GT = auto()
    GE = auto()
    LT = auto()
    LE = auto()
    XOR = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()
    UNARY_MINUS = auto()
    CONSTANT = auto()
    LOAD_VARIABLE = auto()
    # VARIABLE_REF = auto()
    # VARIABLE_PTR = auto()
    # GET_GLOBAL = auto()
    # GET_LOCAL = auto()
    # GET_PARAM = auto()
    FUNCTION_CALL = auto()

    def num_operands(self) -> int | None:
        """
        Return the number of operands for the operation.
        None means the number of operands is variable.
        """
        if self in [TypedExpressionOp.CONSTANT, TypedExpressionOp.LOAD_VARIABLE]:
            return 0
        elif self in [TypedExpressionOp.UNARY_MINUS]:
            return 1
        elif self in [TypedExpressionOp.FUNCTION_CALL]:
            return None
        return 2

    def get_bytecode_op(self):
        if self == TypedExpressionOp.ADD:
            return ByteCodeOp.ADD
        elif self == TypedExpressionOp.SUBTRACT:
            return ByteCodeOp.SUBTRACT
        elif self == TypedExpressionOp.MULTIPLY:
            return ByteCodeOp.MULTIPLY
        elif self == TypedExpressionOp.DIVIDE:
            return ByteCodeOp.DIVIDE
        elif self == TypedExpressionOp.MOD:
            return ByteCodeOp.MOD
        elif self == TypedExpressionOp.LSH:
            return ByteCodeOp.LSH
        elif self == TypedExpressionOp.RSH:
            return ByteCodeOp.RSH
        elif self == TypedExpressionOp.EQ:
            return ByteCodeOp.EQ
        elif self == TypedExpressionOp.NE:
            return ByteCodeOp.NE
        elif self == TypedExpressionOp.GT:
            return ByteCodeOp.GT
        elif self == TypedExpressionOp.GE:
            return ByteCodeOp.GE
        elif self == TypedExpressionOp.LT:
            return ByteCodeOp.LT
        elif self == TypedExpressionOp.LE:
            return ByteCodeOp.LE
        elif self == TypedExpressionOp.XOR:
            return ByteCodeOp.XOR
        elif self == TypedExpressionOp.BIT_AND:
            return ByteCodeOp.BIT_AND
        elif self == TypedExpressionOp.BIT_OR:
            return ByteCodeOp.BIT_OR
        elif self == TypedExpressionOp.BIT_XOR:
            return ByteCodeOp.BIT_XOR
        else:
            raise InternalError(f"Unexpected call to get_bytecode_op: {self}")


BINARY_OPS = {
    TypedExpressionOp.ADD,
    TypedExpressionOp.SUBTRACT,
    TypedExpressionOp.MULTIPLY,
    TypedExpressionOp.DIVIDE,
    TypedExpressionOp.MOD,
    TypedExpressionOp.LSH,
    TypedExpressionOp.RSH,
    TypedExpressionOp.EQ,
    TypedExpressionOp.NE,
    TypedExpressionOp.GT,
    TypedExpressionOp.GE,
    TypedExpressionOp.LT,
    TypedExpressionOp.LE,
    TypedExpressionOp.XOR,
    TypedExpressionOp.BIT_AND,
    TypedExpressionOp.BIT_OR,
    TypedExpressionOp.BIT_XOR,
}

RELATIONAL_OPS = {
    TypedExpressionOp.EQ,
    TypedExpressionOp.NE,
    TypedExpressionOp.GT,
    TypedExpressionOp.GE,
    TypedExpressionOp.LT,
    TypedExpressionOp.LE,
}


class TypedExpressionScope(Enum):
    GLOBAL = auto()
    LOCAL = auto()
    PARAM = auto()
    ROUTINE_REFERENCE = auto()


class TypedExpressionItem:
    def __init__(
        self,
        op: TypedExpressionOp,
        index: int | None = None,
    ):
        self.op = op
        # Index is used for constants, variables, and function calls
        self.index = index
        # Members below are computed when the item is added to a TypedPostfixExpression
        self.item_t: Type = None
        # For binary operations
        # self.op1_const = False
        # self.op2_const = False
        self.op1_t: Type = None
        self.op2_t: Type = None
        # For constants
        self.value: int = None
        # For variables
        self.address: int = None
        self.scope: TypedExpressionScope = None
        # Deepest_operand_index is needed for type inference for intermediate expressions.
        self.deepest_operand_index: int | None = None
        # self.is_pointer = False
        # self.is_reference = False

    def __repr__(self):
        return f"TypedExpressionItem - op: {self.op}, index: {self.index}, item_t: {self.item_t}"


class TypedPostfixExpression:
    """
    A postfix expression in the form of a list of TypedExpressionItems.
    This is used as a temporary internal representation to generate bytecode
    for an expression while keeping track of the types of the expression at
    each step. This is necessary to generate the correct bytecode for things
    like adding a BYTE to an INT, particularly when the values are intermediate
    expression results.
    """

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.items: list[TypedExpressionItem] = []

    def append(self, item: TypedExpressionItem):
        op = item.op
        print(f"Appending item: {item}")
        curr_index = len(self.items)
        if op == TypedExpressionOp.UNARY_MINUS:
            # From Action! manual:
            # "NOTE: using the unary minus (negative sign '-') results in
            # an implied INT type"
            item.item_t = Type.INT_T
            item.deepest_operand_index = self.compute_deepest_operand_index(
                curr_index, 1
            )
        # elif op in RELATIONAL_OPS:
        #     # TODO: Should maintain internal boolean type for relational operations?
        #     item.item_t = Type.BYTE_T
        #     item.deepest_operand_index = self.compute_deepest_operand_index(
        #         curr_index, 2
        #     )
        elif op in BINARY_OPS:
            operand2_index = curr_index - 1
            operand1_index = self.compute_deepest_operand_index(curr_index, 1) - 1
            # operand2 = self.items[operand2_index]
            # operand1_index = operand2.deepest_operand_index - 1
            # operand1 = self.items[operand1_index]
            # operand1_index = self.deepest_operand_index(operand2_index) - 1
            print(
                f"Binary op: {op}, operand1_index: {operand1_index}, operand2_index: {operand2_index}"
            )
            item.op1_t = self.items[operand1_index].item_t
            item.op2_t = self.items[operand2_index].item_t
            # From Action! manual:
            # "TECHNICAL NOTE: using the '*', '/' or 'MOD' operand results
            # in an INT type, so processing of very large CARD values (>
            # 32767) will not work properly."
            if op in [
                TypedExpressionOp.MULTIPLY,
                TypedExpressionOp.DIVIDE,
                TypedExpressionOp.MOD,
            ]:
                item.item_t = Type.INT_T
            elif op in RELATIONAL_OPS:
                item.item_t = Type.BYTE_T
            else:
                item.item_t = binary_expression_type(item.op1_t, item.op2_t)
            item.deepest_operand_index = self.compute_deepest_operand_index(
                curr_index, 2
            )
        elif op == TypedExpressionOp.CONSTANT:
            item.value = self.symbol_table.numerical_constants[item.index]
            item.item_t = self.constant_type(item.value)
            item.deepest_operand_index = curr_index
        elif op == TypedExpressionOp.LOAD_VARIABLE:
            scope = item.scope
            if scope == TypedExpressionScope.GLOBAL:
                item.item_t = self.symbol_table.globals[item.index].var_t
                item.address = self.symbol_table.globals[item.index].address
            elif scope == TypedExpressionScope.LOCAL:
                item.item_t = self.symbol_table.locals[item.index].var_t
                item.address = self.symbol_table.locals[item.index].address
            elif scope == TypedExpressionScope.PARAM:
                item.item_t = self.symbol_table.params[item.index].var_t
                item.address = self.symbol_table.params[item.index].address
            elif scope == TypedExpressionScope.ROUTINE_REFERENCE:
                item.item_t = Type.CARD_T
                item.address = self.symbol_table.routines[item.index].address
            else:
                raise InternalError(f"Unknown scope: {scope}")
            item.deepest_operand_index = curr_index
        elif op == TypedExpressionOp.FUNCTION_CALL:
            item.item_t = self.symbol_table.routines[item.index].return_t
            routine = self.symbol_table.routines[item.index]
            n_operands = len(routine.param_ts)
            item.deepest_operand_index = self.compute_deepest_operand_index(
                curr_index, n_operands
            )
        else:
            raise InternalError(f"Unknown operation: {op}")
        self.items.append(item)

    def compute_deepest_operand_index(self, index: int, n_operands: int):
        """
        Compute the deepest operand index for the last n_operands items.
        """
        for _ in range(n_operands):
            index = index - 1
            index = self.items[index].deepest_operand_index
        return index

    # def deepest_operand_index(self, index: int) -> int:
    #     """
    #     Recursively find the deepest (leftmost) operand. Used to determine the type of a binary operation.
    #     e.g. for the stack 1,2,3,+,*, the leftmost operand of + is 2, the leftmost operand of * is 1.
    #     """
    #     if index < 0:
    #         raise InternalError("No operand found for binary operation.")

    #     # Short-circuit if the result is already memoized.
    #     if self.items[index].deepest_operand_index is not None:
    #         return self.items[index].deepest_operand_index

    #     n_operands = self.items[index].op.num_operands()
    #     if n_operands == None:
    #         # Function call. Look up the number of arguments in the routine from the symbol table.
    #         function_item = self.items[index]
    #         function_item_index = function_item.index
    #         routine = self.symbol_table.routines[function_item_index]
    #         n_operands = len(routine.param_ts)
    #     # Recurse to the leftmost operand. This is the heavy lifting of the algorithm.
    #     for _ in range(n_operands):
    #         index = index - 1
    #         index = self.deepest_operand_index(index)

    #     # Memoize the result.
    #     self.items[index].deepest_operand_index = index

    #     return index

    def optimize(self):
        """
        Perform optimizations on the expression, such as constant folding.
        TODO:
        - Move constants to second operand for commutative and comparison operations,
            which is faster on many processors, including 6502.
        - Convert multiplication and division by powers of 2 to shifts.
        - Store followed by load of same variable can be removed.
        """
        curr_index = 0
        while curr_index < len(self.items):
            item = self.items[curr_index]
            op, tipe, _ = item.op, item.item_t, item.index

            if op in BINARY_OPS:
                item1 = self.items[curr_index - 2]
                item2 = self.items[curr_index - 1]
                # tipe1, tipe2 = item1.tipe, item2.tipe
                op1, op2, value1, value2 = item1.op, item2.op, item1.index, item2.index
                # Constant folding
                if (
                    op1 == TypedExpressionOp.CONSTANT
                    and op2 == TypedExpressionOp.CONSTANT
                ):
                    result, tipe = self.fold_constants(op, value1, value2)
                    # Create new constant and shift all following items down to fill in the gap.
                    self.items[curr_index - 2] = TypedExpressionItem(
                        TypedExpressionOp.CONSTANT, tipe, result
                    )
                    self.items[curr_index - 1 :] = self.items[curr_index + 1 :]
                    curr_index -= 2
            elif op == TypedExpressionOp.UNARY_MINUS:
                # Apply unary minus to constant. Many compilers do this during tokenization,
                # but the manual specifies it as a separate operation.
                item1 = self.items[curr_index - 1]
                op1, value1 = item1.op, item1.index

                if op1 == TypedExpressionOp.CONSTANT:
                    result = -value1
                    result = self.constant_normalize(result)
                    tipe = self.constant_type(result)
                    # Create new constant and shift all following items down to fill in the gap.
                    self.items[curr_index - 1] = TypedExpressionItem(
                        TypedExpressionOp.CONSTANT, tipe, result
                    )
                    self.items[curr_index:] = self.items[curr_index + 1 :]
                    curr_index -= 1

    def constant_normalize(self, value: int) -> int:
        if value < -32768 or value >= 65536:
            return value % 65536
        return value

    def constant_type(self, value: int) -> Type:
        if value >= 0 and value < 256:
            return Type.BYTE_T
        elif value >= -32768 and value < 32768:
            return Type.INT_T
        else:
            return Type.CARD_T

    def fold_constants(
        self, op: TypedExpressionOp, value1: int, value2: int
    ) -> tuple[int, Type]:
        if op == TypedExpressionOp.ADD:
            combined_result = value1 + value2
        elif op == TypedExpressionOp.SUBTRACT:
            combined_result = value1 - value2
        elif op == TypedExpressionOp.MULTIPLY:
            combined_result = value1 * value2
        elif op == TypedExpressionOp.DIVIDE:
            combined_result = value1 // value2
        elif op == TypedExpressionOp.MOD:
            combined_result = value1 % value2
        elif op == TypedExpressionOp.LSH:
            combined_result = value1 << value2
        elif op == TypedExpressionOp.RSH:
            combined_result = value1 >> value2
        elif op == TypedExpressionOp.EQ:
            combined_result = 1 if value1 == value2 else 0
        elif op == TypedExpressionOp.NE:
            combined_result = 1 if value1 != value2 else 0
        elif op == TypedExpressionOp.GT:
            combined_result = 1 if value1 > value2 else 0
        elif op == TypedExpressionOp.GE:
            combined_result = 1 if value1 >= value2 else 0
        elif op == TypedExpressionOp.LT:
            combined_result = 1 if value1 < value2 else 0
        elif op == TypedExpressionOp.LE:
            combined_result = 1 if value1 <= value2 else 0
        elif op == TypedExpressionOp.XOR:
            combined_result = int(bool(value1) ^ bool(value2))
        elif op == TypedExpressionOp.BIT_AND:
            combined_result = value1 & value2
        elif op == TypedExpressionOp.BIT_OR:
            combined_result = value1 | value2
        elif op == TypedExpressionOp.BIT_XOR:
            combined_result = value1 ^ value2
        else:
            raise InternalError(f"Unknown operation: {op}")

        # Computed result may be outside of 16-bit range, so normalize it.
        combined_result = self.constant_normalize(combined_result)

        # Select type most appropriate for range of result
        combined_tipe = self.constant_type(combined_result)

        return combined_result, combined_tipe

    def emit_bytecode(self, code_gen: ByteCodeGen):
        for curr_index, item in enumerate(self.items):
            op, item_t, index = item.op, item.item_t, item.index
            if op == TypedExpressionOp.CONSTANT:
                code_gen.emit_numerical_constant(index)
            elif op == TypedExpressionOp.LOAD_VARIABLE:
                if item.scope == TypedExpressionScope.GLOBAL:
                    code_gen.emit_get_global(index)
                elif item.scope == TypedExpressionScope.LOCAL:
                    code_gen.emit_get_local(index, item_t)
                elif item.scope == TypedExpressionScope.PARAM:
                    code_gen.emit_get_param(index, item_t)
                elif item.scope == TypedExpressionScope.ROUTINE_REFERENCE:
                    code_gen.emit_get_routine_reference(index)
            # elif op == TypedExpressionOp.GET_GLOBAL:
            #     code_gen.emit_get_global(index)
            # elif op == TypedExpressionOp.GET_LOCAL:
            #     code_gen.emit_get_local(value, item_t)
            # elif op == TypedExpressionOp.GET_PARAM:
            #     code_gen.emit_get_param(value, item_t)
            elif op == TypedExpressionOp.FUNCTION_CALL:
                code_gen.emit_function_call(index, item_t)
            elif op in BINARY_OPS:
                bytecode_op = op.get_bytecode_op()
                print(
                    f"Emitting bytecode for binary op {op}, {bytecode_op}, {item.op1_t}, {item.op2_t}"
                )
                code_gen.emit_binary_op(bytecode_op, item.op1_t, item.op2_t)

                # op1_tipe, op2_tipe = item.op1_t, item.op2_t
                # op1_const, op2_const = item.op1_const, item.op2_const
                # code_gen.emit_binary_op(
                #     op, item_t, op1_tipe, op2_tipe, op1_const, op2_const
                # )
            elif op == TypedExpressionOp.UNARY_MINUS:
                code_gen.emit_unary_minus(item_t)
