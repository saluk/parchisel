from nicegui import ui

from lib.data import global_cache
from lib.outputs import Output
from lib.webelements.project_manage import ProjectManagement
from lib.webelements.project_outputs import ProjectOutputs

from lib.webelements.code_editor import CodeEditor

class RenderedCardPreview:
    def __init__(self, view):
        self.view = view
        self.zoom_levels = range(200, 1200, 200)
        self.zoom = self.zoom_levels[0]

    @property
    def project(self):
        return self.view.project

    async def render_images(self, image_element_list=None, output_list=None):
        if not image_element_list:
            image_element_list = self.image_element_list
        if not output_list:
            output_list = self.output_list
        for i in range(len(image_element_list)):
            print("enable view progress")
            self.view.progress.message = f"Building image for: {output_list[i].file_name}"
            try:
                print("updating output image", output_list[i].data_source_name)
                image_element_list[i].set_source(await output_list[i].b64encoded(self.project))
            except Exception as e:
                ui.notify(repr(e))
                continue
        print("dismiss view progress")
        self.view.progress.dismiss()

    @ui.refreshable
    async def build(self,):
        print("render project outputs")
        if not self.project:
            ui.label("No project")
            return
        with ui.grid().classes("w-full") as dragable_card:
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
                self.view.refresh_project()
            with ui.row():
                ui.button("Refresh all").on_click(refresh_all)
                await self.zoom_buttons()
            await self.render_selected_project_outputs()

    async def zoom_buttons(self):
        def set_zoom(adj):
            i = self.zoom_levels.index(self.zoom)
            i += adj
            if i<0 or i>=len(self.zoom_levels):
                return
            self.zoom = self.zoom_levels[i]
            for im_el in self.image_element_list:
                im_el.classes(replace=f"w-[{int(self.zoom)}px]")
                im_el.update()
        with ui.button_group():
            zin:ui.button = ui.button("+")
            zin.tailwind.font_size('xs')
            zout:ui.button = ui.button("-")
            zout.tailwind.font_size('xs')
        zin.on_click(lambda:set_zoom(1))
        zout.on_click(lambda:set_zoom(-1))

    @ui.refreshable
    async def render_selected_project_outputs(self):
        print("render selected")
        if self.view.progress:
            try:
                self.view.progress.dismiss()
            except:
                import traceback
                traceback.print_exc()
        self.view.progress = ui.notification(f"Building output images", 
            position="top-right", 
            type="ongoing",
            spinner=True
        )
        self.image_element_list = []
        self.output_list = []
        with ui.element("div").classes("fit row wrap justify-start items-start content-start"):
            for output_key in self.project.viewed_output:
                output:Output = self.project.outputs[output_key]
                with ui.card().tight().classes("w-fit"):
                    with ui.row():
                        ui.label(output.file_name).classes("m-3 font-bold")
                        ui.label(output.data_source_name).classes("m-3 font-italic")
                        for t in await output.templates_used(self.project):
                            if not t:
                                ui.notification(f'Error: output file {output.file_name} is missing template')
                            ui.label("["+t+"]").classes("m-3")
                    im_el = ui.image("").classes(f'w-[{self.zoom}px]')
                    self.image_element_list.append(im_el)
                    self.output_list.append(output)
        ui.timer(0, lambda:self.render_images(self.image_element_list, self.output_list), once=True)

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
        self.view.toplevel.on('mouseup', lambda: toggle_scroll(False))
        self.view.toplevel.on('mousemove', doscroll)