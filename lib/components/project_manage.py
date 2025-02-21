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
        if project:
            with ui.card().classes('w-80'):
                ui.html(f"Name: <b>{project.name}</b><br> Path: {project.root_path}")
                ui.input("output path").bind_value(project, "output_path")
                ui.input("template path").bind_value(project, "template_path")
                ui.input("data path").bind_value(project, "data_path")
                ui.input("image path").bind_value(project, "image_path")
        with ui.card():
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
            with ui.button_group():
                ui.button("Create New Project").on_click(new_project)
                ui.button("Open Project").on_click(open_project)
        # def add_file():
        #     file = ov.new_data_path.strip()
        #     try:
        #         project.add_data_source(file)
        #     except Exception as e:
        #         ui.notify(str(e))
        #         return
        #     ov.new_data_path = ""
        #     ov.ui_datasources.refresh()
        #     ov.refresh_outputs()
        # for ds in project.data_sources:
        #     def unlink_source(source=ds.source):
        #         project.remove_data_source(source)
        #         ov.ui_datasources.refresh()
        #         ov.refresh_outputs()
        #     with ui.grid(columns=3):
        #         imp = ui.input("path", value=ds.source)
        #         def edit_source(imp=imp, ds=ds):
        #             try:
        #                 project.rename_data_source(ds, imp.value)
        #             except Exception:
        #                 ui.notify(f"{imp.value} could not be loaded")
        #                 return
        #             ui.notify(f"Renamed")
        #             ov.ui_datasources.refresh()
        #             ov.refresh_outputs()
        #         imp.on("keydown.enter", edit_source)
        #         imp.on("blur", edit_source)
        #         ui.label(ds.type_label)
        #         ui.button('Unlink', on_click=unlink_source)
        # ui.separator()
        # with ui.grid(columns=3):
        #     from nicegui import app
        #     async def choose_file():
        #         files = await app.native.main_window.create_file_dialog(allow_multiple=True)
        #         cur_path = os.path.abspath('').replace("\\", "/")
        #         if not files:
        #             return
        #         for file in files:
        #             file = file.replace("\\", "/")
        #             file = file.replace(cur_path+"/", "")
        #             ov.new_data_path = file

        #     ui.button('choose file', on_click=choose_file)
        #     ui.input("path").bind_value(ov, "new_data_path").on("keydown.enter", add_file)
        #     ui.button("Add", on_click=add_file)