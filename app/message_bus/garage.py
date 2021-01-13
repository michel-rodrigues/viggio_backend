from collections import defaultdict


class MessageBus:

    def __init__(self):
        self.handlers = defaultdict(list)

    def handle(self, message):
        subscribers = self.handlers[message.NAME]
        for handle in subscribers:
            handle(message)

    def register(self, message, handler, *args):
        self.handlers[message.NAME].append(handler)
