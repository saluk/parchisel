from nicegui import ui

from lib.javascript_util import element_run_javascript

# needed to inspect our drawing commands
import lib.draw_context
from lib import util

class CodeEditor:
    def __init__(self, view):
        self.view = view
        self.template = None
        self.new_filename = ""
        self.ui_editor = None
    def set_new_filename(self, fn):
        self.new_filename = fn
    async def after_code_update(self):
        # TODO only save if things are rendering OK
        # We could have a button to force save
        self.template.save()
        # TODO make this a helper function on the view
        if await self.view.project.dirty_outputs(for_templates=[self.template.name], for_outputs=self.view.project.viewed_output):   # only redraw outputs that use this template
            await self.view.render_images(self.view.image_element_list, self.view.output_list)

    def create_template(self, template_name):
        t = self.view.project.add_template(template_name)
        self.change_template(t.name)

    def change_template(self, template_name):
        self.template = self.view.project.templates[template_name]
        self.build.refresh()

    async def on_change(self, e):
        value = e.value
        self.template.code = e.value
        await self.update_fancy_line()
        self.queue_update()

    async def on_cursor_move(self, e):
        await self.update_fancy_line()

    def queue_update(self):
        if getattr(self, "code_update_timer", None):
            self.code_update_timer.deactivate()
        self.code_update_timer = ui.timer(0.5, lambda: self.after_code_update(), once=True)

    async def get_cursor(self):
        selected = await element_run_javascript(
            self.ui_editor, 
            f"""return element.editor.viewState.state.selection""")
        cursor = selected["ranges"][0]["anchor"]
        def get_line(cursor):
            return self.template.code[:cursor].count("\n")
        
        split_lines = self.template.code.split("\n")
        cur_line = split_lines[get_line(cursor)]
        line_start = self.template.code[:cursor].rfind("\n")
        if line_start < 0:
            line_start = 0
        cursor_in_line = cursor-line_start
        return {"cursor": cursor, "line": cur_line, "line_number":get_line(cursor), "cursor_in_line": cursor_in_line}        

    async def insert_code(self, code):
        cursor = (await self.get_cursor())["cursor"]
        self.template.code = self.template.code[:cursor] + code + self.template.code[cursor:]
        self.ui_editor.value = self.template.code

    def build_function_list(self):
        with ui.scroll_area():
            with ui.list():
                for method_name in dir(lib.draw_context.DrawContextSkia):
                    func = getattr(lib.draw_context.DrawContextSkia, method_name)
                    if func.__doc__ and func.__doc__[0] == ":":
                        with ui.item():
                            ui.button("<").on_click(
                                lambda method_name=method_name: self.insert_code("card."+method_name)
                            ).classes("m-3")
                            ui.label("card."+func.__doc__[1:])

    async def build_fancy_context(self, cursor):
        import lib.webelements.interactive_context as ic
        interactive = ic.make_interactive(self.template, cursor["line_number"], self.view)
        if interactive:
            await interactive.build()
            return

        import inspect
        for method_name in dir(lib.draw_context.DrawContextSkia):
            if "card."+method_name in cursor["line"]:
                func = getattr(lib.draw_context.DrawContextSkia, method_name)
                sig = inspect.signature(func)
                params = [str(param) for param in sig.parameters.values()][1:]
                #Figure out which parameter cursor is over
                check_string:str = cursor["line"][:cursor["cursor_in_line"]-1]
                which_param = util.find_argument_in_line(check_string)
                params[which_param] = f"<b>{params[which_param]}</b>"
                t = ", ".join(params)
                t += "<br>"
                t += inspect.getdoc(func) or ""
                ui.html(t)

    async def update_fancy_line(self):
        cursor = await self.get_cursor()
        
        self.fancy_line.clear()
        with self.fancy_line:
            if not cursor["line"].strip():
                self.build_function_list()
            else:
                await self.build_fancy_context(cursor)


    @ui.refreshable
    def build(self):

        with ui.dialog() as new_template_dialog, ui.card():
            ui.input(label="New template filename:",
                    on_change=lambda e: self.set_new_filename(e.value))
            with ui.button_group():
                ui.button('Cancel', on_click=new_template_dialog.close)
                def create_cb():
                    self.create_template(self.new_filename)
                    new_template_dialog.close()
                ui.button("Create", on_click=create_cb)

        if not self.view.project:
            ui.label("No project loaded")
            return
        if not self.template:
            if self.view.project.templates:
                self.template = list(self.view.project.templates.values())[0]
        with ui.grid(columns="80px 550px 400px"):
            with ui.column():
                ui.button('New', on_click=lambda:new_template_dialog.open() )
                if not self.view.project or not self.view.project.templates:
                    return
                self.ui_template_list = ui.select(list(self.view.project.templates.keys()), 
                    on_change=lambda e: self.change_template(e.value), 
                    value=self.template.name)
            
            if self.template:
                self.ui_editor = ui.codemirror(
                    value=self.template.code, language="Python", theme="abcdef",
                    on_change=lambda e: self.on_change(e)
                ).classes("w-550px")
                self.ui_editor.on('keydown.left', self.on_cursor_move)
                self.ui_editor.on('keydown.right', self.on_cursor_move)
                self.ui_editor.on('keydown.up', self.on_cursor_move)
                self.ui_editor.on('keydown.down', self.on_cursor_move)
                self.ui_editor.on('click', self.on_cursor_move)
                self.ui_editor.tailwind.height("52")
                # How to determine what line of code user is on?
            else:
                ui.card()
            
            self.fancy_line = ui.card()
