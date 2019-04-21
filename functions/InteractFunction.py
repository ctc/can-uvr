import functions.BasicFunction

class InteractFunction(functions.BasicFunction):
    _buttons = None

    def _init_buttons(self):
        self._buttons = []

    @property
    def buttons(self):
        if self._buttons is None:
            self._init_buttons()
        return self._buttons