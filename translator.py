# -*- coding: utf-8 -*-

class Translate(object):
    def __init__(self, input_file):
        self.input_file = input_file

    def start(self):
        raise NotImplementedError()

    def on_do(self, do):
        raise NotImplementedError()
    
    def on_to(self, to):
        raise NotImplementedError()

    def on_wait(self, wait):
        raise NotImplementedError()

    def end(self):
        raise NotImplementedError()

