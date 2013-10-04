import sublime, sublime_plugin
from contextlib import contextmanager
from itertools import count
from re import escape


def key_func(item):
    return item.begin(), item.end()


def select_all_lines_containing_current_selection(view):
    view.window().run_command("find_all_under")
    view.run_command("expand_selection", dict(to="line"))


def grep_selection(view, edit, invert_selection=True):
    select_all_lines_containing_current_selection(view)
    if invert_selection:
        view.run_command("invert_selection")
    [view.erase(edit, region) for region in sorted(view.sel(), key=key_func, reverse=True)]


def exapnd_tracebacks(view):
    selection = view.sel()
    regions = list(selection)
    for region in regions:
        next_traceback_line_region = view.find(r"(?:\n[^\d].*)+", region.b+1)
        if next_traceback_line_region.a == next_traceback_line_region.b:
            break
        if (next_traceback_line_region.a, next_traceback_line_region.b) == (-1, -1):
            break
        selection.add(next_traceback_line_region)
    view.run_command("expand_selection", dict(to="line"))


def log_grep_selection(view, edit, invert_selection=True):
    select_all_lines_containing_current_selection(view)
    exapnd_tracebacks(view)
    if invert_selection:
        view.run_command("invert_selection")
    [view.erase(edit, region) for region in sorted(view.sel(), key=key_func, reverse=True)]


def get_selected_region(view):
    first_selection = view.sel()[0]
    current_position = first_selection.begin(), first_selection.end()
    word = view.substr(first_selection)
    return current_position, word


@contextmanager
def stay_in_place(view):
    current_position, word = get_selected_region(view)
    all_positions = sorted([(region.a, region.b) for region in view.find_all(word, sublime.LITERAL)])
    index = all_positions.index(current_position)
    yield
    view.sel().clear()
    view.sel().add(view.find_all(word, sublime.LITERAL)[index])


class GrepCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        with stay_in_place(self.view):
            grep_selection(self.view, edit)


class GrepExcludeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        grep_selection(self.view, edit, invert_selection=False)
        self.view.sel().clear()


class LogGrepCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        _, word = get_selected_region(self.view)
        if len(word) < 4:
            sublime.error_message("selection is too short, it will take too long to grep this")
            return
        with stay_in_place(self.view):
            log_grep_selection(self.view, edit)


class LogGrepExcludeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        _, word = get_selected_region(self.view)
        if len(word) < 4:
            sublime.error_message("selection is too short, it will take too long to grep this")
            return
        log_grep_selection(self.view, edit, invert_selection=False)
        self.view.sel().clear()

