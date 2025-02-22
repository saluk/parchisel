import os

from nicegui import ui
from nicegui import app
import webview

from lib.exceptions import NotifyException
from lib.project import LocalProject

# Show current project information if there is one
# ProjectName, ProjectPath
# Project path data
# NewProjectButton
#   File widget

class ProjectManagement:
    def __init__(self, view):
        self.view = view
    def refresh(self):
        self.build.refresh()
    @ui.refreshable
    def build(self):
        ov = self.view
        project = getattr(ov, "project", None)

        async def new_project():
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
        async def open_project():
            file = (await app.native.main_window.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=os.path.abspath("projects/")
            ))[0].replace("\\", "/")
            if not file:
                return
            if not os.path.exists(f"{file}/prchsl_cc_proj.json"):
                raise NotifyException(f"No parchisel component creator project exists at {file}")
            new_project = LocalProject(file.rsplit("/", 1)[-1], file)
            new_project.load()
            self.view.project = new_project
            self.view.refresh_project()
            self.build.refresh()

        with ui.grid(columns='120px auto').classes('w-full'):
            with ui.column():
                ui.button("Create New Project").on_click(new_project)
                ui.button("Open Project").on_click(open_project)
            if project:
                with ui.card():
                    ui.html(f"Current Project: <b>{project.name}</b><br> Path: {project.root_path}")
                    with ui.expansion("Paths"):
                        with ui.grid(columns=2):
                            ui.input("output path").bind_value(project, "output_path")
                            ui.input("template path").bind_value(project, "template_path")
                            ui.input("data path").bind_value(project, "data_path")
                            ui.input("image path").bind_value(project, "image_path")
