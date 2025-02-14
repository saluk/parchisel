#!/usr/bin/env python3
import asyncio
import os.path
import platform
import shlex
import sys
import re
import os

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
    project.data_sources[0].source: Output(project.data_sources[0].source, "cards.png", template="card1.py"),
    project.data_sources[1].source: Output(project.data_sources[1].source, "cards2.png", template_field="Template"),
    project.data_sources[2].source: Output(project.data_sources[2].source, "cards3.png", template="card1.py"),
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
ov = OutputView()



#### UI CODE
@ui.refreshable
def render_selected_project_outputs():
    for output_key in ov.viewed_output:
        output = project.outputs[output_key]
        with ui.card():
            ui.label(output.data_source_name)
            ui.image(output.b64encoded(project)).classes('w-80')
@ui.refreshable
def render_project_outputs():
    if not ov.viewed_output:
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
    for ds in project.data_sources:
        def unlink_source(source=ds.source):
            project.remove_data_source(source)
            ov.ui_datasources.refresh()
        with ui.grid(columns=3):
            ui.input(value=ds.source)
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
        ui.input().bind_value(ov, "new_data_path")
        ui.button("Add", on_click=add_file)
ov.ui_datasources = ui_datasources
ov.new_data_path = ""

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
with ui.tab_panels(tabs, value=project_view).classes('w-full'):
    with ui.tab_panel(project_view):
        ui.label("Current Project")
        with ui.card():
            ui.label("Data Sources")
            ui_datasources()
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