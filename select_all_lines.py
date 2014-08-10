import sublime, sublime_plugin

class SelectAllLinesCommand(sublime_plugin.TextCommand):
    def select_lines(self, start_row, direction):
        row = start_row
        last_row = self.view.rowcol(self.view.size())[0]
        while True:
            text_point = self.view.text_point(row, 0)
            if row > last_row or row < 0:
                break
            self.view.sel().add(sublime.Region(text_point))
            row += direction

    def clear_no_line_beginnings(self):
        for region in reversed(self.view.sel()):
            if self.view.rowcol(region.begin())[1] != 0:
                self.view.sel().subtract(region)

    def run(self, edit, direction):
        if direction == "forward":
            direction = 1
            start_selection = self.view.sel()[-1]
        elif direction == "backward":
            direction = -1
            start_selection = self.view.sel()[0]
        else:
            direction = 1
            start_selection = self.view.line(0)
        start_row = self.view.rowcol(start_selection.begin())[0]
        self.clear_no_line_beginnings()
        self.select_lines(start_row, direction)
