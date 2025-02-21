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

from lib.components.project_manage import ProjectManagement
from lib.components.project_outputs import ProjectOutputs
from lib.components.project_data_sources import ProjectDataSources
from lib.template import Template

project = LocalProject("test", "projects/test")
# project.data_sources = datas = [
#     CSVData("projects/test/data/cards.csv"),
#     CSVData("projects/test/data/cards2.csv"),
#     PythonData("projects/test/data/cards3.py")
# ]
# project.load_data()
# project.load_templates()
# project.outputs = {
#     project.data_sources[0].source: Output(project.data_sources[0].source, "cards.png", template_name="card1.py"),
#     project.data_sources[1].source: Output(project.data_sources[1].source, "cards2.png", template_field="Template"),
#     project.data_sources[2].source: Output(project.data_sources[2].source, "cards3.png", template_name="card1.py", height=4000),
# }
# project.save()
project.load()

class CodeContext:
    def __init__(self):
        self.template = None
        self.new_filename = ""
        self.ui_editor = None
        self.possible_templates = list(project.templates.keys())
    def set_new_filename(self, fn):
        self.new_filename = fn
    async def update_code(self, code):
        self.template.code = code
        # TODO only save if things are rendering OK
        # We could have a button to force save
        self.template.save()
        if project.dirty_outputs(for_templates=[self.template.name], for_outputs=ov.viewed_output):   # only redraw outputs that use this template
            print("rerender images")
            print(ov.image_element_list, ov.output_list)
            await render_images(ov.image_element_list, ov.output_list)

def create_template(template_name):
    t = project.add_template(template_name)
    change_template(t.name)

def change_template(template_name):
    ov.cc.template = ov.project.templates[template_name]
    ov.ui_template_editor.refresh(ov.cc.template)


class OutputView:
    def __init__(self):
        self.columns = None
        self.viewed_output = None

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
        self.ui_template_editor.refresh()
ov = OutputView()
ov.project = project


#### UI CODE
async def render_images(image_element_list, output_list):
    for i in range(len(image_element_list)):
        ov.progress.message = f"Building image for: {output_list[i].file_name}"
        try:
            print("updating output image")
            image_element_list[i].set_source(await output_list[i].b64encoded(ov.project))
        except Exception as e:
            ui.notify(str(e))
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
                zin:ui.button = ui.button("zoomin")
                zin.tailwind.font_size('xs')
                zout:ui.button = ui.button("zoomout")
                zout.tailwind.font_size('xs')
                ui.label(output.data_source_name)
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
    if not ov.viewed_output and ov.project.outputs:
        ov.viewed_output = [list(ov.project.outputs.keys())[0]]
    with ui.row().classes("w-full"):
        with ui.column().classes("w-[20%]"):
            with ui.card():
                async def save_output_btn():
                    await ov.project.save_outputs()
                    ui.notify("Saved!")
                ui.button("Save Output", on_click=save_output_btn)
            with ui.card():
                ui.label("View outputs:")
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
        with ui.column().classes("w-[70%]"):
            with ui.card().classes("w-full") as dragable_card:
                with ui.scroll_area().classes("w-full") as draggable_scroll:
                    dragscroll(dragable_card, draggable_scroll, 3)
                    print("about to render selected project outputs")
                    await render_selected_project_outputs()
ov.render_project_outputs = render_project_outputs
ov.render_selected_project_outputs = render_selected_project_outputs

ov.ui_datasources = ProjectDataSources(ov)
ov.new_data_path = ""

ov.ui_outputs = ProjectOutputs(ov)
ov.ui_project_manage = ProjectManagement(ov)

@ui.refreshable
def render_code_editor(template=None):
    cc = CodeContext()
    if ov.project.templates and not template:
        template = list(ov.project.templates.values())[0]
    cc.template = template
    ov.cc = cc
    with ui.button_group():
        ui.button('New', on_click=lambda:new_template_dialog.open() )
        if not ov.project.templates:
            return
        cc.ui_template_list = ui.select(list(ov.project.templates.keys()), 
            on_change=lambda e: change_template(e.value), 
            value=template.name)
        def queue_update(value):
            if getattr(ov, "code_update_timer", None):
                ov.code_update_timer.deactivate()
            ov.code_update_timer = ui.timer(0.5, lambda: cc.update_code(value), once=True)

        cc.ui_editor = ui.codemirror(
            value=cc.template.code, language="Python", theme="abcdef",
            on_change=lambda e: queue_update(e.value)
        )
        cc.ui_editor.tailwind.height("52")
ov.ui_template_editor = render_code_editor

with ui.dialog() as new_template_dialog, ui.card():
    ui.input(label="New template filename:",
             on_change=lambda e: ov.cc.set_new_filename(e.value))
    with ui.button_group():
        ui.button('Cancel', on_click=new_template_dialog.close)
        def create_cb():
            create_template(ov.cc.new_filename)
            new_template_dialog.close()
        ui.button("Create", on_click=create_cb)


with ui.tabs().classes('w-full') as tabs:
    ov.toplevel = list(tabs.ancestors())[0]
    project_view = ui.tab("Project")
    template_view = ui.tab('Templates')
    sheet_view = ui.tab('Google Sheets')
    tabs.on_value_change(ov.refresh_outputs)
async def ui_panels():
    with ui.tab_panels(tabs, value=project_view).classes('w-full'):
        with ui.tab_panel(project_view):
            with ui.card():
                ov.ui_project_manage.build()
            with ui.card():
                ui.label("Data Sources")
                ov.ui_datasources.build()
            with ui.card():
                ui.label("Outputs")
                ov.ui_outputs.build()
        with ui.tab_panel(template_view):
            ui.label('Templates')
            ov.ui_template_editor()
            ui.label('Output')
            await render_project_outputs()
        with ui.tab_panel(sheet_view):
            ui.label('Google Sheets')
            ui.html('<iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vTlAOJDERD5VIlvgjitaBc1rTfkBy__jH80-FcRQzUblef_3M_S0xJY0SS0Tv5h-EB-VYNjFAFPyI8A/pubhtml?widget=true&amp;headers=false" width=800 height=800></iframe>').classes('w-full')

app.on_startup(ui_panels)

# NOTE: On Windows reload must be disabled to make asyncio.create_subprocess_exec work (see https://github.com/zauberzeug/nicegui/issues/486)
ui.run(reload=platform.system() != 'Windows', native=True, title="Parchisel Component Creator")
#ui.run(reload=platform.system() != 'Windows', native=False, title="Parchisel Component Creator")