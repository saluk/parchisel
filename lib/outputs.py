import time

from nicegui import ui, run

from lib.draw_context import DrawContextSkia as DrawContext

class Output:
    def __init__(self, data_source_name, file_name, rows=None, cols=None, width=int(150*2.5*3), height=int(150*3.5*3), 
                offset_x = 0, offset_y = 0, spacing_x = 0, spacing_y = 0, 
                template_name: str = None, template_field: str = None, card_range:tuple = None,
                data_source=None,
                template=None,
                component=None):
        self.data_source_name = data_source_name
        self.file_name = file_name
        self.template_name = template_name
        self.template_field = template_field

        # If we want to skip the lookup on the project
        self._data_source = data_source
        self._template = template

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

    def resize(self, width=None, height=None, cols=None):
        width = int(width) if width else 1
        height = int(height) if height else 1
        cols = int(cols) if cols else None
        if self.width == width and self.height == height and cols == self.cols:
            return None
        self.width = width
        self.height = height
        self.cols = cols
        return True

    def get_data_source(self, project):
        if self._data_source:
            return self._data_source
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
        if self._template:
            return [self._template.name]
        data_source = self.get_data_source(project)
        if not data_source:
            return [self.template_name] if self.template_name else []
        try:
            await data_source.load_data()
        except Exception:
            return []
        rows = []
        for card in data_source.cards:
            template = self.template_name
            if self.template_field:
                template = card.get(self.template_field, template)
            if template not in rows:
                rows.append(template)
        return rows

    async def render(self, project):
        print(f"RENDERING: {self.data_source_name} as {self.file_name}")
        # Pass parameters so function can be run in separate process
        error = None
        try:
            data_source = self.get_data_source(project)
            assert(data_source)
            await data_source.load_data()
            card_data = data_source.cards
        except Exception:
            card_data = None
            error = f"No data source found: {self.data_source_name}"
        main_template = None
        if self.template_name:
            main_template = project.templates[self.template_name]
        if self._template:
            main_template = self._template
        card_range = self.get_card_range(project)
        if not card_range:
            error = "Card range error: {self.data_source_name}, {card_range}"
            card_range = []
        self.context = self.render_io(self.width, self.height, self.offset_x, self.offset_y, self.cols, self.spacing_x, self.spacing_y, project, card_data, card_range, main_template, self.template_field, error)
        #self.context = await run.io_bound(self.render_io,self.width, self.height, self.offset_x, self.offset_y, self.cols, self.spacing_x, self.spacing_y, project, card_data, card_range, main_template, self.template_field, error)

    def render_io(self, width, height, offset_x, offset_y, cols, spacing_x, spacing_y, project, card_data, card_range, main_template, template_field, error):
        context = DrawContext(width, height, project, "RGB")
        start_time = time.time()
        context.clear((0,0,0,0))

        # Checkerboard pattern
        #check_size = 25
        #colors = [(200, 200, 200, 255), (150, 150, 150, 255)]
        #for x in range(0, self.w, check_size):
        #    for y in range(0, self.h, check_size):
        #        self.context.draw_box(x, y, check_size, check_size, colors[0])
        #        colors.reverse()
        #    colors.reverse()

        # Start drawing
        col = 0
        x=offset_x
        y=offset_y

        #draw cards
        if error:
            context.draw_text(0, 0, error)
            return context
        template_cache = []  #These templates have been reloaded already
        maxh = 0
        for card_index in range(*card_range):
            card = card_data[card_index]
            card_context = DrawContext(640, 480, project, "RGB")
            card_context.clear((0, 0, 0, 0))

            template = main_template
            # Get template from row
            if template_field:
                try:
                    template = project.templates[card[template_field]]
                except Exception:
                    card_context.draw_text(0, 0, f"No data source found:")
                    card_context.draw_text(0, 45, f"{card[template_field]}")
                    card_context.draw_text(0, 90, f"from")
                    card_context.draw_text(0, 125, f"{template_field}")

            if template:
                if template not in template_cache:
                    template.load()
                    template_cache.append(template)

                try:
                    # TODO do the exec in the template
                    exec(template.code, {"card":card_context, "row":card})
                except Exception as exc:
                    print("Exception in executing template:")
                    import traceback
                    traceback.print_exc()
                    #ui.notify(str(traceback.format_exc()))
                    card_context.draw_text(0, 0, f"Template")
                    card_context.draw_text(0, 45, f"Error")

            # Resize output if we are using cols to determine how many cards to place in a row
            if cols:

                change = False
                if card_context.width + x > width:
                    width = x+card_context.width
                    change = True
                if card_context.height + y > height:
                    height = y+card_context.height
                    change = True
                if change:
                    print("RESIZE OUTPUT TO", width, height)
                    context.resize(width, height, "RGB")

            try:
                context.draw_context(x, y, card_context)
            except Exception as exc:
                print("Exception drawing card context to image:")
                import traceback
                traceback.print_exc()
                #ui.notify(str(traceback.format_exc()))
            if card_context.height > maxh:
                maxh = card_context.height
            x += card_context.width+spacing_x
            if x+card_context.width > width or (cols and col>=cols):
                x = offset_x
                y += maxh+spacing_y
                maxh = 0
                col = 0
            #return
        end_time = time.time()
        render_time = end_time-start_time
        #print("Render time:", self.file_name, render_time)
        return context

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
    