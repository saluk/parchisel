import os
from nicegui import ui

from lib import exceptions
from lib.file import File

class EditableTable:
    def __init__(self, ds, project, ov):
        self.ds = ds
        self.project = project
        self.ov = ov
    @ui.refreshable_method
    def build(self):
        ds = self.ds
        project = self.project
        ov = self.ov
        import random
        v = random.randint(0,100000)
        ui.label(v)
        def gen_cols(ds):
            return [
                {"name": n, "label": n, "field": n, 
                "headerClasses":'hidden' if n.startswith("__") else '',
                'classes':'hidden' if n.startswith("__") else ''} for n in ds.fieldnames
            ]
        with ui.row():
            table = ui.table(columns=gen_cols(ds),
                rows=ds.cards
            ).classes("w-3/4")
            if ds.is_editable():
                async def add_field(ds=ds):
                    ds.create_blank_field()
                    ds.save_data()
                    await project.dirty_outputs()
                    ov.refresh_outputs()
                    self.build.refresh()
                async def add_card(ds=ds):
                    ds.create_blank_card()
                    ds.save_data()
                    await project.dirty_outputs()
                    ov.refresh_outputs()
                    self.build.refresh()
                ui.button("add field").classes("w-45").on_click(add_field)
                async def alter_cell(e, ds=ds):
                    for card in ds.cards:
                        if e.args['__id'] == card['__id']:
                            old = {k:card[k] for k in card}
                            card.update(e.args)
                            if old == card:
                                return
                            ds.save_data()
                            await project.dirty_outputs()
                            #ov.refresh_outputs()
                            #ui.notify("updated")
                            return
                async def alter_header(e, ds=ds):
                    original = e.args['field']
                    new = e.args['name']
                    if original.strip() == new.strip():
                        return
                    ds.rename_column(original, new)
                    ds.save_data()
                    await project.dirty_outputs()
                    #ov.refresh_outputs()
                    self.build.refresh()
                async def delete_column(e, ds=ds):
                    original = e.args['field']
                    ds.delete_column(original)
                    ds.save_data()
                    await project.dirty_outputs()
                    #ov.refresh_outputs()
                    self.build.refresh()
                async def delete_row(e, ds=ds):
                    ds.delete_card_matching(e.args)
                    ds.save_data()
                    await project.dirty_outputs()
                    #ov.refresh_outputs()
                    self.build.refresh()
                table.add_slot(f'header', '''
                    <q-tr :props="props">
                    <q-th
                        v-for="col in props.cols"
                        :key="col.name"
                        :props="props"
                    >
                    <q-td style="width:100px">
                        <q-btn class="q-pa-xs q-ma-full" 
                            style="height:15px"
                            size="xs" padding="xs xs" 
                            color="white" dense 
                            text-color="black" label="x" 
                            @click="() => $parent.$emit('delete_column', col)"
                        />
                        <q-input standout dense
                            style="width:100px"
                            v-model="col.name"
                            @blur="() => $parent.$emit('alter_header', col)"
                            @validate:model-value="() => $parent.$emit('alter_header', col)"
                            @keyup.enter="() => $parent.$emit('alter_header', col)"
                        />
                    </q-td>
                    </q-th>
                    </q-tr>
                ''')
                cols = gen_cols(ds)
                for col in cols:
                    avail_fields = [col['field'] for col in cols if not 'hidden' in col['classes']]
                    table.add_slot(f'body-cell-{col['field']}', f'''
                        <q-td key="{col['field']}" :props="props">
                            <div class="row">
                                <q-btn class="col-1 q-pa-xs q-ma-full" 
                                    style="height:15px"
                                    size="xs" padding="xs xs" 
                                    color="white" dense 
                                    text-color="black" label="x"
                                    @click="() => $parent.$emit('delete_row', props.row)"
                                    v-if="props.col.field=='{avail_fields[0] if avail_fields else ''}'"
                                />
                                <q-input class="col"
                                    v-model="props.row.{col['field']}"
                                    @blur="() => $parent.$emit('alter_cell', props.row)"
                                    @validate:model-value="() => $parent.$emit('alter_cell', props.row)"
                                    @keyup.enter="() => $parent.$emit('alter_cell', props.row)"
                                />
                            </div>
                        </q-td>
                    ''')
                table.on('alter_cell', alter_cell)
                table.on('alter_header', alter_header)
                table.on('delete_column', delete_column)
                table.on('delete_row', delete_row)
                # ui.aggrid({
                #     'defaultColDef': {'flex': 1},
                #     'columnDefs': [{'headerName':'ID', 'field':'__id'}] + [
                #         {'headerName': field, 'field': field, 'hide': field.startswith('__'), 'editable': True} for field in ds.fieldnames
                #     ],
                #     'rowData': [
                #         c for c in ds.cards
                #     ],
                #     'rowSelection': 'multiple',
                # })
        if ds.is_editable():
            ui.button("add row").on_click(add_card)

class ProjectDataSources:
    def __init__(self, ov):
        self.view = ov
        self.tables = []
    def refresh(self):
        self.build.refresh()
    @ui.refreshable
    async def build(self):
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
        self.tables = []
        for ds in project.data_sources:
            async def unlink_source(source=ds.source):
                await project.remove_data_source(source)
                ov.ui_datasources.refresh()
                ov.refresh_outputs()
            with ui.grid(columns=3):
                imp = ui.input("path", value=ds.source)
                async def edit_source(imp=imp, ds=ds):
                    try:
                        changed = await project.rename_data_source(ds, imp.value)
                    except Exception:
                        ui.notify(f"{imp.value} could not be loaded")
                        return
                    if changed:
                        ui.notify(f"Renamed")
                        ov.ui_datasources.refresh()
                        ov.refresh_outputs()
                imp.on("keydown.enter", edit_source)
                imp.on("blur", edit_source)
                ui.label(ds.type_label)
                ui.button('Unlink', on_click=unlink_source)
                with ui.expansion("view data").classes('col-span-3'):
                    file = File(ds.source)
                    if file.edit_url:
                        ui.html(f'<iframe src="{file.edit_url}" width=800 height=800></iframe>').classes('w-full')
                    else:
                        editable_table = EditableTable(ds, project, ov)
                        self.tables.append(editable_table)
                        editable_table.build()
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