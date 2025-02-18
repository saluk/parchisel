#!/usr/bin/env python3
import asyncio
import os.path
import platform
import shlex
import sys
import re
import os
import random

import numpy as np
from nicegui import ui
from PIL import Image

from nicegui import ui
from multiprocessing import freeze_support
freeze_support()

from lib.datasource import CSVData, PythonData
from lib.project import Project
from lib.outputs import Output

project = Project()
project.data_sources = datas = [
    CSVData("data/cards.csv"),
    CSVData("data/cards2.csv"),
    PythonData("data/cards3.py")
]
project.load_data()
project.load_templates()
project.outputs = {
    project.data_sources[0].source: Output(project.data_sources[0].source, "cards.png", template_name="card1.py"),
    project.data_sources[1].source: Output(project.data_sources[1].source, "cards2.png", template_field="Template"),
    project.data_sources[2].source: Output(project.data_sources[2].source, "cards3.png", template_name="card1.py"),
}

class CodeContext:
    def __init__(self):
        self.template = None
        self.new_filename = ""
        self.ui_editor = None
        self.possible_templates = list(project.templates.keys())
        self.output_images = None
    def set_new_filename(self, fn):
        self.new_filename = fn
    def update_code(self, code):
        self.template.code = code
        # TODO only save if things are rendering OK
        # We could have a button to force save
        self.template.save()
        # TODO only refresh if template is applied to output images
        # TODO only refresh output images that could have changed
        project.dirty_outputs()
        self.output_images.refresh()
cc = CodeContext()
cc.template = project.templates["card1.py"]

def create_template(fn):
    with open("data/templates/"+fn,"w") as f:
        f.write("")
    project.load_templates()
    change_template(fn)

def change_template(fn):
    cc.template = project.templates[fn]
    cc.ui_editor.value = cc.template.reload_code
    cc.ui_template_list.set_options(list(project.templates.keys()), value=fn)

class OutputView:
    def __init__(self):
        self.columns = None
        self.viewed_output = None

        self.project = None
        # TODO: Make a View class. View class stores the project, and modifies 
        #       project data modifications to refresh the correct parts of the view
    def refresh_outputs(self):
        if self.viewed_output:
            self.viewed_output = [key for key in self.viewed_output if key in self.project.outputs]
        self.ui_outputs.refresh()
        self.render_project_outputs.refresh()
ov = OutputView()
ov.project = project


#### UI CODE
@ui.refreshable
def render_selected_project_outputs():
    with ui.dialog() as zoomed, ui.card().classes("w-full h-full") as zoomed_card:
        with ui.scroll_area().style("max-height:initial").classes("w-full h-full"):
            zoomed_image = ui.image()
    for output_key in ov.viewed_output:
        output = project.outputs[output_key]
        with ui.card():
            ui.label(output.data_source_name)
            def zoom_image(out=output):
                zoomed_image.set_source(out.b64encoded(project))
                zoomed_image.props(f"width={out.w*2} height={out.h*2}")
                zoomed_image.update()
                zoomed_card.style(f"max-width:initial; max-height:initial")
                zoomed.open()
            ui.image(output.b64encoded(project)).classes('w-80').on("click", zoom_image).style("cursor: zoom-in;")
@ui.refreshable
def render_project_outputs():
    if not ov.viewed_output and project.outputs:
        ov.viewed_output = [list(project.outputs.keys())[0]]
    with ui.row():
        with ui.column():
            with ui.card():
                def save_output_btn():
                    project.save_outputs()
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
                for output_key in project.outputs.keys():
                    output = project.outputs[output_key]
                    c = ui.checkbox(output.data_source_name, value=output_key in ov.viewed_output)
                    checks.append((output_key,c))
                def set_check():
                    viewed_output = []
                    for output_key, check in checks:
                        if check.value:
                            viewed_output.append(output_key)
                    ov.viewed_output = viewed_output
                    cc.output_images.refresh()
                [c[1].on_value_change(set_check) for c in checks]
        with ui.card():
            render_selected_project_outputs()
ov.render_project_outputs = render_project_outputs

cc.output_images = render_selected_project_outputs

@ui.refreshable
def ui_datasources():
    def add_file():
        file = ov.new_data_path.strip()
        try:
            project.add_data_source(file)
        except Exception as e:
            ui.notify(str(e))
            return
        ov.new_data_path = ""
        ov.ui_datasources.refresh()
        ov.refresh_outputs()
    for ds in project.data_sources:
        def unlink_source(source=ds.source):
            project.remove_data_source(source)
            ov.ui_datasources.refresh()
            ov.refresh_outputs()
        with ui.grid(columns=3):
            imp = ui.input("path", value=ds.source)
            def edit_source(imp=imp, ds=ds):
                try:
                    project.rename_data_source(ds, imp.value)
                except Exception:
                    ui.notify(f"{imp.value} could not be loaded")
                    return
                ui.notify(f"Renamed")
                ov.ui_datasources.refresh()
                ov.refresh_outputs()
            imp.on("keydown.enter", edit_source)
            imp.on("blur", edit_source)
            if isinstance(ds, CSVData):
                ui.label("CSV File")
            elif isinstance(ds, PythonData):
                ui.label("Python File")
            else:
                ui.label("Unknown data type")
            ui.button('Unlink', on_click=unlink_source)
    ui.separator()
    with ui.grid(columns=3):
        from nicegui import app
        async def choose_file():
            files = await app.native.main_window.create_file_dialog(allow_multiple=True)
            cur_path = os.path.abspath('').replace("\\", "/")
            if not files:
                return
            for file in files:
                file = file.replace("\\", "/")
                file = file.replace(cur_path+"/", "")
                ov.new_data_path = file

        ui.button('choose file', on_click=choose_file)
        ui.input("path").bind_value(ov, "new_data_path").on("keydown.enter", add_file)
        ui.button("Add", on_click=add_file)
ov.ui_datasources = ui_datasources
ov.new_data_path = ""

@ui.refreshable
def ui_outputs():
    with ui.grid(columns=5).classes("w-full font-bold"):
        ui.label("Name");ui.label("Data");ui.label("Template");ui.label("Field");ui.label("")
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

            def select_source(evt, out=out, project=project):
                out.data_source_name = evt.value
                out.rendered_string = ""
                ov.refresh_outputs()
            options = [source.source for source in project.data_sources]
            value = ""
            if out.data_source_name in options:
                value = out.data_source_name
            ui.select([""] + [source.source for source in project.data_sources], value=value,
                      on_change=select_source)
            
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
        if not new_out.data_source_name:
            new_out.data_source_name = random.choice(list(used))
        project.outputs[new_out.file_name] = new_out
        ov.refresh_outputs()
    ui.button("Add", on_click=add_output)
ov.ui_outputs = ui_outputs

with ui.dialog() as new_template_dialog, ui.card():
    ui.input(label="New template filename:",
             on_change=lambda e: cc.set_new_filename(e.value))
    with ui.button_group():
        ui.button('Cancel', on_click=new_template_dialog.close)
        def create_cb():
            create_template(cc.new_filename)
            new_template_dialog.close()
        ui.button("Create", on_click=create_cb)


with ui.tabs().classes('w-full') as tabs:
    project_view = ui.tab("Project")
    template_view = ui.tab('Templates')
    sheet_view = ui.tab('Google Sheets')
    tabs.on_value_change(
        lambda: cc.output_images.refresh()
    )
with ui.tab_panels(tabs, value=project_view).classes('w-full'):
    with ui.tab_panel(project_view):
        ui.label("Current Project")
        with ui.card():
            ui.label("Data Sources")
            ui_datasources()
        with ui.card():
            ui.label("Outputs")
            ui_outputs()
    with ui.tab_panel(template_view):
        ui.label('Templates')
        with ui.button_group():
            cc.ui_template_list = ui.select(cc.possible_templates, 
                                        on_change=lambda e: change_template(e.value), 
                                        value="card1.py")
            ui.button('New', on_click=lambda:new_template_dialog.open() )
        cc.ui_editor = ui.codemirror(
            value=cc.template.code, language="Python", theme="abcdef",
            on_change=lambda e: cc.update_code(e.value)
        )
        cc.ui_editor.tailwind.height("52")
        ui.label('Output')
        render_project_outputs()
    with ui.tab_panel(sheet_view):
        ui.label('Google Sheets')
        ui.html('<iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vTlAOJDERD5VIlvgjitaBc1rTfkBy__jH80-FcRQzUblef_3M_S0xJY0SS0Tv5h-EB-VYNjFAFPyI8A/pubhtml?widget=true&amp;headers=false" width=800 height=800></iframe>').classes('w-full')


# NOTE: On Windows reload must be disabled to make asyncio.create_subprocess_exec work (see https://github.com/zauberzeug/nicegui/issues/486)
ui.run(reload=platform.system() != 'Windows', native=True, title="Parchisel Component Creator")
#ui.run(reload=platform.system() != 'Windows', native=False, title="Parchisel Component Creator")