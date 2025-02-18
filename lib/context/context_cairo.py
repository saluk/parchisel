import cairo

# Cairo benefits:
#   - many advanced drawing functions
#   - exports to pdf and svg
# Cairo flaws:
#   - text rendering primitive
#   - interface confusing

def cairo_color(color):
    if isinstance(color, (list, tuple)) and (len(color) >= 3 and len(color) <= 4):
        if color[0] >= 0.0 and color[0] <= 1.0 and isinstance(color[0], float):
            return color
        else:
            color = tuple([float(x)/255.0 for x in color])
            return color
    return (1.0, 0, 1.0, 1.0)
class CairoContext:
    def __init__(self, surface_width, surface_height, mode="RGBA"):
        self.resize(surface_width, surface_height, mode)
    @property
    def width(self):
        return self.c_surface.get_width()
    @property
    def height(self):
        return self.c_surface.get_height()
    def resize(self, sw, sh, mode="RGBA"):
        self.c_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
        self.c_context = cairo.Context(self.c_surface)
    def draw_box(self, x, y, w, h, color):
        self.draw_polygon([
            [x, y],
            [x+w, y],
            [x+w, y+h],
            [x, y+h]
        ], color)
    def draw_polygon(self, points, color):
        self.c_context.save()

        self.c_context.new_path()
        self.c_context.set_line_width(1)
        self.c_context.set_source_rgba(*cairo_color(color))

        self.c_context.move_to(points[-1][0], points[-1][1])
        for p in points:
            self.c_context.line_to(p[0], p[1])
        self.c_context.fill()

        self.c_context.restore()
    def draw_context(self, x, y, context):
        self.c_context.save()

        #self.c_context.new_path()
        self.c_context.translate(x, y)
        self.c_context.set_source_surface(context.c_surface)
        self.c_context.paint()

        self.c_context.restore()
    def draw_text(self, x, y, text):
        pass
        #fnt = ImageFont.truetype("Raleway-VariableFont_wght.ttf", 60)
        #self.draw.text((x,y), text, (0,0,0), fnt)
    def b64encoded(self):
        updated_image_buffer = BytesIO()
        pil_image = Image.frombuffer(
            "RGBA", 
            (self.width, self.height),
            self.c_surface.get_data().tobytes(),
            "raw",
            "BGRa",
            self.c_surface.get_stride())
        pil_image.save(updated_image_buffer, format="PNG")
        updated_image_bytes = updated_image_buffer.getvalue()
        s = 'data:image/png;base64,' + base64.b64encode(updated_image_bytes).decode('utf8')
        return s
    def save(self, filename):
        # Note this will only save to png
        self.c_surface.write_to_png(filename)