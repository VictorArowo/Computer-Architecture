"""CPU functionality."""
import sys
import time
from select import select

ADD = 0b10100000
AND = 0B10101000
CALL = 0b01010000
CMP = 0b10100111
HLT = 0b00000001
IRET = 0b00010011
JEQ = 0b01010101
JGE = 0b01011010
JGT = 0b01010111
JLE = 0b01011001
JLT = 0b01011000
JMP = 0b01010100
JNE = 0b01010110
LD = 0b10000011
LDI = 0b10000010
MOD = 0b10100100
MUL = 0b10100010
NOT = 0b01101001
OR = 0b10101010
POP = 0b01000110
PRN = 0b01000111
PRA = 0b01001000
PUSH = 0b01000101
RET = 0b00010001
SHL = 0b10101100
SHR = 0b10101101
ST = 0b10000100
XOR = 0b10101011


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""

        self.ram = bytearray(256)

        self.running = True

        # General Registers
        self.reg = bytearray(8)
        self.reg[7] = 0xF4  # SP

        # Internal Registers
        self.PC = 0
        self.IR = None
        self.MAR = None
        self.MDR = None
        self.FL = 0x00

        self.branchtable = {
            MUL: self.op_mul,
            LDI: self.op_ldi,
            HLT: self.op_hlt,
            PRN: self.op_prn,
            POP: self.op_pop,
            PUSH: self.op_push,
            CALL: self.op_call,
            RET: self.op_ret,
            ADD: self.op_add,
            ST: self.op_st,
            JMP: self.op_jmp,
            PRA: self.op_pra,
            IRET: self.op_iret,
            LD: self.op_ld,
            CMP: self.op_cmp,
            JEQ: self.op_jeq,
            JGE: self.op_jge,
            JGT: self.op_jgt,
            JLE: self.op_jle,
            JLT: self.op_jlt,
            JNE: self.op_jne,
            AND: self.op_and,
            OR: self.op_or,
            XOR: self.op_xor,
            NOT: self.op_not,
            SHL: self.op_shl,
            SHR: self.op_shr,
            MOD: self.op_mod
        }

    def ram_read(self, address):
        self.MAR = address
        self.MDR = self.ram[self.MAR]
        return self.MDR

    def ram_write(self, address, value):
        self.MAR = address
        self.MDR = value
        self.ram[self.MAR] = self.MDR

    def run(self):
        interrupt_time = time.time()
        while self.running:
            # Keyboard Interrupts
            i, _, _ = select([sys.stdin], [], [], 0)
            for s in i:
                if s == sys.stdin:
                    input = sys.stdin.readline()
                    self.ram_write(0xF4, ord(input.strip()))
                    self.reg[6] = self.reg[6] | 0b00000010

            # Timer Interrupts
            current_time = time.time()

            if current_time - interrupt_time >= 1:
                self.reg[6] = self.reg[6] | 0b00000001
                interrupt_time = current_time

            masked_interrupts = self.reg[5] & self.reg[6]

            for i in range(8):
                interrupt_happened = ((masked_interrupts >> i) & 1) == 1
                if interrupt_happened:
                    self.reg[6] = self.reg[6] & int(
                        '1' * (7 - i) + '0' + '1' * (i), 2)

                    self.reg[7] -= 1
                    self.ram_write(self.reg[7], self.PC)

                    self.reg[7] -= 1
                    self.ram_write(self.reg[7], self.FL)

                    self.FL = 0
                    for j in range(7):
                        self.op_push(j)
                        self.reg[j] = 0
                    interrupt_vector = 0xF8 + i
                    self.PC = self.ram[interrupt_vector]

            self.IR = self.ram_read(self.PC)
            operand_a = self.ram_read(self.PC + 1)
            operand_b = self.ram_read(self.PC + 2)

            operand_count = self.IR >> 6
            is_pc_setter = self.IR >> 4 & 0b00000001

            if operand_count == 2:
                self.branchtable[self.IR](operand_a, operand_b)
            elif operand_count == 1:
                self.branchtable[self.IR](operand_a)
            else:
                self.branchtable[self.IR]()

            if is_pc_setter == 0:
                self.PC += operand_count + 1

    def load(self):
        """Load a program into memory."""
        print(sys.argv)
        if len(sys.argv) != 2:
            print("usage: ls8.py filename")
            sys.exit(1)
        try:
            address = 0
            with open(sys.argv[1]) as f:
                for line in f:
                    comment_split = line.split("#")

                    num = comment_split[0].strip()

                    if num == '':
                        continue

                    val = int(num, 2)

                    self.ram[address] = val

                    address += 1

        except FileNotFoundError:
            print(f"{sys.argv[0]}: {sys.argv[1]} not found")
            sys.exit(2)
            address = 0

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "CMP":
            self.FL = 0x00
            if self.reg[reg_a] == self.reg[reg_b]:
                self.FL = self.FL | 0b00000001
            if self.reg[reg_a] < self.reg[reg_b]:
                self.FL = self.FL | 0b00000100
            if self.reg[reg_a] > self.reg[reg_b]:
                self.FL = self.FL | 0b00000010
        elif op == "ADD":
            self.reg[reg_a] = self.reg[reg_a] & self.reg[reg_b]
        elif op == "OR":
            self.reg[reg_a] = self.reg[reg_a] | self.reg[reg_b]
        elif op == "XOR":
            self.reg[reg_a] = self.reg[reg_a] ^ self.reg[reg_b]
        elif op == "NOT":
            self.reg[reg_a] = ~self.reg[reg_a]
        elif op == "SHL":
            self.reg[reg_a] = self.reg[reg_a] << self.reg[reg_b]
        elif op == "SHR":
            self.reg[reg_a] = self.reg[reg_a] >> self.reg[reg_b]
        elif op == "MOD":
            self.reg[reg_a] = self.reg[reg_a] % self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.PC,
            # self.fl,
            # self.ie,
            self.ram_read(self.PC),
            self.ram_read(self.PC + 1),
            self.ram_read(self.PC + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def op_add(self, operand_a, operand_b):
        self.alu("ADD", operand_a, operand_b)

    def op_and(self, operand_a, operand_b):
        self.alu("AND", operand_a, operand_b)

    def op_call(self, operand_a):
        self.reg[7] -= 1
        self.ram_write(self.reg[7], self.PC + 2)
        self.PC = self.reg[operand_a]

    def op_cmp(self, operand_a, operand_b):
        self.alu("CMP", operand_a, operand_b)

    def op_hlt(self):
        print("exiting")
        self.running = False

    def op_iret(self):
        for i in range(6, -1, -1):
            self.op_pop(i)
        # FL Register
        self.flag = self.ram[self.reg[7]]
        self.reg[7] += 1

        # PC Register
        self.PC = self.ram[self.reg[7]]
        self.reg[7] += 1

    def op_jeq(self, operand_a):
        if (self.FL & 0b00000001) == 1:
            self.PC = self.reg[operand_a]
        else:
            self.PC += 2

    def op_jge(self, operand_a):
        if (self.FL & 0b00000011) == 1:
            self.PC = self.reg[operand_a]
        else:
            self.PC += 2

    def op_jgt(self, operand_a):
        if (self.FL >> 1 & 0b00000001) == 1:
            self.PC = self.reg[operand_a]
        else:
            self.PC += 2

    def op_jle(self, operand_a):
        if (self.FL & 0b00000101) == 5:
            self.PC = self.reg[operand_a]
        else:
            self.PC += 2

    def op_jlt(self, operand_a):
        if (self.FL >> 2 & 0b00000001) == 1:
            self.PC = self.reg[operand_a]
        else:
            self.PC += 2

    def op_jmp(self, operand_a):
        self.PC = self.reg[operand_a]

    def op_jne(self, operand_a):
        if (self.FL & 0b00000001) == 0:
            self.PC = self.reg[operand_a]
        else:
            self.PC += 2

    def op_ld(self, operand_a, operand_b):
        self.reg[operand_a] = self.ram[self.reg[operand_b]]

    def op_ldi(self, operand_a, operand_b):
        self.reg[operand_a] = operand_b

    def op_mod(self, operand_a, operand_b):
        self.alu("MOD", operand_a, operand_b)

    def op_mul(self, operand_a, operand_b):
        self.alu("MUL", operand_a, operand_b)

    def op_not(self, operand_a, operand_b):
        self.alu("NOT", operand_a, operand_b)

    def op_or(self, operand_a, operand_b):
        self.alu("OR", operand_a, operand_b)

    def op_pop(self, operand_a):
        self.op_ldi(operand_a, self.ram[self.reg[7]])
        self.reg[7] += 1

    def op_pra(self, operand_a):
        print(chr(self.reg[operand_a]))

    def op_prn(self, operand_a):
        print(self.reg[operand_a])

    def op_push(self, operand_a):
        self.reg[7] -= 1
        self.ram_write(self.reg[7], self.reg[operand_a])

    def op_ret(self):
        self.PC = self.ram[self.reg[7]]
        self.reg[7] += 1

    def op_shl(self, operand_a, operand_b):
        self.alu("SHL", operand_a, operand_b)

    def op_shr(self, operand_a, operand_b):
        self.alu("SHR", operand_a, operand_b)

    def op_st(self, operand_a, operand_b):
        self.ram[self.reg[operand_a]] = self.reg[operand_b]

    def op_xor(self, operand_a, operand_b):
        self.alu("XOR", operand_a, operand_b)
