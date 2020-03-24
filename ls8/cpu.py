"""CPU functionality."""

import sys


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""

        self.ram = [0] * 256

        self.running = True

        # General Registers
        self.reg = [0] * 8
        self.reg[7] = 0xF4  # SP

        # Internal Registers
        self.PC = 0
        self.IR = None
        self.MAR = None
        self.MDR = None
        self.FL = 00000000

        LDI = 0b10000010
        PRN = 0b01000111
        HLT = 0b00000001
        MUL = 0b10100010
        POP = 0b01000110
        PUSH = 0b01000101

        self.branchtable = {}
        self.branchtable[MUL] = self.mul
        self.branchtable[LDI] = self.ldi
        self.branchtable[HLT] = self.hlt
        self.branchtable[PRN] = self.prn
        self.branchtable[POP] = self.pop
        self.branchtable[PUSH] = self.push

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    def run(self):
        while self.running:
            self.IR = self.ram_read(self.PC)
            operand_a = self.ram_read(self.PC + 1)
            operand_b = self.ram_read(self.PC + 2)

            operand_count = '{0:08b}'.format(self.IR)[:2]
            is_pc_setter = '{0:08b}'.format(self.IR)[4:5]

            if int(operand_count, 2) == 2:
                self.branchtable[self.IR](operand_a, operand_b)
            elif int(operand_count, 2) == 1:
                self.branchtable[self.IR](operand_a)
            else:
                self.branchtable[self.IR]()

            if int(is_pc_setter, 2) == 0:
                self.PC += int(operand_count, 2) + 1

    def load(self):
        """Load a program into memory."""
        if len(sys.argv) != 2:
            print("usage: ls8.py filename", file=sys.stderr)
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

    def ldi(self, operand_a, operand_b):
        self.reg[operand_a] = operand_b

    def hlt(self):
        print("exiting")
        self.running = False

    def prn(self, operand_a):
        print(self.reg[operand_a])

    def mul(self, operand_a, operand_b):
        self.alu("MUL", operand_a, operand_b)

    def push(self, operand_a, operand_b):
        self.reg[7] -= 1
        self.ram_write(self.reg[7], operand_a)

    def pop(self, operand_a):
        self.ldi(operand_a, self.ram[self.reg[7]])
        self.reg[7] += 1
