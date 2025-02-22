card.draw_box(100, 0, 640, 480, (155, 255, 255, 255))
card.draw_box(0,0,300,100,(50,250,100,50))
if 1:#row["Icon"]:
    card.draw_image(0,20,row["Icon"])
card.draw_text(0,400,row["Name"])