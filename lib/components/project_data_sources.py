import os
from nicegui import ui

from lib import exceptions
from lib.files import File

class ProjectDataSources:
    def __init__(self, ov):
        self.view = ov
    def refresh(self):
        self.build.refresh()
    @ui.refreshable
    def build(self):
        ov = self.view
        project = ov.project
        if not project:
            ui.label("No Project")
            return
        async def add_file():
            file = ov.new_data_path.strip()
            try:
                await project.add_data_source(file)
            except Exception as e:
                raise exceptions.NotifyException(f"Couldn't load file/url {file}")
            ov.new_data_path = ""
            ov.ui_datasources.refresh()
            ov.refresh_outputs()
        async def add_file2():
            file = ov.new_data_path.strip()
            try:
                await project.create_data_source(file)
            except Exception as e:
                raise exceptions.NotifyException(f"Couldn't create file/url {file}")
            ov.new_data_path = ""
            ov.ui_datasources.refresh()
            ov.refresh_outputs()
        for ds in project.data_sources:
            async def unlink_source(source=ds.source):
                await project.remove_data_source(source)
                ov.ui_datasources.refresh()
                ov.refresh_outputs()
            with ui.grid(columns=3):
                imp = ui.input("path", value=ds.source)
                async def edit_source(imp=imp, ds=ds):
                    try:
                        await project.rename_data_source(ds, imp.value)
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
                with ui.expansion("view data").classes('col-span-3'):
                    file = File(ds.source)
                    if file.google_sheet_edit:
                        ui.html(f'<iframe src="{file.google_sheet_edit}" width=800 height=800></iframe>').classes('w-full')
                    else:
                        def gen_cols(ds):
                            return [
                                {"name": n, "label": n, "field": n, 
                                "headerClasses":'hidden' if n.startswith("__") else '',
                                'classes':'hidden' if n.startswith("__") else ''} for n in ds.fieldnames
                            ]
                        # Show input to edit headers
                        if ds.is_editable():
                            header_edit = ui.input("headers", value=", ".join(ds.fieldnames))
                        with ui.grid(columns=2):
                            table = ui.table(columns=gen_cols(ds),
                                rows=ds.cards
                            )
                            if ds.is_editable():
                                def change_headers(v, table, ds=ds):
                                    ds.change_headers(v)
                                    table.columns = gen_cols(ds)
                                    table.update()
                                header_edit.on_value_change(
                                    lambda e, table=table: change_headers(e.value, table)
                                )
                                async def add_field(ds=ds):
                                    ds.create_blank_field()
                                    await project.dirty_outputs()
                                    ov.refresh_outputs()
                                    self.build.refresh()
                                async def add_card(ds=ds):
                                    ds.create_blank_card()
                                    await project.dirty_outputs()
                                    ov.refresh_outputs()
                                    self.build.refresh()
                                ui.button("+").on_click(add_field)
                                ui.button("+").on_click(add_card)
                                async def alter_cell(e, ds=ds):
                                    for card in ds.cards:
                                        if e.args['__id'] == card['__id']:
                                            card.update(e.args)
                                            ds.save_data()
                                            await project.dirty_outputs()
                                            ov.refresh_outputs()
                                            ui.notify("updated")
                                            return
                                for col in gen_cols(ds):
                                    table.add_slot(f'body-cell-{col['field']}', f'''
                                        <q-td key="{col['field']}" :props="props">
                                            <q-input
                                                v-model="props.row.{col['field']}"
                                                @blur="() => $parent.$emit('alter_cell', props.row)"
                                                @validate:model-value="() => $parent.$emit('alter_cell', props.row)"
                                            />
                                        </q-td>
                                    ''')
                                table.on('alter_cell', alter_cell)
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

            ui.button('open file', on_click=choose_file)
            ui.input("path").bind_value(ov, "new_data_path").on("keydown.enter", add_file)
            ui.button("Add existing source", on_click=add_file)
            ui.button("Create new source", on_click=add_file2)