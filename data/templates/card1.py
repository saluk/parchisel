card.resize(400,400)
card.draw_box(0, 0, 400, 400, (255, 255, 255, 255))
card.draw_box(100, 150, 200, 200, (100,100,100,50))
if row["Icon"]:
    card.draw_image(400-64,0,row["Icon"])
card.draw_text(20,0,"N:"+row['Name'])
y = 50
x = 50
for i in range(8):
    card.draw_box(x, y, 120, 20, (155,50,20,120))
    y += 25
