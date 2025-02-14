from PIL import Image
import base64
import skia
import numpy

# SKIA advantage
#   - full featured and modern
# disadvantage
#   - documentation weirdness between python binding and c++


class SkiaContext:
    step = 0
    def __init__(self, surface_width, surface_height, mode="RGBA"):
        self.surface = None
        self.canvas = None
        self.resize(surface_width, surface_height, mode)
        #self.fonts = skia.textlayout.FontCollection()
        #self.fonts.setDefaultFontManager(skia.FontMgr.New_Custom_Directory("."))
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
        #print("make surface")
        #self.surface = skia.Surface(numpy.zeros((sh,sw,4), numpy.uint8))
        # self.surface = skia.Surface.Raster(
        #     skia.ImageInfo(
        #         sw, 
        #         sh, 
        #         skia.ColorType.kRGBA_8888_ColorType, 
        #         skia.AlphaType.kPremul_AlphaType, 
        #         skia.ColorSpace.MakeSRGB()
        #     )
        # )
        self.surface = skia.Surface.MakeRasterN32Premul(sw, sh)
        self.canvas = self.surface.getCanvas()
        #print("made surface")
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
        return
        bg = Image.new("RGBA", self.image.size)
        bg.putalpha(0)
        image = Image.open("data/"+image_file)
        image.load()
        bg.paste(image, (x, y))
        self.image.putalpha(255)
        self.image.paste(Image.alpha_composite(self.image, bg), (0,0))
        #self.draw = ImageDraw.Draw(self.image, "RGBA")
    def draw_text(self, x, y, text):
        return
        style = skia.textlayout.ParagraphStyle()
        builder = skia.textlayout.ParagraphBuilder.make(style, self.fonts, skia.Unicodes.ICU.Make())
        fnt = skia.Font(skia.Typeface.MakeFromFile("Raleway-VariableFont_wght.ttf"), 60)
        #self.draw.text((x,y), text, (0,0,0), fnt)
    def b64encoded(self):
        self.surface.flushAndSubmit()
        image = self.surface.makeImageSnapshot()
        data = image.encodeToData(skia.kPNG, 100)
        s = 'data:image/png;base64,' + base64.b64encode(data).decode('utf8')
        return s
    def save(self, filename):
        self.surface.makeImageSnapshot().save(filename)