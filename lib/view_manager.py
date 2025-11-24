from lib.webelements.project_data_sources import ProjectDataSources
from lib.webelements.project_outputs import ProjectOutputs
from lib.webelements.code_editor import CodeEditor
from lib.webelements.render_cards.rendered_card_preview import RenderedCardPreview
from lib.webelements.project_manage import ProjectManagement

class ViewManager:
    def __init__(self):
        self.columns = None

        self.project = None
        self.progress = None

        self.ui_datasources = ProjectDataSources(self)
        self.new_data_path = ""

        self.ui_outputs = ProjectOutputs(self)
        self.ui_project_manage = ProjectManagement(self)

        self.ui_template_editor = CodeEditor(self)

        self.ui_rendered_card_preview = RenderedCardPreview(self)
    
    def set_project(self, project):
        self.project = project
        self.refresh_project()

    def refresh_project(self):
        self.ui_rendered_card_preview.build.refresh()
        self.ui_datasources.build.refresh()
        self.ui_template_editor.build.refresh()
        self.ui_project_manage.build.refresh()

    def refresh_outputs(self):
        if not self.project:
            return
        # TODO - we could have several project views configured, say we want a print and play view and a screentop view
        if self.project.viewed_output:
            self.project.viewed_output = [key for key in self.project.viewed_output if key in self.project.outputs]
        self.ui_outputs.refresh()
        self.ui_rendered_card_preview.build.refresh()