from nicegui import ui, app

from lib.base_components.small_button import SmallButton
from .model import saveload
import json


class FileList:
    def __init__(self, save_load_view):
        self.save_load_view = save_load_view

    @ui.refreshable
    async def build(self):
        ui.label("Load a tree:")
        with ui.list().props("bordered separator"):
            for key in self.save_load_view.files.keys():
                item = ui.item(key).props('active-class="bg-[#ccfbf3]"')

                def click_item(e, value=key):
                    self.save_load_view.filename = value
                    self.build.refresh()

                item.on_click(click_item)
                if self.save_load_view.filename == key:
                    item.props("active")


class SaveLoadView:
    files_key = "GameStateGraph.files"
    lastfile_key = "GameStateGraph.last_filename"

    def __init__(self, parent):
        self.parent = parent
        self.filename = ""
        if self.lastfile_key in app.storage.user:
            self.filename = app.storage.user[self.lastfile_key]

    @property
    def files(self):
        if not app.storage.user.get(self.files_key, None):
            app.storage.user[self.files_key] = {}
        return app.storage.user[self.files_key]

    def save(self):
        saved = saveload.Saver().to_dict(self.parent.game_states)
        self.files[self.filename] = saved
        app.storage.user[self.lastfile_key] = self.filename
        self.build.refresh()
        ui.notify(f"Saved {self.filename}!")

    async def show_load_dialog(self):
        self.original_filename = self.filename

        def confirm():
            self.load_dialog.close()
            self.reload()
            app.storage.user[self.lastfile_key] = self.filename

        def close():
            self.load_dialog.close()
            self.filename = self.original_filename

        with ui.dialog(value=True) as self.load_dialog, ui.card():
            self.file_list = FileList(self)
            await self.file_list.build()
            SmallButton("Load", on_click=confirm)
            SmallButton("Close", on_click=close)

    def show_save_as_dialog(self):
        def confirm():
            self.save_as_dialog.close()
            self.save()

        with ui.dialog(value=True) as self.save_as_dialog, ui.card():
            ui.input("Filename").bind_value(self, "filename")
            SmallButton("Save", on_click=confirm)
            SmallButton("Close", on_click=self.save_as_dialog.close)

    def reload(self):
        saved = self.files[self.filename]
        tree = saveload.Saver().from_dict(saved)
        self.parent.replace_graph(tree)
        app.storage.user[self.lastfile_key] = self.filename

    @ui.refreshable
    async def build(self):
        # menu button
        # save, save as, load
        with ui.element("div"):
            with SmallButton("Menu"):
                with ui.menu().props("auto-close"):
                    ui.menu_item("New Graph", on_click=self.parent.new_graph)
                    self.save_menu_item = ui.menu_item(
                        "Save", on_click=self.save
                    ).bind_enabled_from(self, "filename")
                    ui.menu_item("Save As", on_click=self.show_save_as_dialog)

                    self.reload_menu_item = ui.menu_item(
                        "Reload", on_click=self.reload
                    ).bind_enabled_from(self, "filename")

                    self.load_menu_item = ui.menu_item(
                        "Load", on_click=self.show_load_dialog
                    )
        print(self.files)
        if not self.files:
            self.load_menu_item.disable()
