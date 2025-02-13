import drawsvg
def drawsvg_color(color):
    if isinstance(color, str) and color.startswith("#"):
        return color
    if isinstance(color, (list, tuple)) and (len(color) >= 3 and len(color) <= 4):
        if color[0] >= 0.0 and color[0] <= 1.0 and isinstance(color[0], float):
            return f"rgb({",".join(str(int(x*100))+"%" for x in color)})"
        else:
            return f"rgb({",".join(x+"%" for x in color)})"
class DrawSVGContext:
    def __init__(self, surface_width, surface_height, mode="RGBA"):
        self.resize(surface_width, surface_height, mode)
    @property
    def width(self):
        return self.image.width
    @property
    def height(self):
        return self.image.height
    def resize(self, sw, sh, mode="RGBA"):
        self.drawing = drawsvg.Drawing(sw, sh)
    def draw_box(self, x, y, w, h, color):
        r = drawsvg.Rectangle(x, y, w, h, fill=drawsvg_color(color))
    def draw_image(self, x, y, context):
        # Not implemented
        # Paint the contents of context into this context
        # Both contexts must match in type
        return
    def draw_text(self, x, y, text):
        # Not implemented
        #fnt = ImageFont.truetype("Raleway-VariableFont_wght.ttf", 60)
        #self.draw.text((x,y), text, (0,0,0), fnt)
        return
    def b64encoded(self):
        # Need to convert the generated svg to an image
        return ""


        updated_image_buffer = BytesIO()
        self.image.save(updated_image_buffer, format="PNG")
        updated_image_bytes = updated_image_buffer.getvalue()
        s = 'data:image/png;base64,' + base64.b64encode(updated_image_bytes).decode('utf8')
        return s
    def save(self, filename):
        self.image.save(filename)