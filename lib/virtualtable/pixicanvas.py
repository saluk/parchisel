from nicegui import ui

class PixiCanvas(ui.element,
    component='pixicanvas.js',
    dependencies=['dist/pixi.js']):
    def __init__(self, width, height) -> None:
        super().__init__()
        self._props['width'] = width
        self._props['height'] = height