import random
from nicegui import ui

from lib.outputs import Output

async def edit_component(project, out, output_list):
    with ui.dialog() as dialog, ui.card():
        component = out.component
        if component:
            ui.button("Set No Component").on_click(lambda: dialog.submit("clear"))
        else:
            component = {"component_name": "", "asset_side": ""}
        def change(k, v):
            component[k] = v
        ui.input("Component name", value=component["component_name"]).on_value_change(
            lambda e: change("component_name", e.value)
        )
        ui.input("Asset side", value=component["asset_side"]).on_value_change(
            lambda e: change("asset_side", e.value)
        )
        ui.button("OK").on_click(lambda: dialog.submit("ok"))
    val = await dialog
    if val == "clear":
        out.component = None
    else:
        out.component = component
    project.save()
    output_list.build.refresh()

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
    async def build(self):
        ov = self.view
        project = ov.project
        grid = "20% 30% auto 15% 5%"
        if not project:
            ui.label("No project")
            return
        with ui.grid(columns=grid).classes("w-full font-bold text-center"):
            ui.label("Name");ui.label("Data Source");ui.label("Template");ui.label("Component");ui.label("")
        bgcol = ["bg-lime-50", "bg-lime-100"]
        for out_key in project.outputs:
            out = project.outputs[out_key]
            def unlink_output(out=out):
                out.rendered_string = ""
                project.remove_output(out)
                ov.refresh_outputs()
            
            with ui.grid(columns=grid).classes(f"w-full {bgcol[0]}"):
                bgcol.reverse()
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
                    project.save()
                options = [source.source for source in project.data_sources]
                value = out.data_source_name
                # Data source selector AND data range selector
                with ui.column():
                    options = {source.source:source.short_name() for source in project.data_sources}
                    if not value in options.keys():
                        options[value] = "BROKEN - "+value
                    ui.select(options, value=value,
                        on_change=select_source)
                    total_range = out.get_card_range(project, True)
                    card_range = out.get_card_range(project)
                    def set_range(e, out=out):
                        out.set_card_range(project, (e.value["min"],e.value["max"]))
                        project.save()
                        out.rendered_string = ""
                        self.queue_update(ov.refresh_outputs)
                    if total_range:
                        ui.range(
                            min=total_range[0], 
                            max=total_range[1], 
                            value={'min': card_range[0], 'max': card_range[1]}
                        ).props('label-always snap').on_value_change(lambda e, out=out: set_range(e, out))

                # Template name
                with ui.column():
                    def select_template(evt, out=out, project=project):
                        out.template_name = evt.value
                        project.save()
                        out.rendered_string = ""
                        ov.refresh_outputs()
                    ui.select([""] + [name for name in project.templates], value=out.template_name,
                            on_change=select_template).props("dense clearable")
                    
                    def select_template_field(evt, out=out, project=project):
                        out.template_field = evt.value
                        project.save()
                        out.rendered_string = ""
                        ov.refresh_outputs()
                    ds = project.get_data_source(out.data_source_name)
                    if ds:
                        values = [key for key in ds.fieldnames]
                        value = out.template_field
                        if value not in values:
                            value = ""
                        ui.select([""] + values, value=value,
                                on_change=select_template_field).props(f"dense {'clearable' if value else ''}")
                comp = "none" if not out.component else f"{out.component['component_name']} - {out.component['asset_side']}"
                async def show_edit_component(out=out, outs=self):
                    await edit_component(project, out, outs)
                with ui.button(comp).props("no-caps size=sm").classes("h-[40px]").on_click(show_edit_component):
                    ui.tooltip('Edit Component info')
                ui.button('X', on_click=unlink_output).classes("h-[25px]")
        ui.separator()
        def add_output():
            project.add_output("new_output.png")
            ov.refresh_outputs()
        ui.button("Add", on_click=add_output)