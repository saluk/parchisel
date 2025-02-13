from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

class Context:
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
        self.draw = ImageDraw.Draw(self.image)
    def draw_box(self, x, y, w, h, color):
        self.draw.rectangle((x, y, x+w, y+h), color)
    def draw_image(self, x, y, context):
        # Paint the contents of context into this context
        # Both contexts must match in type
        self.image.paste(context.image, (x, y))
    def draw_text(self, x, y, text):
        fnt = ImageFont.truetype("Raleway-VariableFont_wght.ttf", 60)
        self.draw.text((x,y), text, (0,0,0), fnt)
    def b64encoded(self):
        updated_image_buffer = BytesIO()
        self.image.save(updated_image_buffer, format="PNG")
        updated_image_bytes = updated_image_buffer.getvalue()
        s = 'data:image/png;base64,' + base64.b64encode(updated_image_bytes).decode('utf8')
        return s
    def save(self, filename):
        self.image.save(filename)