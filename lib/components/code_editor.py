from nicegui import ui

class CodeEditor:
    def __init__(self, view):
        self.view = view
        self.template = None
        self.new_filename = ""
        self.ui_editor = None
    def set_new_filename(self, fn):
        self.new_filename = fn
    async def update_code(self, code):
        self.template.code = code
        # TODO only save if things are rendering OK
        # We could have a button to force save
        self.template.save()
        # TODO make this a helper function on the view
        if await self.view.project.dirty_outputs(for_templates=[self.template.name], for_outputs=self.view.viewed_output):   # only redraw outputs that use this template
            await self.view.render_images(self.view.image_element_list, self.view.output_list)

    def create_template(self, template_name):
        t = self.view.project.add_template(template_name)
        self.change_template(t.name)

    def change_template(self, template_name):
        self.template = self.view.project.templates[template_name]
        self.build.refresh()

    def queue_update(self, value):
        if getattr(self, "code_update_timer", None):
            self.code_update_timer.deactivate()
        self.code_update_timer = ui.timer(0.5, lambda: self.update_code(value), once=True)

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

        if not self.template:
            if self.view.project.templates:
                self.template = list(self.view.project.templates.values())[0]
        with ui.grid(columns="80px 550px"):
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
                    on_change=lambda e: self.queue_update(e.value)
                ).classes("w-550px")
                self.ui_editor.tailwind.height("52")
