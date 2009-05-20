from time import sleep

class Machine(object):
    def __init__(self, rom, ram):
        self.rom = rom
        self.ram = ram
        self.reset()
    def reset(self):
        self.time = 0
        self.ir = 0
        self.pc = 0
        self.ar = 0
        self.dr = {'d0': 0, 'd1': 0}
        self.d1 = 0
        self.ad = 128
    def __iter__(self):
        return self
    def next(self):
        line = self.rom[self.pc]
        instr = line[0]
        args = line[1:]
        self.last_pc = self.pc
        self.do(instr, args)
        self.pc += 1
        return self.time
    def clock(self):
        sleep(0.01)
        self.time += 1
    def do(self, instr, args):
        self.clock()
        getattr(self, instr.lower())(*args)
    def nop(self):
        pass
    def jmp(self, addr):
        self.clock()
        self.pc = addr
    def jmpz(self, addr):
        self.clock()
        if self.ar == 0:
            self.pc = addr
    def store(self, dx, adr):
        self.ram[int(adr, 16)] = self.dr[dx]
    def load(self, dx, adr):
        self.dr[dx] = self.ram[int(adr, 16)]
    def add(self, data):
        if data[0] == 'd':
            self.ar = self.ar + self.dr[data] % 0x100
        elif data[0] == '#':
            self.ar = self.ar + int(data[1:], 16) % 0x100
    def sub(self, data):
        if data[0] == 'd':
            self.ar = self.ar - self.dr[data] % 0x100
        elif data[0] == '#':
            self.ar = self.ar - int(data[1:], 16) % 0x100
    def put(self, dx):
        self.ar = self.dr[dx]
    def get(self, dx):
        self.dr[dx] = self.ar
    def adread(self):
        self.ar = self.ad
    def lda(self, data):
        self.ar = data

import sys
ram = [0]*0x1000
#asm = sys.stdin.read().split('\n')
asm = file('asm.asm').read().split('\n')
keywords = ['store', 'load', 'add', 'sub', 'put', 'get', 'jmp', 'jmpz']
labels = {}
rom = []
for line in asm:
    if line:
        line = line.split()
        command = line[0]
        if not command in keywords:
            labels[command.strip(":")] = len(rom)
            line = line[2:] 
        if line:
            rom.append(line)

for i, line in enumerate(rom):
    if line[0] in ['jmp', 'jmpz']:
        rom[i][1] = labels[line[1]]

m = Machine(rom, ram)
for time in m:
    if not time % 100:
        print time
