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
    def __init__(self, color, go_back=False, time=None, 
            steps=False, channel=1):

        if time is None:
            time = 0

        self.color = color
        self.go_back = go_back
        self.time = time
        self.steps = steps
        self.channel = channel

    def __repr__(self):
        return "ToStatement(%r, go_back=%r, time=%i, steps=%s, channel=%s, indent=%i)" \
            % (self.color, self.go_back, self.time, 
               self.steps, self.channel, self.indent)

class WaitStatement(Statement):
    def __init__(self, time=None):
        if time is None:
            time = 0
        self.time = time

    def __repr__(self):
        return "WaitStatement(time=%i, indent=%i)" \
            % (self.time, self.indent)
