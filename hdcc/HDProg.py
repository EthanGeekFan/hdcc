from __future__ import annotations
from typing import Union
from . import HDTypes as Types
from enum import Enum




class StatementType(Enum):
    DECL_LOCAL = "DECL_LOCAL"
    DECL_VAR = "DECL_VAR"
    DECL_CONST = "DECL_CONST"
    ASSIGN = "ASSIGN"
    pass


def stringify_statement(stmt: tuple):
    return " ".join([str(x) for x in stmt])


class Operator(Enum):
    BIND = "BIND"
    UNBIND = "UNBIND"
    BUNDlE = "BUNDLE"
    PERMUTATION = "PERMUTATION"
    FRAC_BIND = "FRAC_BIND"

    def support(self, types: list[type]) -> type:
        support_entry = supportted_types[self]
        if self == Operator.BUNDlE:
            # bundle takes variable number of arguments
            for i in range(len(types)):
                if not issubclass(types[i], Types.HyperVector):
                    raise Exception("Unsupported type " + str(types[i]) + " for operator " + str(self))
            return types[0]
        else:
            if len(types) != len(support_entry) - 1:
                raise Exception("Unsupported number of arguments " + str(len(types)) + " for operator " + str(self))
            for i in range(len(types)):
                if not issubclass(types[i], support_entry[i]):
                    raise Exception("Unsupported type " + str(types[i]) + " for operator " + str(self))
            if issubclass(types[0], Types.HyperVector):
                return types[0]
            elif issubclass(types[1], Types.HyperVector):
                return types[1]
            else:
                return support_entry[-1]
    pass


supportted_types = {
    Operator.BIND: ((str, Types.HyperVector), (str, Types.HyperVector), Types.HyperVector),
    Operator.UNBIND: ((str, Types.HyperVector), (str, Types.HyperVector), Types.HyperVector),
    Operator.BUNDlE: ((str, Types.HyperVector), (str, Types.HyperVector), Types.HyperVector),
    Operator.PERMUTATION: ((str, Types.HyperVector), (int), Types.HyperVector),
    Operator.FRAC_BIND: ((str, Types.HyperVector), (str, int, float), Types.HyperVector)
}


class Expression:
    # a: Expression | str | int | float | Types.HyperVector
    # aType: type
    op: Operator
    # b: Expression | str | int | float | Types.HyperVector
    # bType: type
    outType: type
    operands: list[Expression | str | int | float | Types.HyperVector]
    types: list[type]

    def __init__(self, op: Operator, operands: list[Expression | str | int | float | Types.HyperVector], program: HDProg = None):
        self.op = op
        self.operands = operands
        self.types = []
        # parse types
        for i in range(len(operands)):
            if isinstance(operands[i], Expression):
                self.types.append(operands[i].outType)
            elif isinstance(operands[i], str):
                if program is None:
                    raise Exception("Program is required for symbol type inference")
                self.types.append(program.getSymbolType(operands[i]))
            else:
                self.types.append(type(operands[i]))
        self.typecheck()
        pass

    def __str__(self):
        return "Expression(" + str(self.op) + ", " + str(self.operands) + ")"
    
    def typecheck(self):
        self.outType = self.op.support(self.types)
        pass

    def eval(self, state: HDProgState):
        if not self.op == Operator.BUNDlE:
            if isinstance(self.operands[0], Expression):
                self.operands[0] = self.operands[0].eval(state)
            elif isinstance(self.operands[0], str):
                # type check
                if self.operands[0] not in state.val_table:
                    raise Exception("Symbol " + self.operands[0] + " not found")
                if not issubclass(state.val_table[self.operands[0]][1], self.types[0]):
                    raise Exception("Symbol " + self.operands[0] + " is not of type " + str(self.types[0]))
                self.operands[0] = state.val_table[self.operands[0]][3]
            if isinstance(self.operands[1], Expression):
                self.operands[1] = self.operands[1].eval(state)
            elif isinstance(self.operands[1], str):
                # type check
                if self.operands[1] not in state.val_table:
                    raise Exception("Symbol " + self.operands[1] + " not found")
                if not issubclass(state.val_table[self.operands[1]][1], self.types[1]):
                    raise Exception("Symbol " + self.operands[1] + " is not of type " + str(self.types[1]))
                self.operands[1] = state.val_table[self.operands[1]][3]
            if self.op == Operator.BIND:
                return self.operands[0].bind(self.operands[1])
            elif self.op == Operator.UNBIND:
                return self.operands[0].unbind(self.operands[1])
            elif self.op == Operator.PERMUTATION:
                return self.operands[0].permutation(self.operands[1])
            elif self.op == Operator.FRAC_BIND:
                return self.operands[0].frac_bind(self.operands[1])
            else:
                raise Exception("Unsupported operator " + str(self.op))
        else:
            vals = []
            for i in range(len(self.operands)):
                if isinstance(self.operands[i], Expression):
                    vals.append(self.operands[i].eval(state))
                elif isinstance(self.operands[i], str):
                    # type check
                    if self.operands[i] not in state.val_table:
                        raise Exception("Symbol " + self.operands[i] + " not found")
                    if not issubclass(state.val_table[self.operands[i]][1], self.types[i]):
                        raise Exception("Symbol " + self.operands[i] + " is not of type " + str(self.types[i]))
                    vals.append(state.val_table[self.operands[i]][3])
                else:
                    vals.append(self.operands[i])
            return self.outType.bundle(vals)
    pass


Operand = Union[Expression, str, int, float, Types.HyperVector]


# Definition of HDProg class

class HDProgState:
    val_table: dict = {}
    pc = 0

    def __init__(self, val_table: dict = None, pc: int = 0):
        if val_table is not None:
            self.val_table = val_table
        self.pc = pc
        pass
    pass


class HDSymbolType(Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    PARAM = "PARAM"
    LOCAL = "LOCAL"
    VAR = "VAR"
    CONST = "CONST"
    pass


class HDProg:
    # HDProg is a class that represents a HDC program

    def __init__(self):
        self.inputs: dict = {}
        self.outputs: dict = {}
        self.params: dict = {}
        self.local_vars: dict = {}
        self.variables: dict = {}
        self.constants: dict = {}
        self.statements: list = []
        self.symbols: dict = {}
        pass

    def add_symbol(self, sym_type: HDSymbolType, identifier, value):
        if identifier in self.symbols:
            raise Exception("Symbol " + identifier + " already exists")
        self.symbols[identifier] = value
        if sym_type == HDSymbolType.INPUT:
            self.inputs[identifier] = value
        elif sym_type == HDSymbolType.OUTPUT:
            self.outputs[identifier] = value
        elif sym_type == HDSymbolType.PARAM:
            self.params[identifier] = value
        elif sym_type == HDSymbolType.LOCAL:
            self.local_vars[identifier] = value
        elif sym_type == HDSymbolType.VAR:
            self.variables[identifier] = value
        elif sym_type == HDSymbolType.CONST:
            self.constants[identifier] = value
        else:
            raise Exception("Invalid symbol type " + str(sym_type))

    def add_input(self, type: type, identifier, dim: str | int | None=None):
        if isinstance(dim, str):
            p = self.params[dim]
            if not issubclass(p[0], int):
                raise Exception("Invalid type for dimension parameter: " + str(p[0]))
            dim = p[2]
        self.add_symbol(HDSymbolType.INPUT, identifier, (type, dim, None))
        

    def add_output(self, type: type, identifier, dim: str | int | None=None):
        if isinstance(dim, str):
            p = self.params[dim]
            if not issubclass(p[0], int):
                raise Exception("Invalid type for dimension parameter: " + str(p[0]))
            dim = p[2]
        self.add_symbol(HDSymbolType.OUTPUT, identifier, (type, dim, None))

    def add_param(self, type: type, identifier, value):
        self.add_symbol(HDSymbolType.PARAM, identifier, (type, None, value))

    def decl_local(self, type: type, identifier, dim: str | int | None):
        if isinstance(dim, str):
            p = self.params[dim]
            if not issubclass(p[0], int):
                raise Exception("Invalid type for dimension parameter: " + str(p[0]))
            dim = p[2]
        self.statements.append((StatementType.DECL_LOCAL, type, identifier, dim))
        self.add_symbol(HDSymbolType.LOCAL, identifier, (type, dim, None))

    def decl_var(self, type: type, identifier, dim: str | int | None):
        if isinstance(dim, str):
            p = self.params[dim]
            if not issubclass(p[0], int):
                raise Exception("Invalid type for dimension parameter: " + str(p[0]))
            dim = p[2]
        self.statements.append((StatementType.DECL_VAR, type, identifier, dim))
        self.add_symbol(HDSymbolType.VAR, identifier, (type, dim, None))

    def decl_const(self, type: type, identifier, value):
        self.statements.append((StatementType.DECL_CONST, type, identifier, value))
        if isinstance(value, Types.HyperVector):
            self.add_symbol(HDSymbolType.CONST, identifier, (type, value.dim, value))
        else:
            self.add_symbol(HDSymbolType.CONST, identifier, (type, None, value))

    def assign(self, lhs: str, rhs: Union[Expression, str, int, float, Types.HyperVector]):
        rhs_type = type(rhs)
        if rhs_type == Expression:
            rhs_type = rhs.outType
        elif rhs_type == str:
            if rhs not in self.symbols:
                raise Exception("Symbol " + rhs + " not declared")
            rhs_type = self.getSymbolType(rhs)
        if lhs not in self.symbols:
            raise Exception("Symbol " + lhs + " not declared")
        if self.symbols[lhs][0] == HDSymbolType.CONST or self.symbols[lhs][0] == HDSymbolType.INPUT or self.symbols[lhs][0] == HDSymbolType.PARAM:
            raise Exception("Symbol " + lhs + " is read-only")
        lhs_type = self.getSymbolType(lhs)
        if not issubclass(rhs_type, lhs_type):
            raise Exception("Invalid assignment to " + lhs + ": type mismatch. Expected " + str(lhs_type) + " but got " + str(rhs_type) + ".")
        self.statements.append((StatementType.ASSIGN, lhs, rhs))

    def typecheck(self):
        pass

    def build(self) -> HDProgState:
        '''Builds the program into a state object that can be executed by exec(state, *args)'''
        # (symbol_type, data_type, dim, value, declared, initialized, accessible)
        val_table = {}
        for k, v in self.params.items():
            val_table[k] = (HDSymbolType.PARAM, v[0], v[1], v[2], True, True, True)
        for k, v in self.inputs.items():
            val_table[k] = (HDSymbolType.INPUT, v[0], v[1], v[2], True, True, True)
        for k, v in self.constants.items():
            val_table[k] = (HDSymbolType.CONST, v[0], v[1], v[2], False, False, False)
        for k, v in self.local_vars.items():
            val_table[k] = (HDSymbolType.LOCAL, v[0], v[1], v[2], False, False, False)
        for k, v in self.variables.items():
            val_table[k] = (HDSymbolType.VAR, v[0], v[1], v[2], False, False, False)
        for k, v in self.outputs.items():
            val_table[k] = (HDSymbolType.OUTPUT, v[0], v[1], v[2], True, False, True)
        return HDProgState(val_table)

    def init(self, state: HDProgState, *args):
        pass

    def run(self, state: HDProgState, args: dict):
        while state.pc < len(self.statements):
            self.step(state, args)
        return state, *(state.val_table[out][3] for out in self.outputs)
        

    def step(self, state: HDProgState, args: dict):
        # print("PC: " + str(state.pc) + " " + str(self.statements[state.pc]))
        if state.pc == 0:
            # plug in arguments/inputs
            for k in self.inputs.keys():
                if not k in args:
                    raise Exception("Missing input: " + k)
                if not issubclass(type(args[k]), self.inputs[k][0]):
                    raise Exception("Invalid input type for " + k + ": expected " + str(self.inputs[k][0]) + " but got " + str(type(args[k])))
                state.val_table[k] = (HDSymbolType.INPUT, self.inputs[k][0], self.inputs[k][1], args[k], True, True, True)
        stmt = self.statements[state.pc]
        if stmt[0] == StatementType.DECL_CONST:
            # declare constant
            identifier = stmt[2]
            if not identifier in state.val_table:
                raise Exception("Constant " + identifier + " not declared in compile-time")
            if state.val_table[identifier][4] or state.val_table[identifier][5]:
                raise Exception("Constant " + identifier + " already declared")
            state.val_table[identifier] = (HDSymbolType.CONST, stmt[1], state.val_table[identifier][2], stmt[3], True, True, True)
        elif stmt[0] == StatementType.DECL_LOCAL:
            # declare local variable
            identifier = stmt[2]
            if not identifier in state.val_table:
                raise Exception("Local variable " + identifier + " not declared in compile-time")
            if issubclass(stmt[1], Types.HyperVector):
                state.val_table[identifier] = (HDSymbolType.LOCAL, stmt[1], stmt[3], stmt[1](stmt[3]), True, True, True)
            else:
                state.val_table[identifier] = (HDSymbolType.LOCAL, stmt[1], stmt[3], None, True, True, True)
        elif stmt[0] == StatementType.DECL_VAR:
            # declare variable
            identifier = stmt[2]
            if not identifier in state.val_table:
                raise Exception("Variable " + identifier + " not declared in compile-time")
            if issubclass(stmt[1], Types.HyperVector):
                state.val_table[identifier] = (HDSymbolType.VAR, stmt[1], stmt[3], stmt[1](stmt[3]), True, True, True)
            else:
                state.val_table[identifier] = (HDSymbolType.VAR, stmt[1], stmt[3], None, True, True, True)
        elif stmt[0] == StatementType.ASSIGN:
            # assign value to variable
            identifier = stmt[1]
            if not identifier in state.val_table:
                raise Exception("Variable " + identifier + " not declared in compile-time")
            if not state.val_table[identifier][4]:
                raise Exception("Variable " + identifier + " not declared at this point")
            if not state.val_table[identifier][6]:
                raise Exception("Variable " + identifier + " not accessible")
            if isinstance(stmt[2], Expression):
                # evaluate expression
                expr = stmt[2].eval(state)
                if not issubclass(type(expr), state.val_table[identifier][1]):
                    raise Exception("Type mismatch: cannot assign " + str(expr) + " to " + identifier + ". Expected " + str(state.val_table[identifier][1]) + " but got " + str(type(expr)))
                if issubclass(type(expr), Types.HyperVector) and expr.dim != state.val_table[identifier][2]:
                    raise Exception("Dimension mismatch: cannot assign " + str(expr) + " to " + identifier + ". Expected dimension " + str(state.val_table[identifier][2]) + " but got " + str(expr.dim))
                state.val_table[identifier] = (state.val_table[identifier][0], state.val_table[identifier][1], state.val_table[identifier][2], expr, True, True, True)
            elif issubclass(stmt[2], str):
                # typecheck
                if not stmt[2] in state.val_table:
                    raise Exception("Variable " + stmt[2] + " does not exist")
                if not state.val_table[stmt[2]][4]:
                    raise Exception("Variable " + stmt[2] + " not declared at this point")
                if not state.val_table[stmt[2]][5]:
                    raise Exception("Variable " + stmt[2] + " not initialized")
                if not state.val_table[stmt[2]][6]:
                    raise Exception("Variable " + stmt[2] + " not accessible")
                if not issubclass(state.val_table[stmt[2]][1], state.val_table[identifier][1]):
                    raise Exception("Type mismatch: cannot assign " + stmt[2] + " to " + identifier + ". Expected " + str(state.val_table[identifier][1]) + " but got " + str(state.val_table[stmt[2]][1]))
                if not state.val_table[stmt[2]][2] == state.val_table[identifier][2]:
                    raise Exception("Dimension mismatch: cannot assign " + stmt[2] + " to " + identifier + ". Expected " + str(state.val_table[identifier][2]) + " but got " + str(state.val_table[stmt[2]][2]))
                # get variable
                expr = state.val_table[stmt[2]][3]
                state.val_table[identifier] = (state.val_table[identifier][0], state.val_table[identifier][1], state.val_table[identifier][2], expr, True, True, True)
            else:
                # typecheck
                if not isinstance(stmt[2], state.val_table[identifier][1]):
                    raise Exception("Type mismatch: cannot assign " + str(stmt[2]) + " to " + identifier + ". Expected " + str(state.val_table[identifier][1]))
                # get variable
                expr = stmt[2]
                state.val_table[identifier] = (state.val_table[identifier][0], state.val_table[identifier][1], state.val_table[identifier][2], expr, True, True, True)
        else:
            raise Exception("Unknown statement type " + str(stmt[0]))
        state.pc += 1

    def getSymbolType(self, identifier: str) -> type:
        if identifier not in self.symbols:
            raise Exception("Symbol " + identifier + " not declared")
        t = self.symbols[identifier][0]
        assert isinstance(t, type)
        return t
    
    def bind(self, a: Operand, b: Operand) -> Expression:
        return Expression(Operator.BIND, [a, b], self)
    
    def unbind(self, a: Operand, b: Operand) -> Expression:
        return Expression(Operator.UNBIND, [a, b], self)

    def bundle(self, *operands: Operand) -> Expression:
        return Expression(Operator.BUNDlE, list(operands), self)

    def permutation(self, a: Operand, b: Operand) -> Expression:
        return Expression(Operator.PERMUTATION, [a, b], self)

    def frac_bind(self, a: Operand, b: Operand) -> Expression:
        return Expression(Operator.FRAC_BIND, [a, b], self)
        
    def __str__(self):
        string = ""
        string += "Inputs:\n"
        for k, v in self.inputs.items():
            string += f"\t{k}: {v[0]} dim {v[1]}\n"
        string += "Outputs:\n"
        for k, v in self.outputs.items():
            string += f"\t{k}: {v[0]} dim {v[1]}\n"
        string += "Params:\n"
        for k, v in self.params.items():
            string += f"\t{k}: {v[0]} = {v[2]}\n"
        string += "Local Vars:\n"
        for k, v in self.local_vars.items():
            string += f"\t{k}: {v[0]} dim {v[1]}\n"
        string += "Vars:\n"
        for k, v in self.variables.items():
            string += f"\t{k}: {v[0]} dim {v[1]}\n"
        string += "Constants:\n"
        for k, v in self.constants.items():
            string += f"\t{k}: {v[0]} = {v[2]}\n"
        string += "Statements:\n"
        for s in self.statements:
            string += f"\t{stringify_statement(s)}\n"
        return string

