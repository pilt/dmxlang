# -*- coding: utf-8 -*-

from statements import *

def strip_comment(line):
    pos = line.find('--')
    if pos == -1:
        return line
    else:
        return line[:pos]

class ParseError(Exception):
    pass

class TimeError(Exception):
    pass

class Time(object):
    def __init__(self, time=0):
        self.time = time

    def from_string(self, string):
        for (end, mult) in [('ms', 1), ('s', 1000)]:
            if string.endswith(end):
                time = string[:-len(end)]
                if time.isdigit():
                    time = int(time) * mult
                    if (time <= 0) or (time > 255):
                        raise TimeError('time must be 1ms to 255ms long')
                    self.time = time
                    break
                else:
                    raise TimeError('bad time value (%s)' % time)
        else:
            raise TimeError("unknown time unit")
        return self

class IndentError(Exception):
    pass

def indent_level(line):
    """Get the level of indentation on 'line.' Indentation must be done with 
    spaces and the number of spaces must be a multiple of four.

    Example
        >>> indent_level('to 255 0 0')
        0
        >>> indent_level('    to 255 0 0') # 4 spaces
        1
    """
    spaces = 0
    for ch in line:
        if ch == ' ':
            spaces += 1
        elif ch.isspace(): # nothing but spaces are valid for indenation
            raise IndentError("indentation is done with spaces (got %r)" \
                % ch)
        else:
            break
    if spaces % 4 == 0:
        return spaces // 4
    else:
        raise IndentError("indentation level could not be determined")

def parse(lines):
    def parse_do(args):
        if len(args) == 0:
            raise ParseError("missing argument to 'do' statement")
        elif len(args) == 1:
            if args[0] == 'forever':
                return DoStatement(forever=True)
        elif len(args) == 2:
            if args[0].isdigit() and args[1] == 'times':
                return DoStatement(times=int(args[0]))
        else:
            raise ParseError("too many arguments to 'do' statement")

    def check_color(args):
        try:
            for arg in args:
                if arg.isdigit():
                    val = int(arg)
                    if (0 <= val and val <= 255):
                        continue
                raise ParseError("bad RGB value %r" % arg)
        except ParseError, e:
            return (False, str(e))
        return (True, '')
        
    def parse_reset(args):
        if len(args) != 1:
            raise ParseError("wrong number of arguments to 'reset'")  
        return ResetStatement(int(args[0]))
        
    def parse_set(args):
        if len(args) != 3:
            raise ParseError("wrong number of arguments to 'set'")
        assert args[1] in ['color', 'shutter', 'gobo', 'focus', 'direct']
        return SetStatement(int(args[0]), args[1], args[2])
    
    def parse_move(args):
        if len(args) != 4:
            raise ParseError("wrong number of arguments to 'move'")
        pan = args[1]
        tilt = args[2]
        speed = int(args[3])
        return MoveStatement(int(args[0]), pan, tilt, speed)

    def parse_to(args):
        if len(args) > 10:
            raise ParseError("too many arguments to 'to'")
        def off(i):
            return args[i]
        
        ok, msg = check_color(args[:3])
        if not ok:
            raise ParseError(msg)
        
        color = RGB(*[int(i) for i in args[:3]])
        sm = ToStatement(color)

        o = 3
        if len(args) == o:
            return sm
        
        if off(o) == 'from':
            if len(args) < o + 3:
                raise ParseError("expecting color (three-tuple)")
            else:
                o += 1
                color = [args[o], args[o+1], args[o+2]]
                ok, msg = check_color(color)
                if ok:
                    sm.from_color = RGB(*[int(i) for i in color])
                    o += 3
                    if len(args) == o:
                        return sm
                else:
                    raise ParseError(msg)


        if off(o) == 'on':
            if off(o+1) == 'channel':
                chan = off(o+2) 
                if chan.isdigit():
                    sm.channel = int(chan)
                    o += 3
                    if len(args) == o:
                        return sm
                else:
                    ParseError("bad channel value %r" % chan)
            else:
                raise ParseError("expecting 'channel'")
        
        if len(args) == o:
            return sm
        else:
            raise ParseError("unexpected keyword %r" % args[o])

    def parse_wait(args):
        if len(args) != 1:
            raise ParseError("bad number of arguments to 'wait'")
        try:
            time_obj = Time()
            time_obj.from_string(args[0])
        except TimeError, e:
            raise ParseError(e)
        sm = WaitStatement(time_obj.time)
        return sm
    
    # Register our parsers.
    parsers = {}
    for (name, value) in locals().iteritems():
        begner = 'parse_'
        if name.startswith(begner):
            parsers[name[len(begner):]] = value

    parsed = []
    def check_indent(this_indent):
        if len(parsed) != 0:
            last = parsed[-1]
            if type(last) == DoStatement:
                if this_indent <= last.indent:
                   raise ParseError("empty 'do' block")
                elif this_indent > last.indent + 1:
                   raise ParseError("too large indendation increase")
    
    lines.append('') # we want to check that the indentation on the real last 
                     # line is OK
    for (idx, line) in enumerate(lines):
        words = strip_comment(line).lower().split()
        
        try:
            indent = indent_level(line)
        except IndentError, e:
            raise ParseError("%s on line %i: %r" % (e, idx+1, line))

        if len(words) == 0:
            check_indent(indent)
            continue

        statement = words[0]
        args = words[1:]
        if statement in parsers:
            try:
                check_indent(indent)
                sm = parsers[statement](args)
                sm.indent = indent
                parsed.append(sm)

            except ParseError, e:
                err = "%s on line %i: %r" % (e, idx+1, line)
                raise ParseError(err)
#            except Exception, e:
#                raise ParseError("Bad line1: %r" % line)
        else:
            raise ParseError("Bad line2: %r" % line)

    def tree(first, rest):
        if type(first) == DoStatement:
            children = Statements()
            stop = rest
            for r in rest:
                if r.indent > first.indent:
                    stop = stop[1:]
                    children.append(r)
                else:
                    break

            first.statements = tree(children[0], children[1:])
            if len(stop) == 0:
                return [first]
            else:
                return [first] + tree(stop[0], stop[1:])
        else:
            if len(rest) == 0:
                return [first]
            else:
                return [first] + tree(rest[0], rest[1:])
    
    if len(parsed) == 0:
        return []
    else:
        return tree(parsed[0], parsed[1:])

