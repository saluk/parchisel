card.resize(400,400)
card.draw_box(0, 0, 400, 400, (50, 0, 0, 255))
card.draw_box(1, 1, 398, 398, (255, 215, 255, 255))
card.draw_box(100, 150, 200, 200, (100,100,100,50))
if row["Icon"]:
    card.draw_image(600-64,0,row["Icon"])
y = 50
x = 50
for i in range(8):
    card.draw_box(x, y, 120, 20, (155,50,20,120))
    y += 30
    x += 3
    if y > 400:
        y -= 450

name_width = 220
name_height = 120
name_x = 20
name_y = 50
card.draw_box(name_x, name_y, name_width, name_height, (200,200,200,225))
card.draw_text(name_x+5,name_y+5,row["Name"]+" hello to you you beautiful person",name_width,name_height,30, 24)
card.draw_text(300, 15, str(row.get("Power", "5"))+"/"+row.get("HP", "5"), 75, 50, font_size=30)