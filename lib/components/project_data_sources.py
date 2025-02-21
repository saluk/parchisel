import os
from nicegui import ui

class ProjectDataSources:
    def __init__(self, ov):
        self.view = ov
    def refresh(self):
        self.build.refresh()
    @ui.refreshable
    def build(self):
        ov = self.view
        project = ov.project
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
                ui.label(ds.type_label)
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