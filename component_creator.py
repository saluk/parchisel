#!/usr/bin/env python3

# TODO very bad, let's make cairo the same as cairocffi

#import cairo
#import sys
#sys.modules["cairocffi"] = cairo

import platform
import os

from nicegui import ui, app
from nicegui.events import KeyEventArguments

from multiprocessing import freeze_support
freeze_support()

from lib.project import LocalProject

from lib.view_manager import ViewManager

from lib.webelements.mainmenu import MainMenu

from lib.data.profile import global_profile

# TODO make a parchisel app that has component creator and virtual table as modes to select between
from lib.virtualtable import virtual_table

@ui.page('/')
async def main():

    view_manager = ViewManager()

    async def initial_project_load():
        print(global_profile.profile)
        if global_profile.profile['last_project']:
            project = LocalProject(global_profile.profile['last_project'], global_profile.profile['last_project'])
            await project.load()
            # we don't need to refresh when we are building from the initial load
            view_manager.set_project(project, refresh=False)

    def handle_keys(e:KeyEventArguments):
        if e.key not in view_manager.key_state:
            view_manager.key_state[e.key] = {'keydown':e.action.keydown, 'keyup':e.action.keyup}
        else:
            if view_manager.key_state[e.key]['keydown'] != e.action.keydown:
                view_manager.key_state[e.key] = {'keydown':e.action.keydown, 'keyup':e.action.keyup}
                #ui.notify(repr(e.key)+":"+repr(view_manager.key_state[e.key]))
    view_manager.keyboard = ui.keyboard().on_key(handle_keys)
    with ui.header().classes(replace='row items-center') as header:
        MainMenu(view_manager, view_manager.ui_project_manage).build()
        with ui.tabs() as tabs:
            view_manager.toplevel = list(tabs.ancestors())[1]
            project_view = ui.tab("Project")
            template_view = ui.tab('Templates')
            virtual_table_view = ui.tab('Virtual Tables')
            graph_view = ui.tab('Game State Graph')
            tabs.on_value_change(view_manager.refresh_outputs)

    tabs.on("click", lambda tab: print(tab))

    view_manager.header = header
    with ui.tab_panels(tabs, value=project_view).classes('w-full') as tabs:
        # with ui.tab_panel(virtual_table_view):
        #     view = virtual_table.TableView()
        #     with ui.card():
        #         await view.build()
        # with ui.tab_panel(project_view):
        #     with ui.card():
        #         view_manager.ui_project_manage.build()
        #     with ui.card():
        #         ui.label("Data Sources")
        #         await view_manager.ui_datasources.build()
        #     with ui.card():
        #         ui.label("Outputs")
        #         await view_manager.ui_outputs.build()
        # with ui.tab_panel(template_view):
        #     async def save_output_btn():
        #         await view_manager.project.save_outputs()
        #         ui.notify("Saved!")
        #     ui.button("Save All Project Images", on_click=save_output_btn)
        #     def save_screentop():
        #         from lib.exports import ExportComponents
        #         ExportComponents(view_manager.project)
        #     ui.button("Export Screentop", on_click=save_screentop)
        #     ui.label('Templates')
        #     with ui.card().tight():
        #         view_manager.ui_template_editor.build()
        #     await view_manager.ui_rendered_card_preview.build()
        with ui.tab_panel(graph_view):
            await view_manager.ui_game_state_graph.build()
    view_manager.tabs = tabs
    ui.timer(0.1, initial_project_load, once=True)

app.add_static_files('/images', 'lib/images')
app.on_startup(main)

# NOTE: On Windows reload must be disabled to make asyncio.create_subprocess_exec work (see https://github.com/zauberzeug/nicegui/issues/486)
#ui.run(reload=platform.system() != 'Windows', native=True, title="Parchisel Component Creator", port=6812)
ui.run(reload=True, native=False, title="Parchisel Component Creator", port=6812, show=False)
