import sublime, sublime_plugin
from contextlib import contextmanager


def key_func(item):
    return min(item.a, item.b), max(item.a, item.b)


def grep_selection(view, edit, invert_selection=True):
    view.window().run_command("find_all_under")
    view.run_command("expand_selection", dict(to="line"))
    if invert_selection:
        view.run_command("invert_selection")
    [view.erase(edit, region) for region in sorted(view.sel(), key=key_func, reverse=True)]


@contextmanager
def stay_in_place(view):
    first_selection = view.sel()[0]
    current_position = min(first_selection.a, first_selection.b), max(first_selection.a, first_selection.b)
    word = view.substr(first_selection)
    all_positions = sorted([(region.a, region.b) for region in view.find_all(word, sublime.LITERAL)])
    index = all_positions.index(current_position)
    yield
    view.sel().clear()
    view.sel().add(view.find_all(word, sublime.LITERAL)[index])
    view.run_command("find_under")


class GrepCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        with stay_in_place(self.view):
            grep_selection(self.view, edit)


class GrepExcludeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        grep_selection(self.view, edit, invert_selection=False)
        self.view.sel().clear()
