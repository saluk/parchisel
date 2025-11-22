from nicegui import ui

from lib.data import global_cache
from lib.outputs import Output
from lib.webelements.project_manage import ProjectManagement
from lib.webelements.project_outputs import ProjectOutputs
from lib.webelements.project_data_sources import ProjectDataSources
from lib.webelements.code_editor import CodeEditor

class OutputView:
    def __init__(self):
        self.columns = None

        self.project = None
        self.progress = None
        # TODO: Make a View class. View class stores the project, and modifies 
        #       project data modifications to refresh the correct parts of the view

        self.ui_datasources = ProjectDataSources(self)
        self.new_data_path = ""

        self.ui_outputs = ProjectOutputs(self)
        self.ui_project_manage = ProjectManagement(self)

        self.ui_template_editor = CodeEditor(self)

    def refresh_outputs(self):
        if not self.project:
            return
        # TODO - we could have several project views configured, say we want a print and play view and a screentop view
        if self.project.viewed_output:
            self.project.viewed_output = [key for key in self.project.viewed_output if key in self.project.outputs]
        self.ui_outputs.refresh()
        self.render_project_outputs.refresh()
    
    def refresh_project(self):
        self.refresh_outputs()
        self.ui_datasources.build.refresh()
        self.ui_template_editor.build.refresh()
        self.ui_project_manage.build.refresh()

    async def render_images(self, image_element_list, output_list):
        for i in range(len(image_element_list)):
            self.progress.message = f"Building image for: {output_list[i].file_name}"
            try:
                print("updating output image", output_list[i].data_source_name)
                image_element_list[i].set_source(await output_list[i].b64encoded(self.project))
            except Exception as e:
                ui.notify(repr(e))
                continue
        self.progress.dismiss()

    @ui.refreshable
    async def render_project_outputs(self,):
        print("render project outputs")
        if not self.project:
            ui.label("No project")
            return
        with ui.row().classes("w-full"):
            with ui.grid(columns="200px auto"):
                with ui.card().classes("w-[500px]").tight() as dragable_card:
                    with ui.expansion("Viewed Outputs").classes("font-size-8 padding-0"):
                        checks = []
                        with ui.button_group():
                            def f_all():
                                for k,c in checks:
                                    c.set_value(True)
                            ui.button("All", on_click=f_all)
                            def f_none():
                                for k,c in checks:
                                    c.set_value(False)
                            ui.button("None", on_click=f_none)
                        for output_key in self.project.outputs.keys():
                            output = self.project.outputs[output_key]
                            c = ui.checkbox(output.file_name, value=output_key in self.project.viewed_output)
                            checks.append((output_key,c))
                        def set_check():
                            viewed_output = []
                            for output_key, check in checks:
                                if check.value:
                                    viewed_output.append(output_key)
                            self.project.viewed_output = viewed_output
                            self.project.save()
                            self.render_selected_project_outputs.refresh()
                        [c[1].on_value_change(set_check) for c in checks]
                    async def refresh_all():
                        global_cache.clear()
                        await self.project.dirty_outputs()
                        await self.project.load_data()
                        self.render_selected_project_outputs.refresh()
                        self.ui_datasources.build.refresh()
                    ui.button("Refresh all").on_click(refresh_all)
                    with ui.scroll_area().classes("w-full") as draggable_scroll:
                        self.dragscroll(dragable_card, draggable_scroll, 3)
                        print("about to render selected project outputs")
                        await self.render_selected_project_outputs()

    @ui.refreshable
    async def render_selected_project_outputs(self):
        zoom_levels = range(200, 1200, 200)
        print("render selected")
        if self.progress:
            try:
                self.progress.dismiss()
            except:
                import traceback
                traceback.print_exc()
        self.progress = ui.notification(f"Building output images", 
            position="top-right", 
            type="ongoing",
            spinner=True
        )
        # TODO mselfe this to the output view class
        self.image_element_list = []
        self.output_list = []
        for output_key in self.project.viewed_output:
            output:Output = self.project.outputs[output_key]
            with ui.card():
                with ui.button_group():
                    zin:ui.button = ui.button("+")
                    zin.tailwind.font_size('xs')
                    zout:ui.button = ui.button("-")
                    zout.tailwind.font_size('xs')
                    ui.label(output.file_name).classes("m-3 font-bold")
                    ui.label(output.data_source_name).classes("m-3 font-italic")
                    for t in await output.templates_used(self.project):
                        if not t:
                            ui.notification(f'Error: output file {output.file_name} is missing template')
                        ui.label("["+t+"]").classes("m-3")
                zoom = zoom_levels[len(zoom_levels)//2]
                im_el = ui.image("").classes(f'w-[{zoom}px]').style("cursor: zoom-in;")
                im_el.zoom = zoom
                def set_zoom(adj, im_el=im_el):
                    i = zoom_levels.index(im_el.zoom)
                    i += adj
                    if i<0 or i>=len(zoom_levels):
                        return
                    im_el.zoom = zoom_levels[i]
                    im_el.classes(replace=f"w-[{int(im_el.zoom)}px]")
                    im_el.update()
                zin.on_click(lambda im_el=im_el:set_zoom(1, im_el))
                zout.on_click(lambda im_el=im_el:set_zoom(-1, im_el))
                self.image_element_list.append(im_el)
                self.output_list.append(output)
        ui.timer(0.1, lambda:self.render_images(self.image_element_list, self.output_list), once=True)

    def dragscroll(self, el, scroll_area:ui.scroll_area, speed=1):
        if not hasattr(el, "is_scrolling"):
            el.is_scrolling = False
        def toggle_scroll(on):
            el.is_scrolling = on
        def doscroll(evt):
            if not el.is_scrolling:
                return
            if not hasattr(scroll_area, "position"):
                scroll_area.position = [0,0]
            scroll_area.position[0] -= evt.args['movementX']*speed
            scroll_area.position[1] -= evt.args['movementY']*speed
            scroll_area.scroll_to(pixels=scroll_area.position[0], axis='horizontal')
            scroll_area.scroll_to(pixels=scroll_area.position[1], axis='vertical')
            return False
        el.on('mousedown', lambda: toggle_scroll(True))
        self.toplevel.on('mouseup', lambda: toggle_scroll(False))
        self.toplevel.on('mousemove', doscroll)