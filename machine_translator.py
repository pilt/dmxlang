#! /usr/bin/env python
# -*- coding: utf-8 -*-

import translator

class ID(object): 
    __shared = {} 
    def __init__(self):
        self.__dict__ = self.__shared

    def feed(self):
        if hasattr(self, 'id'):
            self.id += 1
        else:
            self.id = 0
        return self.id

def uid():
    """Return a unique, numeric identifier."""
    feeder = ID()
    return feeder.feed()

def umem():
    """Return a unique memory address. You should use this function every time
    you need a new memory address to store something at."""
    # FIXME: Use another counter for memory addresses. There is no need for them
    # to be shared with label identifiers.
    return uid()

def absarg(decimal):
    val = hex(abs(decimal))[2:]
    return "#" + val.rjust(2, '0')

def channel(offset=0):
    """Channel 0 is at memory address 0xC00 (3072)."""
    return hex(3072 + offset)[2:]

def mem(adr):
    """Format a memory address."""
    return hex(adr)[2:].rjust(3, '0')

def label(tag="label"):
    "Generate a label for an address. 'tag' will be added a the beginning."
    return "%s__%s" % (tag, str(uid()).rjust(5, '0'))

def mem_counter(offset=0):
    return mem(offset)

def add_loop_forever(transl, body_statements):
    """Insert a forever loop in a translator. Elements in 'body_statements'
    can be either a subclass of 'translator.Statement' or a string of machine code.
    """
    start_label = label('do_forever')
    insert(transl, "%s : nop" % start_label)
    for child in body_statements:
        try:
            transl.walk(child)
        except translator.TranslationError:
            insert(transl, "%s" % child)
    insert(transl, "jmp %s" % start_label)

def add_loop_times(transl, times, body_statements):
    """Insert a loop running a given number of iterations in a
    translator. Elements in 'body_statements' can be either a subclass of
    'translator.Statement' or a string of machine code. """
    start_line = transl.lineno
    start_label = label('do_%i_times' % times)
    insert(transl, "lda %s" % absarg(times))
    insert(transl, "%s : nop" % start_label)
    insert(transl, "get d0")
    insert(transl, "store d0 %s" % mem_counter(start_line))
    for child in body_statements:
        transl.walk(child)
    insert(transl, "load d0 %s" % mem_counter(start_line))
    insert(transl, "put d0")
    insert(transl, "sub %s" % absarg(1))
    insert(transl, "get d0")
    insert(transl, "store d0 %s" % mem_counter(start_line))
    end_label = label('end_do')
    insert(transl, "jmpz %s" % end_label)
    insert(transl, "jmp %s" % start_label)
    insert(transl, "%s : nop" % end_label)

def insert(transl, line_or_lines):
    """Add machine code lines and increment the internal line number
    counter. You should use this method and not operate on 'transl.lines'
    directly. """
    if type(line_or_lines) == str:
        line_or_lines = [line_or_lines]
    for line in line_or_lines:
        transl.lineno += 1
        transl.lines.append(line)

class TranslationError(translator.TranslationError):
    pass

class MasterTranslate(translator.MasterTranslate):

    def start(self):
        self.lineno = 0
        self.lines = []
        self.procs = []

    def add_process(self, statements):
        max_pids = 8
        pid = len(self.procs)
        if pid >= max_pids:
            raise TranslationError("too many processes")
        proctrans = ProcessTranslate(pid)
        proctrans.traverse(statements)
        self.procs.append(proctrans)

    def on_process(self, process):
        if process.indent > 0:
            raise TranslationError('processes must be at first level indentation')
        self.add_process(process.statements)

    def end(self):
        body = translator.Statements()
        proc_returns = [label('process_%i_return_to_master' % p.pid) for p in self.procs]
        proc_data = zip(self.procs, proc_returns)
        # Insert code for the master event loop.
        for (proc, ret) in proc_data:
            body.append('jmp %s' % proc.start_label)
            body.append('%s : nop' % ret)
        add_loop_forever(self, body)
        insert(self, ['', '']) 

        # Insert code for each process.
        for (proc, ret) in proc_data:
            insert(self, proc.lines)
            insert(self, [
                'jmp %s' % ret, 
                '', 
                ''])

        print "\n".join(self.lines)

class ProcessTranslate(translator.ProcessTranslate):
    """This class translates a parse tree to machine code."""
    
    def __init__(self, pid):
        self.pid = pid

        # Initialize memory area.
        self.mem_wait1 = umem()
        self.mem_wait2 = umem() # XXX: do we need both?
        self.mem_ar = umem()
        self.mem_d0 = umem()
        self.mem_break = umem()

        self.return_labels = []
        
        # Initialize labels.
        self.start_label = label('process_%i_start' % self.pid)
        self.end_label = label('process_%i_end' % self.pid)
        self.enter_label = label('process_%i_enter' % self.pid)

    def insert_save(self):
        """Insert code to save D0 and AR values to memory."""
        self.lines += [
            'store d0 %s' % mem(self.mem_d0),
            'get d0',
            'store d0 %s' % mem(self.mem_ar)]

    def insert_restore(self):
        """Insert code to restore values of D0 and AR from memory."""
        self.lines += [
            'load d0 %s' % mem(self.mem_ar),
            'put d0',
            'load d0 %s' % mem(self.mem_d0)]

    def insert(self, line_or_lines):
        """Add machine code lines and increment the internal line number
        counter. You should use this method and not operate on 'self.lines'
        directly. """
        if type(line_or_lines) == str:
            line_or_lines = [line_or_lines]
        for line in line_or_lines:
            self.lineno += 1
            slot_space = 10
            if self.lineno % slot_space == 0 or line.lstrip().startswith('jmp'):
                count = self.lineno // slot_space
                return_label = label('process_%i_return_%i' % (self.pid, count))
                self.return_labels.append((count, return_label))
                self.insert_save()
                self.lines.append("put d1")
                self.lines.append("add #01")
                self.lines.append("%s : get d1" % return_label)
                self.lines.append("store d1 %s" % mem(self.mem_break))
                self.insert_restore()
            self.lines.append(line)

    def start(self):
        self.lineno = 0
        self.lines = []
        
        # Insert label to start of process. 
        extra = self.lines.append
        extra('%s : nop' % self.start_label)
        extra('lda #00')
        extra('get d1')
        extra('store d1 %s' % mem(self.mem_break))

    def end(self):
        """Called when we are finished parsing."""

        extra = self.lines.append
        extra('jmp %s' % self.end_label)
        extra('%s : nop' % self.enter_label)
        extra('load d0 %s' % mem(self.mem_break))
        extra('put d0')
        for (count, ret_lbl) in self.return_labels:
            extra('jmpz %s' % ret_lbl)
            extra('sub #01')
        extra('jmp %s' % self.start_label)
        extra('%s : nop' % self.end_label)

    def on_do(self, do):
        """Write the machine code for a 'do' block. See 'DoStatement' in the
        statements module to see 'do's properties. """
        if do.forever:
            add_loop_forever(self, do.statements)
        else:
            add_loop_times(self, do.times, do.statements)
    
    def on_to(self, to):
        """Write the machine code for a 'to' statement. See 'ToStatement' in the
        statements module to see 'to's properties."""
        # TODO: Implement other things. See IMPLEMENTATION.
        if to.time == 0:
            for (c, off) in zip([0, to.color.r, to.color.g, to.color.b, 0], range(5)):
                self.insert("lda %s" % absarg(c))
                self.insert("get d0")
                self.insert("store d0 %s" % channel(to.channel + off))
        else: # we have a fade
            # FIXME: Every fade will be 255ms long whatever argument was passed.
            # fade_time = to.time
            # FIXME: The final color is likely to differ from the wanted value
            # because of the rounding.

            # See 'IMPLEMENTATION' for a description of the algorithm.
            
            # Generate memory addresses to use for the current color.
            curcol_addrs = [umem() for _ in range(3)]

            # Save the initial color values to memory.
            for (c, off) in zip(
                    [0,
                    to.from_color.r, 
                    to.from_color.g, 
                    to.from_color.b,
                    0], range(5)):
                self.insert("lda %s" % absarg(c))
                self.insert("get d0")
                if off not in [0, 4]:
                    self.insert("store d0 %s" % mem(curcol_addrs[off-1]))
                self.insert("store d0 %s" % channel(to.channel + off))
            
            # Insert the loop code.
            fade_steps = 17
            iter_wait = 15
            differ = translator.RGBDiffer(to.from_color, to.color)
            step_diff = differ.step_diff(fade_steps).round()
            print "FROM : %r" % to.from_color
            print "TO : %r" % to.color
            print "STEP DIFF : %r" % step_diff
            print ""
            body = translator.Statements()
            for (color_offset, iter_diff) in [
                    (0, step_diff.r),
                    (1, step_diff.g),
                    (2, step_diff.b)]:
                col_channel = to.channel + color_offset + 1
                mem_addr = curcol_addrs[color_offset]
                update = translator.UpdateStatement(col_channel, mem_addr, iter_diff)
                body.append(update)
            wait = translator.WaitStatement(iter_wait)
            body.append(wait)
            add_loop_times(self, fade_steps, body)

    def on_update(self, update):
        if update.update_by == 0:
            return
        self.insert('load d0 %s' % mem(update.mem_addr))
        self.insert('put d0')
        if update.update_by < 0:
            update_line = 'sub %s' % absarg(update.update_by)
        else:
            update_line = 'add %s' % absarg(update.update_by)
        self.insert(update_line)
        self.insert('get d0')
        self.insert('store d0 %s' % mem(update.mem_addr))
        self.insert('store d0 %s' % channel(update.channel))

    def on_wait(self, wait):
        """Write the machine code for a 'wait' statement. See 'WaitStatement' in
        the statements module to see 'wait's properties."""
        # FIXME: Use 'add_loop_times'.
        start = label('wait_%i' % wait.time)
        self.insert("lda %s" % absarg(wait.time))
        self.insert("get d0")
        counter = mem_counter(self.lineno)
        self.insert("store d0 %s" % counter)
        self.insert("%s : nop" % start)

        # Inner loop.
        inner = label('inner_wait')
        self.insert("lda %s" % absarg(200))
        self.insert("%s : nop" % inner)
        [self.insert("nop") for _ in range(14)]
        self.insert("sub %s" % absarg(1))
        inner_end = label('inner_end')
        self.insert("jmpz %s" % inner_end)
        self.insert("jmp %s" % inner)
        self.insert("%s : nop" % inner_end)

        # Outer check.
        self.insert("load d0 %s" % counter)
        self.insert("put d0")
        self.insert("sub %s" % absarg(1))
        self.insert("get d0")
        self.insert("store d0 %s" % counter)
        outer_end = label('wait_end')
        self.insert("jmpz %s" % outer_end)
        self.insert("jmp %s" % start)
        self.insert("%s : nop" % outer_end)


    def __str__(self):
        return "\n".join(self.lines) + '\n'

