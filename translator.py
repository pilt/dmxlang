# -*- coding: utf-8 -*-

from statements import *

class Translate(object):
    def __init__(self, input_file):
        self.input_file = input_file

    def walk(self, node):
        if type(node) == DoStatement:
            self.on_do(node)
        elif type(node) == ToStatement:
            self.on_to(node)
        elif type(node) == WaitStatement:
            self.on_wait(node)
        
    def traverse(self, tree): 
        self.start()
        for node in tree:
            self.walk(node)
        self.end()

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

