import os

from nicegui import ui
from nicegui import app
try:
    import webview
except:
    webview = None

from lib.exceptions import NotifyException
from lib.project import LocalProject
from lib.file.profile import global_profile

# Show current project information if there is one
# ProjectName, ProjectPath
# Project path data
# NewProjectButton
#   File widget

class ProjectManagement:
    def __init__(self, view):
        self.view = view
    async def new_project(self):
        file = (await app.native.main_window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=os.path.abspath("projects/"),
            save_filename="project_name"
        ))
        if not file: # Cancel chosen
            return
        new_project = LocalProject(file.replace("\\", "/").rsplit("/", 1)[-1], file)
        new_project.create()
        self.view.project = new_project
        self.view.refresh_project()
        self.build.refresh()
    async def open_project(self):
        file = (await app.native.main_window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=os.path.abspath("projects/")
        ))[0].replace("\\", "/")
        if not file:
            return
        if not os.path.exists(f"{file}/prchsl_cc_proj.json"):
            raise NotifyException(f"No parchisel component creator project exists at {file}")
        new_project = LocalProject(file.rsplit("/", 1)[-1], file)
        await new_project.load()
        self.view.project = new_project
        self.view.ui_template_editor.template = None
        self.view.refresh_project()
        self.build.refresh()
        global_profile.profile['last_project'] = file
        global_profile.write()
    async def save_project(self):
        if not self.view.project:
            return ui.notify("No project loaded")
        self.view.project.save()
        ui.notify("Saved!", type="positive")
    def refresh(self):
        self.build.refresh()
    @ui.refreshable
    def build(self):
        ov = self.view
        project = getattr(ov, "project", None)
        if project:
            with ui.card():
                ui.html(f"Current Project: <b>{project.name}</b><br> Path: {project.root_path}")
                with ui.expansion("Paths"):
                    with ui.grid(columns=2):
                        ui.input("output path").bind_value(project, "output_path")
                        ui.input("template path").bind_value(project, "template_path")
                        ui.input("data path").bind_value(project, "data_path")
                        ui.input("image path").bind_value(project, "image_path")
        else:
            ui.label("No project loaded")
