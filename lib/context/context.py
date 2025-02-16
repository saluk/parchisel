from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

# PIL advantage
#   - simple library
# disadvantage
#   - can't adjust vectors later or convert to svg
#   - can't well support mixing 2 images with alpha
#       (maybe we can force this to work with blending)

image_draw_init = ImageDraw.__init__
def image_draw_init_force_blend(self, *args, **kwargs):
    image_draw_init(self, *args, **kwargs)
    self.draw = Image.core.draw(self.im, 1)
ImageDraw.__init__ = image_draw_init_force_blend

class Context:
    step = 0
    def __init__(self, surface_width, surface_height, mode="RGBA"):
        self.resize(surface_width, surface_height, mode)
    @property
    def width(self):
        return self.image.width
    @property
    def height(self):
        return self.image.height
    def resize(self, sw, sh, mode="RGBA"):
        self.image = Image.new(mode, (sw, sh))
        self.draw = ImageDraw.Draw(self.image, "RGBA")
    def clear(self, color):
        self.draw.rectangle((0,0,self.image.size[0],self.image.size[1]), color)
    def log(self, image):
        return
        image.save(f"step{Context.step}.png")
        Context.step += 1
    def draw_box(self, x, y, w, h, color):
        self.draw.rectangle((x, y, x+w, y+h), color)
    def draw_context(self, x, y, context):
        # Paint the contents of context into this context
        # Both contexts must match in type
        self.image.paste(context.image, (x, y))
    def draw_image(self, x, y, image_file):
        self.log(self.image)
        bg = Image.new("RGBA", self.image.size)
        bg.putalpha(0)
        image = Image.open("data/"+image_file)
        image.load()
        bg.paste(image, (x, y))
        self.log(bg)
        self.image.putalpha(255)
        self.log(self.image)
        self.image.paste(Image.alpha_composite(self.image, bg), (0,0))
        #self.draw = ImageDraw.Draw(self.image, "RGBA")
        self.log(self.image)
    def draw_text(self, x, y, text):
        fnt = ImageFont.truetype("Raleway-VariableFont_wght.ttf", 60)
        self.draw.text((x,y), text, (0,0,0), fnt)
        self.log(self.image)
    def b64encoded(self):
        updated_image_buffer = BytesIO()
        self.image.save(updated_image_buffer, format="PNG")
        updated_image_bytes = updated_image_buffer.getvalue()
        s = 'data:image/png;base64,' + base64.b64encode(updated_image_bytes).decode('utf8')
        return s
    def save(self, filename):
        self.image.save(filename)