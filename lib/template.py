class Template:
    def __init__(self, filename):
        self.name = filename.rsplit("/")[-1] if "/" in filename else filename
        self.filename = filename
        self._code = None
    @property
    def code(self):
        if not self._code:
            self.load()
        return self._code
    @code.setter
    def code(self, code):
        self._code = code
    @property
    def reload_code(self):
        self.load()
        return self._code
    def get_line(self, line_num):
        return self.code.split("\n")[line_num]
    def load(self):
        with open(self.filename,"r") as f:
            self._code = f.read()
    def save(self):
        if self._code is None:
            self._code = ""
        with open(self.filename,"w") as f:
            f.write(self._code)