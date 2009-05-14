# -*- coding: utf-8 -*-

import sys

class Translate(object):
    def start(self):
        sys.stdout.write("start\n\n")
        self.time = 0
        self.lines = []

    def add_evt(self, evt):
        self.lines.append(" "*4*evt.indent + repr(evt))

    def on_do(self, do):
        self.time += 1
        self.add_evt(do)
    
    def on_to(self, to):
        self.time += 1
        self.add_evt(to)

    def on_wait(self, wait):
        self.time += 1
        self.add_evt(wait)

    def end(self):
        sys.stdout.write("time: %i\n\n%s\n\nfinished.\n" \
                % (self.time, "\n".join(self.lines)))

