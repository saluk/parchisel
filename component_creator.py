#!/usr/bin/env python3
import os.path
import platform
import os
import random

from nicegui import ui, app

from multiprocessing import freeze_support
freeze_support()

from lib.datasource import CSVData, PythonData
from lib.project import LocalProject
from lib.outputs import Output

from lib.components.mainmenu import MainMenu
from lib.components.project_manage import ProjectManagement
from lib.components.project_outputs import ProjectOutputs
from lib.components.project_data_sources import ProjectDataSources
from lib.components.code_editor import CodeEditor
from lib.template import Template
from lib.file import global_cache

# TODO make a parchisel app that has component creator and virtual table as modes to select between
from lib.virtualtable import virtual_table

class OutputView:
    def __init__(self):
        self.columns = None
        self.viewed_output = []

        self.project = None
        self.progress = None
        # TODO: Make a View class. View class stores the project, and modifies 
        #       project data modifications to refresh the correct parts of the view

    def refresh_outputs(self):
        if self.viewed_output:
            self.viewed_output = [key for key in self.viewed_output if key in self.project.outputs]
        self.ui_outputs.refresh()
        self.render_project_outputs.refresh()
    
    def refresh_project(self):
        self.refresh_outputs()
        self.ui_datasources.build.refresh()
        self.ui_template_editor.build.refresh()
        self.ui_project_manage.build.refresh()
ov = OutputView()

#### UI CODE
async def render_images(image_element_list, output_list):
    for i in range(len(image_element_list)):
        ov.progress.message = f"Building image for: {output_list[i].file_name}"
        try:
            print("updating output image")
            image_element_list[i].set_source(await output_list[i].b64encoded(ov.project))
        except Exception as e:
            ui.notify(repr(e))
            continue
    ov.progress.dismiss()
zoom_levels = range(200, 1200, 200)
@ui.refreshable
async def render_selected_project_outputs():
    print("render selected")
    if ov.progress:
        ov.progress.dismiss()
    ov.progress = ui.notification(f"Building output images", 
        position="top-right", 
        type="ongoing",
        spinner=True
    )
    # TODO move this to the output view class
    ov.image_element_list = []
    ov.output_list = []
    for output_key in ov.viewed_output:
        output = ov.project.outputs[output_key]
        with ui.card():
            with ui.button_group():
                zin:ui.button = ui.button("+")
                zin.tailwind.font_size('xs')
                zout:ui.button = ui.button("-")
                zout.tailwind.font_size('xs')
                ui.label(output.file_name).classes("m-3 font-bold")
                ui.label(output.data_source_name).classes("m-3 font-italic")
                for t in await output.templates_used(ov.project):
                    ui.label("["+t+"]").classes("m-3")
            zoom = zoom_levels[len(zoom_levels)//2]
            im_el = ui.image("").classes(f'w-[{zoom}px]').style("cursor: zoom-in;")
            im_el.zoom = zoom
            def set_zoom(adj, im_el=im_el):
                i = zoom_levels.index(im_el.zoom)
                i += adj
                if i<0 or i>=len(zoom_levels):
                    return
                im_el.zoom = zoom_levels[i]
                im_el.classes(replace=f"w-[{int(im_el.zoom)}px]")
                im_el.update()
            zin.on_click(lambda im_el=im_el:set_zoom(1, im_el))
            zout.on_click(lambda im_el=im_el:set_zoom(-1, im_el))
            ov.image_element_list.append(im_el)
            ov.output_list.append(output)
    ui.timer(0.1, lambda:render_images(ov.image_element_list, ov.output_list), once=True)

def dragscroll(el, scroll_area:ui.scroll_area, speed=1):
    if not hasattr(el, "is_scrolling"):
        el.is_scrolling = False
    def toggle_scroll(on):
        el.is_scrolling = on
    def doscroll(evt):
        if not el.is_scrolling:
            return
        if not hasattr(scroll_area, "position"):
            scroll_area.position = [0,0]
        scroll_area.position[0] -= evt.args['movementX']*speed
        scroll_area.position[1] -= evt.args['movementY']*speed
        scroll_area.scroll_to(pixels=scroll_area.position[0], axis='horizontal')
        scroll_area.scroll_to(pixels=scroll_area.position[1], axis='vertical')
        return False
    el.on('mousedown', lambda: toggle_scroll(True))
    ov.toplevel.on('mouseup', lambda: toggle_scroll(False))
    ov.toplevel.on('mousemove', doscroll)

@ui.refreshable
async def render_project_outputs():
    print("render project outputs")
    if not ov.project:
        ui.label("No project")
        return
    if not ov.viewed_output and ov.project.outputs:
        ov.viewed_output = [list(ov.project.outputs.keys())[0]]
    with ui.row().classes("w-full"):
        with ui.grid(columns="200px auto"):
            with ui.card().classes("w-[500px]").tight() as dragable_card:
                with ui.expansion("Viewed Outputs").classes("font-size-8 padding-0"):
                    checks = []
                    with ui.button_group():
                        def f_all():
                            for k,c in checks:
                                c.set_value(True)
                        ui.button("All", on_click=f_all)
                        def f_none():
                            for k,c in checks:
                                c.set_value(False)
                        ui.button("None", on_click=f_none)
                    for output_key in ov.project.outputs.keys():
                        output = ov.project.outputs[output_key]
                        c = ui.checkbox(output.file_name, value=output_key in ov.viewed_output)
                        checks.append((output_key,c))
                    def set_check():
                        viewed_output = []
                        for output_key, check in checks:
                            if check.value:
                                viewed_output.append(output_key)
                        ov.viewed_output = viewed_output
                        ov.render_selected_project_outputs.refresh()
                    [c[1].on_value_change(set_check) for c in checks]
                async def refresh_all():
                    global_cache.clear()
                    await ov.project.dirty_outputs()
                    await ov.project.load_data()
                    render_selected_project_outputs.refresh()
                    ov.ui_datasources.build.refresh()
                ui.button("Refresh all").on_click(refresh_all)
                with ui.scroll_area().classes("w-full") as draggable_scroll:
                    dragscroll(dragable_card, draggable_scroll, 3)
                    print("about to render selected project outputs")
                    await render_selected_project_outputs()

ov.render_images = render_images
ov.render_project_outputs = render_project_outputs
ov.render_selected_project_outputs = render_selected_project_outputs

ov.ui_datasources = ProjectDataSources(ov)
ov.new_data_path = ""

ov.ui_outputs = ProjectOutputs(ov)
ov.ui_project_manage = ProjectManagement(ov)

ov.ui_template_editor = CodeEditor(ov)

async def initial_project_load():
    project = LocalProject("test", "projects/dog_and_pony")
    await project.load()
    ov.project = project
    ov.refresh_project()

@ui.page('/')
async def main():
    with ui.header().classes(replace='row items-center'):
        MainMenu(ov, ov.ui_project_manage).build()
        with ui.tabs() as tabs:
            ov.toplevel = list(tabs.ancestors())[1]
            project_view = ui.tab("Project")
            template_view = ui.tab('Templates')
            sheet_view = ui.tab('Google Sheets')
            virtual_table_view = ui.tab('Virtual Tables')
            tabs.on_value_change(ov.refresh_outputs)

    with ui.tab_panels(tabs, value=project_view).classes('w-full'):
        with ui.tab_panel(virtual_table_view):
            view = virtual_table.TableView()
            with ui.card():
                await view.build()
        with ui.tab_panel(project_view):
            with ui.card():
                ov.ui_project_manage.build()
            with ui.card():
                ui.label("Data Sources")
                await ov.ui_datasources.build()
            with ui.card():
                ui.label("Outputs")
                await ov.ui_outputs.build()
        with ui.tab_panel(template_view):
            async def save_output_btn():
                await ov.project.save_outputs()
                ui.notify("Saved!")
            ui.button("Save All Project Images", on_click=save_output_btn)
            def save_screentop():
                from lib.exports import ExportComponents
                ExportComponents(ov.project)
            ui.button("Export Screentop", on_click=save_screentop)
            ui.label('Templates')
            with ui.card().tight():
                ov.ui_template_editor.build()
            await render_project_outputs()
    ui.timer(0.1, initial_project_load, once=True)

app.on_startup(main)

# NOTE: On Windows reload must be disabled to make asyncio.create_subprocess_exec work (see https://github.com/zauberzeug/nicegui/issues/486)
ui.run(reload=platform.system() != 'Windows', native=True, title="Parchisel Component Creator", port=6812)
#ui.run(reload=platform.system() != 'Windows', native=False, title="Parchisel Component Creator")