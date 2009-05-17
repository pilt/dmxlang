# -*- coding: utf-8 -*-

import translator
import sys

def absarg(decimal):
    val = hex(decimal)[2:]
    return "#" + val.rjust(2, '0')

def channel(offset=0):
    return hex(3072 + offset)[2:]

def mem(adr):
    return hex(adr)[2:].rjust(3, '0')

def label(adr, tag="label"):
    label = tag + mem(adr)
    return label.upper()

def mem_counter(offset=0):
    return mem(offset)

class Translate(translator.Translate):
    """This class translates a parse tree to machine code."""

    def start(self):
        self.lines = []
        self.lineno = 0

    def insert(self, line_or_lines):
        """Add machine code lines and increment the internal line number
        counter. You should use this method and not operate on 'self.lines'
        directly. """
        if type(line_or_lines) == str:
            line_or_lines = [line_or_lines]
        for line in line_or_lines:
            self.lineno += 1
            self.lines.append(line)

    def on_do(self, do):
        """Write the machine code for a 'do' block. See 'DoStatement' in the
        statements module to see 'do's properties. """
        start_line = self.lineno
        if do.forever:
            start_label = label(start_line, 'do_forever')
            self.insert("%s : nop" % start_label)
        else:
            start_label = label(start_line, 'do_%i_times' % do.times)
            self.insert("lda %s" % absarg(do.times))
            self.insert("%s : nop" % start_label)
            self.insert("get d0")
            self.insert("store d0 %s" % mem_counter(start_line))

        for child in do.statements:
            self.walk(child)

        if do.forever:
            self.insert("jmp %s" % start_label)
        else:
            self.insert("load d0 %s" % mem_counter(start_line))
            self.insert("put d0")
            self.insert("sub %s" % absarg(1))
            self.insert("get d0")
            self.insert("store d0 %s" % mem_counter(start_line))
            end_label = label(self.lineno + 2, 'end_do')
            self.insert("jmpz %s" % end_label)
            self.insert("jmp %s" % start_label)
            self.insert("%s : nop" % end_label)
    
    def on_to(self, to):
        """Write the machine code for a 'to' statement. See 'ToStatement' in the
        statements module to see 'to's properties."""
        # TODO: Implement other things. See IMPLEMENTATION.
        for (c, off) in zip([0, to.color.r, to.color.g, to.color.b, 0], range(5)):
            self.insert("lda %s" % absarg(c))
            self.insert("get d0")
            self.insert("store d0 %s" % channel(to.channel + off))

    def on_wait(self, wait):
        """Write the machine code for a 'wait' statement. See 'WaitStatement' in
        the statements module to see 'wait's properties."""
        # FIXME: Timing! 
        start = label(self.lineno, 'wait_%i' % wait.time)
        self.insert("lda %s" % absarg(wait.time))
        self.insert("get d0")
        counter = mem_counter(self.lineno)
        self.insert("store d0 %s" % counter)
        self.insert("%s : nop" % start)

        # Inner loop.
        inner = label(self.lineno, 'inner_wait')
        self.insert("lda %s" % absarg(255))
        self.insert("%s : nop" % inner)
        [self.insert("nop") for _ in range(7)]
        self.insert("sub %s" % absarg(1))
        inner_end = label(self.lineno + 2, 'inner_end')
        self.insert("jmpz %s" % inner_end)
        self.insert("jmp %s" % inner)
        self.insert("%s : nop" % label(self.lineno, 'inner_end'))

        # Outer check.
        self.insert("load d0 %s" % counter)
        self.insert("put d0")
        self.insert("sub %s" % absarg(1))
        self.insert("get d0")
        self.insert("store d0 %s" % counter)
        outer_end = label(self.lineno + 2, 'wait_end')
        self.insert("jmpz %s" % outer_end)
        self.insert("jmp %s" % start)
        self.insert("%s : nop" % outer_end)

    def end(self):
        """Called when we are finished parsing. Write output to standard
        output."""
        sys.stdout.write("\n".join(self.lines) + '\n')
