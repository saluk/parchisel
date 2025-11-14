# Defines a component

# A single card component, unique backs
# Functionally: build a component whose faces are generated from datasource x, and whose backs are generated from datasource y
uniqueback = {
    "name": "loot",
    "sides": [
        {
            "name": "front",
            "datasource": "front1",
            "range": [0,10],
            "repeat": False
        },
        {
            "name": "back",
            "datasource": "back1",
            "range": [0,10],
            "repeat": False
        },
    ]
}

# A single card component, the same backs
# Functionally: build a component whose faces are generated from datasource x, and whose backs are all an identical copy of datasource y
sameback = {
    "name": "loot",
    "sides": [
        {
            "name": "front",
            "datasource": "front1",
            "range": [0,10],
            "repeat": False
        },
        {
            "name": "back",
            "datasource": "backimage",
            "range": [0,1],
            "repeat": True
        },
    ]
}

# A dice component
# Functionally: take datasource x, and turn each row into a side
die = {
    "name": "die",
    "sides": [
        {
            "name": "1",
            "datasource": "diefaces",
            "range": [0,1],
            "repeat": False
        },
        {
            "name": "2",
            "datasource": "diefaces",
            "range": [1,2],
            "repeat": False
        },
        {
            "name": "3",
            "datasource": "diefaces",
            "range": [2,3],
            "repeat": False
        },
        {
            "name": "4",
            "datasource": "diefaces",
            "range": [3,4],
            "repeat": False
        },
        {
            "name": "5",
            "datasource": "diefaces",
            "range": [4,5],
            "repeat": False
        },
        {
            "name": "6",
            "datasource": "diefaces",
            "range": [5,6],
            "repeat": False
        },
    ]
}