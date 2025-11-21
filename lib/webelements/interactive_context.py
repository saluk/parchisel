from collections import defaultdict

from nicegui import ui, ElementFilter

from lib.outputs import Output
from lib.draw_context import DrawContextSkia
from lib.data.datasource import TempDataSource

def make_inspectable_func(f):
    import inspect
    sig = inspect.signature(f)
    def getargs(*args, **kwargs):
        new_args = {}
        for k in sig.parameters.keys():
            if sig.parameters[k].default != inspect._empty:
                new_args[k] = sig.parameters[k].default
        # skip self
        param_keys = list(sig.parameters.keys())[1:]
        for a in args:
            v = param_keys.pop(0)
            print("incoming arg", a, "param_key", v)
            new_args[v] = a
        for k in kwargs:
            new_args[k] = kwargs[k]
        return new_args
    return getargs

def apply_args_to_func(f, args_dict):
    import inspect
    sig = inspect.signature(f)
    # strings to join
    args = []
    # output positional_only arguments
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            args.append(args_dict.get(param.name))
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            args.append(args_dict.get(param.name))
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            args.append(args_dict.get(param.name))
    for param in sig.parameters.values():
        if param.kind in [
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD
        ]:
            args.append(param.name+"="+repr(args_dict.get(param.name)))
    return f.__name__+f"({", ".join(args)})"

# TODO we actually need to execute the script up to the line, within the proper context
# and then run this line so it has all of the local variables
def adapt_line(template, line_number):
    line = template.get_line(line_number)
    line = line.strip()
    first_paren = line.find("(")
    func = line[:first_paren]
    # We usually do card.draw_box
    method = func.split(".")[1]
    parens = line[first_paren:]
    ifunc = make_inspectable_func(getattr(DrawContextSkia, method))
    row = defaultdict(lambda x:"stub")
    glob = {
        "row": row,
        "ifunc": ifunc
    }
    # TODO execution option on template
    #template.execute_until_line(line_number, glob)
    args = eval("ifunc"+parens, glob)
    return method, args

class InteractiveOutput:
    def __init__(self, template, line_number, view):
        # Dont need a template field, we're going to pass the edited template in
        # data source name - we need to make and pass a data source
        self.data_source = TempDataSource()
        self.output = Output("", "", template=template, data_source=self.data_source)
        self.view = view
        self.template = template
        self.line_number = line_number
        self.dragging = None

        method, self.args = adapt_line(self.template, self.line_number)

    async def build(self):
        await self.output.render(self.view.project)
        self.interact = ui.interactive_image(
            await self.output.b64encoded(self.view.project), 
            content = self.get_svg()
        ).on('svg:pointerdown', lambda e: self.pointerdown(e.args['element_id'])
        )
        
        self.view.tabs.on('mouseup', lambda e: self.mouseup())
        self.view.tabs.on('mousemove', lambda e: self.mousemove(e))
    
    def pointerdown(self, element_id):
        if not self.dragging:
            self.dragging = element_id
    
    def mouseup(self):
        if self.dragging:
            self.dragging = None
    
    def mousemove(self, e):
        if not self.dragging:
            return
        amt = e.args['movementX'], e.args['movementY']
        self.move_component(self.dragging, amt)
        self.regen_svg()
    
    def regen_svg(self):
        self.interact.content = self.get_svg()
        self.interact.update()

    def get_svg(self):
        pass

    def move_component(self, element_id, amt):
        if hasattr(self, "move_component_"+element_id):
            return getattr(self, "move_component_"+element_id)(amt)

class DrawRectInteractiveOutput(InteractiveOutput):
    method = "draw_box"
    def get_svg(self):
        # get from line
        rect_x = self.args["x"]
        rect_y = self.args["y"]
        rect_width = self.args["w"]
        rect_height = self.args["h"]
        print(rect_x, rect_y, rect_width, rect_height)
        return f'''<rect id="therect" x="{rect_x}" y="{rect_y}" width="{rect_width}" height="{rect_height}" pointer-events="all" fill-opacity="50%"/>
                    <rect id="right" x="{rect_x+rect_width-10}" y="{rect_y+rect_height/2-10}" width="20" height="20" pointer-events="all"/>
                    <rect id="bottom" x="{rect_x+rect_width/2-10}" y="{rect_y+rect_height-10}" width="20" height="20" pointer-events="all"/>'''
    def move_component_therect(self, amt):
        self.args["x"] += amt[0]
        self.args["y"] += amt[1]
    def move_component_right(self, amt):
        self.args["w"] += amt[0]
    def move_component_bottom(self, amt):
        self.args["h"] += amt[1]

def make_interactive(template, line_num, view):
    # TODO I might be not implementing interactive outputs
    return
    method, args = adapt_line(template, line_num)
    for clsn in list(globals().keys()):
        cls = eval(clsn)
        #if hasattr(cls,"method") and cls.method == method:
        #    return cls(template, line_num, view)