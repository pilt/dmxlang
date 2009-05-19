# -*- coding: utf-8 -*-

from statements import *

class TranslationError(Exception):
    pass

class BaseTranslate(object):
    def start(self):
        pass

    def always(self, node):
        pass

    def walk(self, node):
        raise NotImplementedError()

    def end(self):
        pass
        
    def traverse(self, tree): 
        self.start()
        for node in tree:
            self.walk(node)
        self.end()


class MasterTranslate(BaseTranslate):
    def walk(self, node):
        self.always(node)
        if type(node) == ProcessStatement:
            self.on_process(node)
        else:
            raise TranslationError("unknown node %r" % node)

    def on_process(self, process):
        raise NotImplementedError()


class ProcessTranslate(BaseTranslate):
    def walk(self, node):
        self.always(node)
        if type(node) == DoStatement:
            self.on_do(node)
        elif type(node) == ToStatement:
            self.on_to(node)
        elif type(node) == WaitStatement:
            self.on_wait(node)
        elif type(node) == UpdateStatement:
            self.on_update(node)
        else:
            raise TranslationError("unknown node %r" % node)

    def on_do(self, do):
        raise NotImplementedError()
    
    def on_to(self, to):
        raise NotImplementedError()

    def on_wait(self, wait):
        raise NotImplementedError()

    def on_update(self, update):
        raise NotImplementedError()
