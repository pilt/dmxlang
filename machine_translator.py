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

    def _a(self, line):
        """Add a machine code line and increment the internal line number
        counter. You should use this method and not operate on 'self.lines'
        directly. """
        self.lineno += 1
        self.lines.append(line)

    def on_do(self, do):
        """Write the machine code for a 'do' block. See 'DoStatement' in the
        statements module to see 'do's properties. """
        start_line = self.lineno
        if do.forever:
            start_label = label(start_line, 'do_forever')
            self._a("%s : nop" % start_label)
        else:
            start_label = label(start_line, 'do_%i_times' % do.times)
            self._a("lda %s" % absarg(do.times))
            self._a("%s : nop" % start_label)
            self._a("get d0")
            self._a("store d0 %s" % mem_counter(start_line))

        for child in do.statements:
            self.walk(child)

        if do.forever:
            self._a("jmp %s" % start_label)
        else:
            self._a("load d0 %s" % mem_counter(start_line))
            self._a("put d0")
            self._a("sub %s" % absarg(1))
            self._a("get d0")
            self._a("store d0 %s" % mem_counter(start_line))
            end_label = label(self.lineno + 2, 'end_do')
            self._a("jmpz %s" % end_label)
            self._a("jmp %s" % start_label)
            self._a("%s : nop" % end_label)
    
    def on_to(self, to):
        """Write the machine code for a 'to' statement. See 'ToStatement' in the
        statements module to see 'to's properties."""
        # TODO: Implement other things. See IMPLEMENTATION.
        for (c, off) in zip([0, to.color.r, to.color.g, to.color.b, 0], range(5)):
            self._a("lda %s" % absarg(c))
            self._a("get d0")
            self._a("store d0 %s" % channel(to.channel + off))

    def on_wait(self, wait):
        """Write the machine code for a 'wait' statement. See 'WaitStatement' in
        the statements module to see 'wait's properties."""
        # FIXME: Timing! 
        start = label(self.lineno, 'wait_%i' % wait.time)
        self._a("lda %s" % absarg(wait.time))
        self._a("get d0")
        counter = mem_counter(self.lineno)
        self._a("store d0 %s" % counter)
        self._a("%s : nop" % start)

        # Inner loop.
        inner = label(self.lineno, 'inner_wait')
        self._a("lda %s" % absarg(255))
        self._a("%s : nop" % inner)
        [self._a("nop") for _ in range(7)]
        self._a("sub %s" % absarg(1))
        inner_end = label(self.lineno + 2, 'inner_end')
        self._a("jmpz %s" % inner_end)
        self._a("jmp %s" % inner)
        self._a("%s : nop" % label(self.lineno, 'inner_end'))

        # Outer check.
        self._a("load d0 %s" % counter)
        self._a("put d0")
        self._a("sub %s" % absarg(1))
        self._a("get d0")
        self._a("store d0 %s" % counter)
        outer_end = label(self.lineno + 2, 'wait_end')
        self._a("jmpz %s" % outer_end)
        self._a("jmp %s" % start)
        self._a("%s : nop" % outer_end)

    def end(self):
        """Called when we are finished parsing. Write output to standard
        output."""
        sys.stdout.write("\n".join(self.lines) + '\n')
