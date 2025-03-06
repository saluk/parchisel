import time

from nicegui import ui

from lib.context import Context
from lib.context import SkiaContext as Context

class Output:
    def __init__(self, data_source_name, file_name, rows=None, cols=None, width=1800, height=1800, 
                offset_x = 0, offset_y = 0, spacing_x = 0, spacing_y = 0, 
                template_name: str = None, template_field: str = None, card_range:tuple = None,
                component=None):
        self.data_source_name = data_source_name
        self.file_name = file_name
        self.template_name = template_name
        self.template_field = template_field

        self.component = component   # This should be a dict of {component_name, asset_side}

        self.card_range = tuple(card_range) if card_range else None  # Set to a (start, end) tuple to only render those cards

        # TODO use all of these fields
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y

        self.rendered_string = ""   # Clear to rerender

    def get_data_source(self, project):
        return project.get_data_source(self.data_source_name)

    def get_card_range(self, project, total=False):
        if self.card_range and not total:
            return self.card_range
        source = self.get_data_source(project)
        if not source:
            return None
        return (0, len(source.cards))
    
    def set_card_range(self, project, range_or_None):
        total = self.get_card_range(project, True)
        if not range_or_None:
            range_or_none = total
        min, max = range_or_None
        if min == total[0] and max == total[1]:
            self.card_range = None
            return
        self.card_range = [min, max]

    async def templates_used(self, project):
        rows = []
        data_source = project.get_data_source(self.data_source_name)
        if not data_source:
            return [self.template_name]
        try:
            await data_source.load_data()
        except Exception:
            return rows
        for card in data_source.cards:
            template = self.template_name
            if self.template_field:
                template = card.get(self.template_field, template)
            if template not in rows:
                rows.append(template)
        return rows

    async def render(self, project):
        print(f"RENDERING: {self.data_source_name} as {self.file_name}")
        self.context = Context(self.width, self.height, project, "RGB")
        start_time = time.time()
        self.context.clear((0,0,0,0))

        # Checkerboard pattern
        #check_size = 25
        #colors = [(200, 200, 200, 255), (150, 150, 150, 255)]
        #for x in range(0, self.w, check_size):
        #    for y in range(0, self.h, check_size):
        #        self.context.draw_box(x, y, check_size, check_size, colors[0])
        #        colors.reverse()
        #    colors.reverse()

        # Start drawing
        x=self.offset_x
        y=self.offset_y

        #draw cards
        try:
            data_source = project.get_data_source(self.data_source_name)
            assert(data_source)
            await data_source.load_data()
        except Exception:
            self.context.draw_text(0, 0, f"No data source found: {self.data_source_name}")
            return
        main_template = None
        if self.template_name:
            main_template = project.templates[self.template_name]
        template_cache = []  #These templates have been reloaded already
        maxh = 0
        card_range = self.get_card_range(project)
        if not card_range:
            return
        for card_index in range(*card_range):
            card = data_source.cards[card_index]
            card_context = Context(640, 480, project, "RGB")
            card_context.clear((0, 0, 0, 0))

            template = main_template
            # Get template from row
            if self.template_field:
                try:
                    template = project.templates[card[self.template_field]]
                except Exception:
                    card_context.draw_text(0, 0, f"No data source found:")
                    card_context.draw_text(0, 45, f"{card[self.template_field]}")
                    card_context.draw_text(0, 90, f"from")
                    card_context.draw_text(0, 125, f"{self.template_field}")

            if template:
                if template not in template_cache:
                    template.load()
                    template_cache.append(template)

                try:
                    # TODO do the exec in the template
                    exec(template.code, {"card":card_context, "row":card})
                except Exception as exc:
                    import traceback
                    traceback.print_exc()
                    ui.notify(str(exc))
                    card_context.draw_text(0, 0, f"Template")
                    card_context.draw_text(0, 45, f"Error")

            self.context.draw_context(x, y, card_context)
            if card_context.height > maxh:
                maxh = card_context.height
            x += card_context.width+self.spacing_x
            if x+card_context.width > self.width:
                x = self.offset_x
                y += maxh+self.spacing_y
                maxh = 0
            #return
        end_time = time.time()
        render_time = end_time-start_time
        print("Render time:", self.file_name, render_time)

    def save(self, folder):
        fn = self.file_name
        if folder:
            if not folder.endswith("/"):
                folder += "/"
            fn = folder + self.file_name
        self.context.save(fn)

    async def b64encoded(self, project):
        if self.rendered_string:
            return self.rendered_string
        await self.render(project)
        self.rendered_string = self.context.b64encoded()
        return self.rendered_string
    