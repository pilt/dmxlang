# -*- coding: utf-8 -*-

class Statement(object):
    indent = -1
    pass


class Statements(list):
    pass


class DoStatement(Statement):
    def __init__(self, times=0, forever=False):
        self.times = times
        self.forever = forever
        self.statements = Statements()

    def __repr__(self):
        if self.forever == True:
            return "DoStatement(forever=True, indent=%i)" % self.indent
        else:
            return "DoStatement(times=%i, indent=%i)" \
                % (self.times, self.indent)


class ToStatement(Statement):
    def __init__(self, color, channel=1, from_color=None):
        self.color = color
        self.channel = channel
        self.from_color = from_color

    def __repr__(self):
        return "ToStatement(%r, channel=%s, from_color=%r, indent=%i)" \
            % (self.color, self.channel, self.from_color, self.indent)

class ResetStatement(Statement):
    """ Reset a moving head"""
    def __init__(self, channel):
        self.channel = channel

class MoveStatement(Statement):
    """ Move moving head """
    def __init__(self, channel, pan, tilt, speed):
        self.channel = channel
        self.pan = pan
        self.tilt = tilt
        self.speed = speed

class SetStatement(Statement):
    """ Change value on a moving head"""
    def __init__(self, channel, param, value=None, ad=None):
        self.channel = channel
        self.param = param
        self.value = value
        self.ad = ad


class UpdateStatement(Statement):
    """Used in fades."""
    def __init__(self, channel, mem_addr, update_by):
        self.channel = channel
        self.mem_addr = mem_addr
        self.update_by = update_by


class WaitStatement(Statement):
    def __init__(self, time=None):
        if time is None:
            time = 0
        self.time = time

    def __repr__(self):
        return "WaitStatement(time=%i, indent=%i)" \
            % (self.time, self.indent)


class RGB(object):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def round(self):
        rgb = [int(x//1) for x in [self.r, self.g, self.b]]
        return RGB(*rgb)

    def __repr__(self):
        return "RGB(%s, %s, %s)" % (self.r, self.g, self.b)


class RGBDiffer(object):
    def __init__(self, rgb1, rgb2):
        self.rgb1 = rgb1
        self.rgb2 = rgb2

    def diff(self):
        diff = []
        for c in ['r', 'g', 'b']:
            c1 = getattr(self.rgb1, c)
            c2 = getattr(self.rgb2, c)
            diff.append(c2-c1)
        return RGB(*diff)

    def step_diff(self, step_count):
        diff = self.diff()
        diffs = [x/float(step_count) for x in [diff.r, diff.g, diff.b]]
        return RGB(*diffs)

    def __repr__(self):
        return "RGBDiffer(rgb1=%r, rgb2=%r, diff=%r)" \
                % (self.rgb1, self.rgb2, self.diff())
