import time

from lib.context import Context
from lib.context import SkiaContext as Context

class Output:
    def __init__(self, data_source_name, file_name, rows=None, cols=None, width=None, height=None, 
                offset_x = 10, offset_y = 10, spacing_x = 10, spacing_y = 10, 
                template: str = None, template_field: str = None):
        assert(template or template_field)
        self.data_source_name = data_source_name
        self.file_name = file_name

        # TODO use all of these fields
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y

        self.template = template
        self.template_field = template_field

        self.rendered_string = ""   # Clear to rerender
        self.w = 1800
        self.h = 1800
    def render(self, project):
        self.context = Context(self.w, self.h, "RGB")
        start_time = time.time()
        self.context.clear((0,0,0,0))

        # Checkerboard pattern
        check_size = 25
        colors = [(200, 200, 200, 255), (150, 150, 150, 255)]
        #for x in range(0, self.w, check_size):
        #    for y in range(0, self.h, check_size):
        #        self.context.draw_box(x, y, check_size, check_size, colors[0])
        #        colors.reverse()
        #    colors.reverse()

        # Start drawing
        x=self.offset_x
        y=self.offset_y

        #draw cards
        data_source = project.get_data_source(self.data_source_name)
        if not data_source:
            self.context.draw_text(0, 0, f"No data source found: {self.data_source_name}")
            return
        template = None
        if self.template:
            template = project.templates[self.template]
        template_cache = []  #These templates have been reloaded already
        for card in data_source.cards:
            card_context = Context(640, 480, "RGB")
            card_context.clear((0, 0, 0, 0))

            # Get template from row
            if self.template_field:
                template = project.templates[card[self.template_field]]
            
            if template not in template_cache:
                template.load()
                template_cache.append(template)

            # TODO do the exec in the template
            exec(template.code, {"card":card_context, "row":card})

            self.context.draw_context(x, y, card_context)
            x += card_context.width+10
            if x+card_context.width > 1800:
                x = 10
                y += card_context.height+10
            #return
        end_time = time.time()
        render_time = end_time-start_time
        print("Render time:", self.file_name, render_time)

    def save(self):
        self.context.save("outputs/"+self.file_name)

    def b64encoded(self, project):
        if self.rendered_string:
            return self.rendered_string
        self.render(project)
        self.rendered_string = self.context.b64encoded()
        return self.rendered_string