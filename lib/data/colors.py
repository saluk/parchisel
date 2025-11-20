# We can convert colors as data or as strings from one of the following formats to class which can give rgba256 tuple:
#   3, 6, and 8 character hex <str> rgb/rgba:
#       #000
#       #000000
#       #00000000
#   3 and 4 component rgb, rgba as int from 0-255 <str><tuple><list>:
#       (0,50,255)
#       (0,50,255,255)
#   3 and 4 component rgb, rgba as int from 0-255 with "rgb" or "rgba" at the beginning
#       rgb(0,50,255)
#       rgba(0,50,255,255)
#   as a name <str>:
#       red
#   as a name plus percentage:
#       red,50
import traceback
import colour

class ColorException(Exception):
    pass

def detect_str_format(color):
    if "(" in color or ")" in color or "," in color:
        return detect_componentstring_format(color)
    return detect_strhex_format(color)
def detect_strhex_format(color):
    if color.startswith("#"):
        color = color.replace("#","")
    second_color = None
    for c in color:
        if not c.isnumeric():
            try:
                second_type, second_color = detect_component_list(colour.Color(color).get_rgb())
            except:
                pass
    # We had non numeric characters and found a color
    if second_color:
        return "named", second_color
    if len(color) in [3,6,8]:
        try:
            hex = int(color, 16)
            return detect_component_list([int(color[i:i+2],16) for i in range(0, len(color), 2)])
        except:
            traceback.print_exc()
    raise ColorException(f"'{color}' could not be parsed")
def detect_componentstring_format(color):
    color = color.replace("rgba","").replace("rgb","").replace("(","").replace(")","")
    components = []
    for comp in color.split(","):
        try:
            if "." in comp:
                components.append(float(comp))
            else:
                components.append(int(comp))
        except:
            raise ColorException(f"Non-numeric component in color string {color}")
    return detect_component_list(components)
def detect_component_list(components):
    if not len(components) in [3,4]:
        raise ColorException(f"List of color components must be of length 3 or 4 {components}")
    numbers = []
    for comp in components:
        try:
            i = int(comp)
            f = float(comp)
            if i==f:
                numbers.append(i)
            numbers.append(f)
        except:
            raise ColorException("Non-numeric component in color format {color}, {comp}")
    if any(comp>1 for comp in components) and not all(type(comp)==float for comp in components):
        ints = [int(comp) for comp in components]
    else:
        ints =[int(float(comp)*255) for comp in components]
    if not all([component>=0 and component <= 255 for component in ints]):
        raise ColorException(f"Color component out of bounds, must be between 0 and 255: {ints}")
    return "list", tuple(ints)
def detect_format(color):
    if type(color) == str:
        return detect_str_format(color)
    if type(color) in [tuple, list]:
        return detect_component_list(color)
    raise ColorException(f"Unknown color input format: {color}.")

class Color:
    def __init__(self, input_color):
        self.input_format, self.int_components = detect_format(input_color)
        self.input_color = input_color
        if len(self.int_components) == 3:
            self.int_components = tuple(list(self.int_components)+[255])
    def __repr__(self):
        return f"Color: Type:{self.input_format} RGBA256:{self.rgba256()}"
    def rgba256(self):
        return self.int_components

strings = [
"rgba(10,15,25,0)",
"rgba(1.0,15,25,0)",
"rgba(1.0,1.0,1.0,0)",
"red",
"000000",
"#00FF8F",
"#10FF8Fb0",
"(100, 200, 220)"
]
for string in strings:
    try:
        print(repr(string), Color(string))
    except:
        traceback.print_exc()