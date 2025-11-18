from nicegui import ui

# A class to handle mounting and updating a virtual table display
class TableDisplay(ui.element):
    def __init__(self, width, height) -> None:
        super().__init__()
        self._props['width'] = width
        self._props['height'] = height