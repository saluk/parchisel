import base64
import skia

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
    def draw_image(self, x, y, image_file, width=None, height=None):
        image = skia.Image.open("data/"+image_file)
        if width or height:
            if not width: width = image.bounds().width()
            if not height: height = image.bounds().height()
            try:
                self.canvas.drawImageRect(
                    image, 
                    skia.Rect.MakeXYWH(x, y, width, height),
                    skia.SamplingOptions(skia.FilterMode.kLinear))
            except Exception as exc:
                import traceback
                traceback.print_exception(exc)
        else:
            self.canvas.drawImage(image, x, y)
    def draw_text(self, x, y, text, max_width=None, max_height=None, font_size=60, min_font_size=None):
        typeface = self.fontmgr.matchFamilyStyle('Raleway', skia.FontStyle.Bold())
        size_range = [font_size]
        if min_font_size:
            size_range = range(min_font_size, font_size, int((font_size-min_font_size)/4))
        for font_size in reversed(size_range):
            font = skia.Font(typeface, font_size)
            sections = []
            builder = skia.TextBlobBuilder()
            builder.allocRun("..", font, 0, font_size)
            space = builder.make()
            space_width = space.bounds().width()
            space_height = space.bounds().top()+space.bounds().height()
            builder.allocRun("h", font, 0, font_size)
            icon_blob = builder.make()
            icon_rect = icon_blob.bounds()
            icon_size = max([icon_rect.width(), icon_rect.height()])
            class TextSection:
                def __init__(self, text):
                    self.text = text
                    self.make_blob()
                    self.start_x = 0
                    self.start_y = 0
                def __repr__(self):
                    return f"T({self.text}, {self.width()})"
                def make_blob(self):
                    builder.allocRun(self.text, font, 0, font_size)
                    self.blob = builder.make()
                def width(self):
                    if not self.blob:
                        return 0
                    trailing_space = len(self.text)-len(self.text.rstrip())
                    return self.blob.bounds().left()+self.blob.bounds().width() + ((trailing_space) * space_width)
                def draw(self, ctx):
                    if not self.blob:
                        return
                    ctx.canvas.drawTextBlob(
                        self.blob, 
                        self.start_x, 
                        self.start_y, 
                        skia.Paint(AntiAlias=True))
            class IconSection:
                def __init__(self, filename):
                    self.filename = filename
                    self.start_x = 0
                    self.start_y = 0
                def __repr__(self):
                    return f"I({self.filename}, {self.width()})"
                def width(self):
                    return icon_size+space_width
                def draw(self, ctx):
                    ctx.draw_image(self.start_x+icon_rect.left(), self.start_y+icon_rect.top(), "images/"+self.filename, icon_size, icon_size)
            _text = text
            while _text:
                if _text.startswith("<") and ">" in _text:
                    icon = _text[:_text.find(">")+1]
                    sections.append(IconSection(icon[1:-1]))
                    _text = _text.replace(icon, "", 1)
                else:
                    if "<" in _text:
                        text_segment = _text[:_text.find("<")]
                        sections.append(TextSection(text_segment))
                        _text = _text.replace(text_segment, "", 1)
                    else:
                        sections.append(TextSection(_text))
                        break
            # Naive text wrapping
            def wrap_sections(sections, x1, y1):
                i = 0
                x = x1
                y = y1
                limit = 100
                wrapped = 0
                while i < len(sections) and limit:
                    limit -= 1
                    section = sections[i]
                    next_x = x+section.width()
                    if max_width and next_x > max_width:
                        wrapped += 1
                        overage = next_x-max_width
                        cut_off_percent = overage/section.width()
                        # if section is an icon, just move it to the next row
                        if isinstance(section, IconSection):
                            y += space_height
                            section.start_x = x1
                            section.start_y = y
                            i += 1
                            continue
                        else:
                            text = section.text
                            len_text = len(text)
                            if cut_off_percent > 1:
                                cut_off_percent = 1
                            char_split = int((1.0-cut_off_percent) * len_text)
                            # split at space?
                            if " " in text[:char_split]:
                                split_at = text[:char_split].rfind(" ")
                                left = text[:split_at]
                                right = text[split_at:].lstrip()
                            else:
                                left = text[:char_split-1]+"-"
                                right = text[char_split-1:].lstrip()
                            section = TextSection(left)
                            sections[i] = section
                            section.start_x = x
                            section.start_y = y

                            right_section = TextSection(right)
                            x = x1
                            y+=space_height
                            sections.insert(i+1, right_section)
                            i += 1
                            continue
                    else:
                        section.start_x = x
                        section.start_y = y
                        x = next_x
                    i += 1
                return wrapped
            wrapped = wrap_sections(sections, x, y)
            if wrapped > 0 and min_font_size and font_size > min_font_size:
                continue
            self.canvas.save()
            if max_height or max_width:
                self.canvas.clipRect(skia.Rect.MakeXYWH(x, y, max_width or self.width(), max_height or self.height()))
            for section in sections:
                section.draw(self)
            self.canvas.restore()
            break
    def b64encoded(self):
        self.surface.flushAndSubmit()
        image = self.surface.makeImageSnapshot()
        data = image.encodeToData(skia.kPNG, 100)
        s = 'data:image/png;base64,' + base64.b64encode(data).decode('utf8')
        return s
    def save(self, filename):
        self.surface.makeImageSnapshot().save(filename)