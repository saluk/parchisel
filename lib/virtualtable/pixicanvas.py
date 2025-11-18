from lib.virtualtable.tabledisplay import TableDisplay

class PixiCanvas(TableDisplay,
    component='pixicanvas.js',
    dependencies=['dist/pixi.js']):
    pass