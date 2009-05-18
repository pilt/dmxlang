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
    def __init__(self, color, time=None, 
            steps=False, channel=1, from_color=None):

        if time is None:
            time = 0

        self.color = color
        self.time = time
        self.steps = steps
        self.channel = channel
        self.from_color = from_color

    def __repr__(self):
        return "ToStatement(%r, time=%i, steps=%s, channel=%s, indent=%i)" \
            % (self.color, self.time, self.steps, self.channel, self.indent)


class WaitStatement(Statement):
    def __init__(self, time=None):
        if time is None:
            time = 0
        self.time = time

    def __repr__(self):
        return "WaitStatement(time=%i, indent=%i)" \
            % (self.time, self.indent)
