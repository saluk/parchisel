import skia
import contextlib

@contextlib.contextmanager
def draw_target():
    surface = skia.Surface(256, 256)
    with surface as canvas:
        yield canvas
    image = surface.makeImageSnapshot()
    image.save("test.png")

with draw_target() as canvas:
    canvas.drawColor(skia.ColorWHITE)
    
    paint = skia.Paint(
        Style=skia.Paint.kFill_Style,
        AntiAlias=True,
        StrokeWidth=4,
        Color=0xFF4285F4)
    
    rect = skia.Rect.MakeXYWH(10, 10, 100, 160)
    canvas.drawRect(rect, paint)
    
    oval = skia.RRect()
    oval.setOval(rect)
    oval.offset(40, 80)
    paint.setColor(0xFFDB4437)
    canvas.drawRRect(oval, paint)
    
    paint.setColor(0xFF0F9D58)
    canvas.drawCircle(180, 50, 25, paint)
    
    rect.offset(80, 50)
    paint.setColor(0xFFF4B400)
    paint.setStyle(skia.Paint.kStroke_Style)
    canvas.drawRoundRect(rect, 10, 10, paint)