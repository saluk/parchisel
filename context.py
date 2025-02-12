from PIL import Image, ImageDraw, ImageFont

import cairo

class Context:
    def __init__(self, surface_width, surface_height, mode="RGBA"):
        self.resize(surface_width, surface_height, mode)
    def resize(self, sw, sh, mode="RGBA"):
        self.image = Image.new(mode, (sw, sh))
        self.draw = ImageDraw.Draw(self.image)
    def draw_box(self, x, y, w, h, color):
        self.draw.rectangle((x, y, x+w, y+h), color)
    def draw_image(self, x, y, image):
        self.image.paste(image, (x, y))
    def draw_text(self, x, y, text):
        fnt = ImageFont.truetype("Raleway-VariableFont_wght.ttf", 60)
        self.draw.text((x,y), text, (0,0,0), fnt)