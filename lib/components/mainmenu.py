from nicegui import ui

from lib.components.project_manage import ProjectManagement

class MainMenu:
    def __init__(self, view, project_manager:ProjectManagement):
        self.view = view
        self.project_manager = project_manager
    def build(self):
        project = self.view.project
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item("Create New Project").on_click(lambda: self.project_manager.new_project())
                ui.menu_item("Open Project").on_click(lambda: self.project_manager.open_project())
                ui.separator()
                ui.menu_item('Quit')