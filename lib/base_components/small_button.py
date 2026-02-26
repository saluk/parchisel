from nicegui import ui


class SmallButton(ui.button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.props("size=sm dense")
