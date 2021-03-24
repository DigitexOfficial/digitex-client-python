class Listener:
    def wait_for_message(self, **kwargs):
        for message in self:
            if all(getattr(message, key) == kwargs[key] for key in kwargs):
                return message
            else:
                self.ack()

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def ack(self):
        pass
