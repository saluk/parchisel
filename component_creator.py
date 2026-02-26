#!/usr/bin/env python3

# TODO very bad, let's make cairo the same as cairocffi

# import cairo
# import sys
# sys.modules["cairocffi"] = cairo

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


@ui.page("/")
async def main():

    # Brand palette
    ui.colors(
        primary="#8c3b2a",  # deep rust
        secondary="#5a3e36",  # dark clay brown
        accent="#a3472a",  # brighter rust accent
        positive="#2f6b3f",  # forest green
        negative="#ff6a00",  # bright safety orange
        warning="#ff6a00",
        info="#3e5f4e",  # muted forest-teal
    )

    # Typography + background system
    ui.add_head_html(
        """
    <style>

    /* 🌄 App background */
    body {
    background-color: #f4eee8;  /* warm parchment */
    color: #3b1f18;             /* dark warm brown */
    font-weight: 400;
    }

    /* 🧱 Headings feel branded */
    h1, h2, h3, h4, h5, h6 {
    color: #8c3b2a;
    font-weight: 600;
    }

    /* Subtle text */
    .text-caption,
    .text-subtitle2 {
    color: #6b3a2f;
    }

    /* Links */
    a {
    color: #a3472a;
    text-decoration: none;
    }
    a:hover {
    color: #ff6a00;
    }

    /* 🪵 Cards feel warm instead of stark white */
    .q-card {
    background: #fbf7f3;
    border-radius: 12px;
    }

    /* Buttons slightly softened */
    .q-btn {
    border-radius: 10px;
    font-weight: 500;
    }

    /* Outline buttons use rust */
    .q-btn--outline {
    border-color: var(--q-primary);
    color: var(--q-primary);
    }

    /* Inputs blend with theme */
    .q-field__control {
    background: #ffffff;
    border-radius: 8px;
    }

    </style>
    """
    )

    view_manager = ViewManager()

    async def initial_project_load():
        print(global_profile.profile)
        if global_profile.profile["last_project"]:
            project = LocalProject(
                global_profile.profile["last_project"],
                global_profile.profile["last_project"],
            )
            await project.load()
            # we don't need to refresh when we are building from the initial load
            view_manager.set_project(project, refresh=False)

    with ui.header().classes(replace="row items-center") as header:
        MainMenu(view_manager, view_manager.ui_project_manage).build()
        with ui.tabs() as tab_buttons:
            view_manager.toplevel = list(tab_buttons.ancestors())[1]
            project_view = ui.tab("Project")
            template_view = ui.tab("Templates")
            virtual_table_view = ui.tab("Virtual Tables")
            graph_view = ui.tab("Game State Graph")

    view_manager.header = header
    with ui.tab_panels(tab_buttons, value=project_view).classes("w-full") as tab_views:
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
    view_manager.tabs = tab_views

    # Note, storage.general is only good for the desktop app as we would want each user storage
    # to be independant. This needs a database.
    print("Last Tab=", app.storage.user.get("last_tab", "Project"))
    tab_buttons.set_value(app.storage.user.get("last_tab", "Project"))

    def save_tab(e):
        print(f"saving tab: {e}")
        app.storage.user["last_tab"] = e.value

    tab_buttons.on_value_change(save_tab)

    ui.timer(0.1, initial_project_load, once=True)


app.add_static_files("/images", "lib/images")

# NOTE: On Windows reload must be disabled to make asyncio.create_subprocess_exec work (see https://github.com/zauberzeug/nicegui/issues/486)
# ui.run(reload=platform.system() != 'Windows', native=True, title="Parchisel Component Creator", port=6812)
ui.run(
    reload=True,
    native=False,
    title="Parchisel Component Creator",
    port=6812,
    show=False,
    storage_secret="secretxyz",
)
