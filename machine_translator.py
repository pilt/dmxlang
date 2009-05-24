# -*- coding: utf-8 -*-

import translator

modes =  {'direct': {'offset': 0, 'values': {}}, 
          'color':
              {'offset': 6, 
               'values': 
               {'white': 0,
                'turquoise': 10,
                'red': 21, 
                'cyan': 32, 
                'green': 42, 
                'magenta': 53, 
                'lightblue': 64, 
                'yellow': 74,
                'green': 85, 
                'pink': 96, 
                'blue': 106, 
                'orange': 117
                }},
          'gobo': 
          {'offset': 10,
           'values': 
           {'open': 0,
            'gobo1': 32,
            'gobo2': 64,
            'gobo3': 96,
            'gobo4': 128,
            'gobo5': 160,
            'gobo6': 192,
            }}, 
          'focus': {'offset': 13, 'values': {}}, 
          'shutter': {'offset': 15,
                      'values': {'open': 255, 
                                 'closed': 0}}}
def absarg(decimal):
    val = hex(abs(decimal))[2:]
    return "#" + val.rjust(2, '0')

def channel(offset=0):
    """Channel 0 is at memory address 0xC00 (3072)."""
    return hex(3072 + offset)[2:]

def mem(adr):
    """Format a memory address."""
    return hex(adr)[2:].rjust(3, '0')

def label(adr, tag="label"):
    "Generate a label for an address. 'tag' will be added a the beginning."
    label = tag + '__' + mem(adr)
    return label

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

    def gen_loop_times(self, times, body_statements):
        start_line = self.lineno
        start_label = label(start_line, 'do_%i_times' % times)
        self.insert("lda %s" % absarg(times))
        self.insert("%s :" % start_label)
        self.insert("get d0")
        self.insert("store d0 %s" % mem_counter(start_line))
        for child in body_statements:
            self.walk(child)
        self.insert("load d0 %s" % mem_counter(start_line))
        self.insert("put d0")
        self.insert("sub %s" % absarg(1))
        self.insert("get d0")
        self.insert("store d0 %s" % mem_counter(start_line))
        end_label = label(self.lineno + 2, 'end_do')
        self.insert("jmpz %s" % end_label)
        self.insert("jmp %s" % start_label)
        self.insert("%s :" % end_label)

    def gen_loop_forever(self, body_statements):
        start_line = self.lineno
        start_label = label(start_line, 'do_forever')
        self.insert("%s :" % start_label)
        for child in body_statements:
            self.walk(child)
        self.insert("jmp %s" % start_label)

    def on_do(self, do):
        """Write the machine code for a 'do' block. See 'DoStatement' in the
        statements module to see 'do's properties. """
        if do.forever:
            self.gen_loop_forever(do.statements)
        else:
            self.gen_loop_times(do.times, do.statements)

    def insert_load_value(self, value):
        if value == 'ad':
            self.insert('adread')
        else:
            self.insert('lda %s' % absarg(int(value)))
            self.insert('get d0')
        
    def on_reset(self, node):
        self.insert([
         'lda #00',
         'get d0', ])
        for i in range(16):
            self.insert('store d0 %s' % channel(node.channel + i))
            self.insert('nop')
        self.insert([
         'lda #ff',
         'get d0', ])
        for i in [5, 14, 15]:
            self.insert('store d0 %s' % channel(node.channel + i))
            self.insert('nop')
            
    def on_move(self, node):
        self.insert_load_value(node.pan)
        self.insert('store d0 %s'% channel(node.channel+0))
        self.insert_load_value(node.tilt)
        self.insert('store d0 %s'% channel(node.channel+1))
        self.insert(['lda %s' % absarg(node.speed),
                    'get d0',
                    'store d0 %s'% channel(node.channel+4),])

    def on_set(self, node):
        mode = modes[node.param]
        offset = mode['offset']
        value = mode['values'].get(node.value, node.value)
        self.insert_load_value(value)
        self.insert('store d0 %s'% channel(node.channel+offset))
        
    def on_to(self, to):
        """Write the machine code for a 'to' statement. See 'ToStatement' in the
        statements module to see 'to's properties."""
        if to.from_color is None:
            for (c, off) in zip([0, to.color.r, to.color.g, to.color.b, 0], range(5)):
                self.insert("lda %s" % absarg(c))
                self.insert("get d0")
                self.insert("store d0 %s" % channel(to.channel + off))
        else: # we have a fade
            # See 'IMPLEMENTATION' for a description of the algorithm.
            
            # Memory address to store current color values at. Red is at
            # 'curcol_mem_start' + 0, green at +1, blue at +2.
            curcol_mem_start = self.lineno

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
                    self.insert("store d0 %s" % mem(curcol_mem_start + off))
                self.insert("store d0 %s" % channel(to.channel + off))
            
            # Insert the loop code.
            fade_steps = 17
            iter_wait = 15
            differ = translator.RGBDiffer(to.from_color, to.color)
            step_diff = differ.step_diff(fade_steps).round()
            body = translator.Statements()
            for (color_offset, iter_diff) in [
                    (1, step_diff.r),
                    (2, step_diff.g),
                    (3, step_diff.b)]:
                col_channel = to.channel + color_offset
                mem_addr = curcol_mem_start + color_offset
                update = translator.UpdateStatement(col_channel, mem_addr, iter_diff)
                body.append(update)
            wait = translator.WaitStatement(iter_wait)
            body.append(wait)
            self.gen_loop_times(fade_steps, body)

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
        # FIXME: Use 'gen_loop_times'.
        start = label(self.lineno, 'wait_%i' % wait.time)
        self.insert("lda %s" % absarg(wait.time))
        self.insert("get d0")
        counter = mem_counter(self.lineno)
        self.insert("store d0 %s" % counter)
        self.insert("%s :" % start)

        # Inner loop.
        inner = label(self.lineno, 'inner_wait')
        self.insert("lda %s" % absarg(200))
        self.insert("%s :" % inner)
        [self.insert("nop") for _ in range(14)]
        self.insert("sub %s" % absarg(1))
        inner_end = label(self.lineno + 2, 'inner_end')
        self.insert("jmpz %s" % inner_end)
        self.insert("jmp %s" % inner)
        self.insert("%s :" % label(self.lineno, 'inner_end'))

        # Outer check.
        self.insert("load d0 %s" % counter)
        self.insert("put d0")
        self.insert("sub %s" % absarg(1))
        self.insert("get d0")
        self.insert("store d0 %s" % counter)
        outer_end = label(self.lineno + 2, 'wait_end')
        self.insert("jmpz %s" % outer_end)
        self.insert("jmp %s" % start)
        self.insert("%s :" % outer_end)

    def __str__(self):
        return "\n".join(self.lines) + '\n'

    def end(self):
        """Called when we are finished parsing."""
        pass
