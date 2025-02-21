import random
def rows():
    for i in range(40):
        name = [random.choice("abcdefghijklmnopqrstuvwxyz") for i in range(random.randint(5,10))]
        yield ({
            "Name": "".join(name).capitalize(), 
            "Hp": random.randint(0,100),
            "Power": random.randint(0,100),
            "Icon":"purple_sphere.png"
        })