from PIL import Image
import base64
import skia
import numpy
import math

# SKIA advantage
#   - full featured and modern
# disadvantage
#   - documentation weirdness between python binding and c++


class SkiaContext:
    step = 0
    fontmgr = skia.FontMgr.New_Custom_Directory(".")
    def __init__(self, surface_width, surface_height, mode="RGBA"):
        self.surface = None
        self.canvas = None
        self.resize(surface_width, surface_height, mode)
    @property
    def width(self):
        return self.surface.width()
    @property
    def height(self):
        return self.surface.height()
    def resize(self, sw, sh, mode="RGBA"):
        if self.surface:
            del self.surface
        if self.canvas:
            del self.canvas
        self.surface = skia.Surface.MakeRasterN32Premul(sw, sh)
        self.canvas = self.surface.getCanvas()
    def clear(self, color):
        self.canvas.clear(skia.ColorSetARGB(color[3], color[0], color[1], color[2]))
    def draw_box(self, x, y, w, h, color):
        paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            AntiAlias=True,
            StrokeWidth=4,
            Color=skia.ColorSetARGB(color[3], color[0], color[1], color[2])
        )
        rect = skia.Rect.MakeXYWH(x, y, w, h)
        self.canvas.drawRect(rect, paint)
    def draw_context(self, x, y, context):
        # Paint the contents of context into this context
        # Both contexts must match in type
        context.surface.draw(self.canvas, x, y)
    def draw_image(self, x, y, image_file):
        image = skia.Image.open("data/"+image_file)
        self.canvas.drawImage(image, x, y)
    def draw_text(self, x, y, text):
        print(list(self.fontmgr))
        styles = self.fontmgr.matchFamily('Raleway')
        print(styles)
        typeface = styles.createTypeface(0)
        print(typeface)
        builder = skia.TextBlobBuilder()
        builder.allocRun(text, skia.Font(typeface, 60), 0, 60)
        blob = builder.make()
        self.canvas.drawTextBlob(blob, x, y, skia.Paint(AntiAlias=True))
    def b64encoded(self):
        self.surface.flushAndSubmit()
        image = self.surface.makeImageSnapshot()
        data = image.encodeToData(skia.kPNG, 100)
        s = 'data:image/png;base64,' + base64.b64encode(data).decode('utf8')
        return s
    def save(self, filename):
        self.surface.makeImageSnapshot().save(filename)