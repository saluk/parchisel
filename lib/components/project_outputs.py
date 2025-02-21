import random
from nicegui import ui

from lib.outputs import Output

class ProjectOutputs:
    def __init__(self, ov):
        self.view = ov
        self.update_timer = None
    def refresh(self):
        self.build.refresh()
    def queue_update(self, func, delay=0.5):
        if self.update_timer:
            self.update_timer.deactivate()
        self.update_timer = ui.timer(delay, func, once=True)
    @ui.refreshable
    def build(self):
        ov = self.view
        project = ov.project
        with ui.grid(columns=5).classes("w-full font-bold"):
            ui.label("Name");ui.label("Data Source");ui.label("Template");ui.label("Field");ui.label("")
        for out_key in project.outputs:
            out = project.outputs[out_key]
            def unlink_output(out=out):
                out.rendered_string = ""
                project.remove_output(out)
                ov.refresh_outputs()
            with ui.grid(columns=5).classes("w-full"):
                imp = ui.input("path", value=out.file_name)
                def edit_name(inp=imp, out=out):
                    project.rename_output(out, inp.value)
                    ov.refresh_outputs()
                imp.on('keydown.enter', edit_name)
                imp.on('blur', edit_name)

                # TODO popout data source selection to choose both source and range
                def select_source(evt, out=out, project=project):
                    out.data_source_name = evt.value
                    out.rendered_string = ""
                    ov.refresh_outputs()
                options = [source.source for source in project.data_sources]
                value = ""
                if out.data_source_name in options:
                    value = out.data_source_name
                with ui.column():
                    ui.select([""] + [source.source for source in project.data_sources], value=value,
                        on_change=select_source)
                    total_range = out.get_card_range(project, True)
                    card_range = out.get_card_range(project)
                    def set_range(e, out=out):
                        out.card_range = (e.value["min"],e.value["max"])
                        out.rendered_string = ""
                        self.queue_update(ov.refresh_outputs)
                    ui.range(
                        min=total_range[0], 
                        max=total_range[1], 
                        value={'min': card_range[0], 'max': card_range[1]}
                    ).props('label-always snap').on_value_change(lambda e, out=out: set_range(e, out))
                def select_template(evt, out=out, project=project):
                    out.template_name = evt.value
                    out.rendered_string = ""
                    ov.refresh_outputs()
                ui.select([""] + [name for name in project.templates], value=out.template_name,
                        on_change=select_template)
                
                def select_template_field(evt, out=out, project=project):
                    out.template_field = evt.value
                    out.rendered_string = ""
                    ov.refresh_outputs()
                ds = project.get_data_source(out.data_source_name)
                if ds:
                    values = [key for key in ds.fieldnames]
                    value = out.template_field
                    if value not in values:
                        value = ""
                    ui.select([""] + values, value=value,
                            on_change=select_template_field)

                ui.button('Remove', on_click=unlink_output)
        ui.separator()
        def add_output():
            new_out = Output("", "new_output.png")
            # Choose a data source that isn't output yet, or pick at random
            used = set([out.data_source_name for out in project.outputs.values()])
            for s in project.data_sources:
                if s.source not in used:
                    new_out.data_source_name = s.source
            if not new_out.data_source_name and used:
                new_out.data_source_name = random.choice(list(used))
            project.outputs[new_out.file_name] = new_out
            ov.refresh_outputs()
        ui.button("Add", on_click=add_output)