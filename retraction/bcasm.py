from functools import partial
from typing import Callable

from retraction.bytecode import (
    ByteCodeOp,
    ByteCodeVariableAddressMode,
    ByteCodeVariableScope,
)
from retraction.types import FundamentalType

disasm_type = {
    FundamentalType.BYTE_T: "BYTE",
    FundamentalType.INT_T: "INT",
    FundamentalType.CARD_T: "CARD",
    FundamentalType.VOID_T: "VOID",
}

disasm_scope = {
    ByteCodeVariableScope.GLOBAL: "GLB",
    ByteCodeVariableScope.LOCAL: "LOC",
    ByteCodeVariableScope.PARAM: "PRM",
    ByteCodeVariableScope.ROUTINE_REFERENCE: "RTR",
}

disasm_addr_mode = {
    ByteCodeVariableAddressMode.DEFAULT: "DEF",
    ByteCodeVariableAddressMode.POINTER: "PTR",
    ByteCodeVariableAddressMode.REFERENCE: "REF",
    ByteCodeVariableAddressMode.OFFSET: "OFF",
}


def disasm_binary_op(op: str, data: bytes) -> tuple[str, int]:
    operand1_t = FundamentalType(data[1])
    operand2_t = FundamentalType(data[2])
    return f"{op} {disasm_type[operand1_t]} {disasm_type[operand2_t]}", 3


def disasm_break(data: bytes) -> tuple[str, int]:
    return "BREAK", 1


disasm_add = partial(disasm_binary_op, "ADD")
disasm_subtract = partial(disasm_binary_op, "SUB")
disasm_multiply = partial(disasm_binary_op, "MUL")
disasm_divide = partial(disasm_binary_op, "DIV")
disasm_mod = partial(disasm_binary_op, "MOD")
disasm_lsh = partial(disasm_binary_op, "LSH")
disasm_rsh = partial(disasm_binary_op, "RSH")
disasm_eq = partial(disasm_binary_op, "EQ")
disasm_ne = partial(disasm_binary_op, "NE")
disasm_gt = partial(disasm_binary_op, "GT")
disasm_ge = partial(disasm_binary_op, "GE")
disasm_lt = partial(disasm_binary_op, "LT")
disasm_le = partial(disasm_binary_op, "LE")
disasm_xor = partial(disasm_binary_op, "XOR")
disasm_bit_and = partial(disasm_binary_op, "AND")
disasm_bit_or = partial(disasm_binary_op, "OR")
disasm_bit_xor = partial(disasm_binary_op, "BXR")


def disasm_unary_minus(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    return f"NEG {disasm_type[operand_t]}", 2


def disasm_jump_if_false(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    addr = int.from_bytes(data[2:4], "little", signed=False)
    return f"JMPF {disasm_type[operand_t]} {addr}", 4


def disasm_jump(data: bytes) -> tuple[str, int]:
    addr = int.from_bytes(data[1:3], "little", signed=False)
    return f"JMP {addr}", 3


def disasm_dup(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    return f"DUP {disasm_type[operand_t]}", 2


def disasm_pop(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    return f"POP {disasm_type[operand_t]}", 2


def disasm_numerical_constant(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    size = 2
    value = -1
    if operand_t == FundamentalType.BYTE_T:
        value = data[2]
        size += 1
    elif operand_t == FundamentalType.INT_T:
        value = int.from_bytes(data[2:4], "little", signed=True)
        size += 2
    elif operand_t == FundamentalType.CARD_T:
        value = int.from_bytes(data[2:4], "little", signed=False)
        size += 2

    # value = int.from_bytes(value, "little", signed=True)
    return f"CONST {disasm_type[operand_t]} {value}", size


def disasm_load_variable(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    scope = ByteCodeVariableScope(data[2])
    addr_mode = ByteCodeVariableAddressMode(data[3])
    addr = int.from_bytes(data[4:6], "little", signed=False)
    return (
        f"LOAD {disasm_type[operand_t]} {disasm_scope[scope]} {disasm_addr_mode[addr_mode]} {addr}",
        6,
    )


def disasm_store_variable(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    scope = ByteCodeVariableScope(data[2])
    addr_mode = ByteCodeVariableAddressMode(data[3])
    addr = int.from_bytes(data[4:6], "little", signed=False)
    return (
        f"STORE {disasm_type[operand_t]} {disasm_scope[scope]} {disasm_addr_mode[addr_mode]} {addr}",
        6,
    )


def disasm_routine_call(data: bytes) -> tuple[str, int]:
    return_t = FundamentalType(data[1])
    locals_size = int.from_bytes(data[2:4], "little", signed=False)
    addr = int.from_bytes(data[4:6], "little", signed=False)
    return f"CALL {disasm_type[return_t]} {locals_size} {addr}", 6


def disasm_routine_postlude(data: bytes) -> tuple[str, int]:
    return_t = FundamentalType(data[1])
    param_bytes = int.from_bytes(data[2:4], "little", signed=False)
    return f"POST {disasm_type[return_t]} {param_bytes}", 4


def disasm_return(data: bytes) -> tuple[str, int]:
    return_t = FundamentalType(data[1])
    return f"RET {disasm_type[return_t]}", 2


def disasm_cast(data: bytes) -> tuple[str, int]:
    from_t = FundamentalType(data[1])
    to_t = FundamentalType(data[2])
    return f"CAST {disasm_type[from_t]} {disasm_type[to_t]}", 3


def disasm_nop(data: bytes) -> tuple[str, int]:
    return "NOP", 1


def disasm_devprint(data: bytes) -> tuple[str, int]:
    operand_t = FundamentalType(data[1])
    return f"DEVPRINT {disasm_type[operand_t]}", 2


BC_TO_DISASM_FN: dict[ByteCodeOp, Callable[[bytes], tuple[str, int]]] = {
    ByteCodeOp.BREAK: disasm_break,
    ByteCodeOp.ADD: disasm_add,
    ByteCodeOp.SUBTRACT: disasm_subtract,
    ByteCodeOp.MULTIPLY: disasm_multiply,
    ByteCodeOp.DIVIDE: disasm_divide,
    ByteCodeOp.MOD: disasm_mod,
    ByteCodeOp.LSH: disasm_lsh,
    ByteCodeOp.RSH: disasm_rsh,
    ByteCodeOp.EQ: disasm_eq,
    ByteCodeOp.NE: disasm_ne,
    ByteCodeOp.GT: disasm_gt,
    ByteCodeOp.GE: disasm_ge,
    ByteCodeOp.LT: disasm_lt,
    ByteCodeOp.LE: disasm_le,
    ByteCodeOp.XOR: disasm_xor,
    ByteCodeOp.BIT_AND: disasm_bit_and,
    ByteCodeOp.BIT_OR: disasm_bit_or,
    ByteCodeOp.BIT_XOR: disasm_bit_xor,
    ByteCodeOp.UNARY_MINUS: disasm_unary_minus,
    ByteCodeOp.JUMP_IF_FALSE: disasm_jump_if_false,
    ByteCodeOp.JUMP: disasm_jump,
    ByteCodeOp.DUP: disasm_dup,
    ByteCodeOp.POP: disasm_pop,
    ByteCodeOp.NUMERICAL_CONSTANT: disasm_numerical_constant,
    ByteCodeOp.LOAD_VARIABLE: disasm_load_variable,
    ByteCodeOp.STORE_VARIABLE: disasm_store_variable,
    ByteCodeOp.ROUTINE_CALL: disasm_routine_call,
    ByteCodeOp.ROUTINE_POSTLUDE: disasm_routine_postlude,
    ByteCodeOp.RETURN: disasm_return,
    ByteCodeOp.CAST: disasm_cast,
    ByteCodeOp.NOP: disasm_nop,
    ByteCodeOp.DEVPRINT: disasm_devprint,
}


def disasm_bytecode(data: bytes) -> tuple[str, int]:
    op = ByteCodeOp(data[0])
    return BC_TO_DISASM_FN[op](data)
