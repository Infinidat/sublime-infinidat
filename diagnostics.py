import sublime, sublime_plugin
from glob import glob
from os import path
from time import sleep


def get_open_file_prefix(filepath):
    if filepath[-1].isdigit():
        return filepath.rsplit('.', 1)[0]
    return filepath


def get_file_series(prefix):
    return list(glob(prefix + "*"))


def open_file(window, filepath):
    view = window.open_file(filepath)



class OpenNextFile(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        series = get_file_series(get_open_file_prefix(filepath))
        index = (series.index(filepath)+1) % len(series)
        open_file(self.window, series[index])


class OpenPreviousFile(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        series = get_file_series(get_open_file_prefix(filepath))
        index = (series.index(filepath)-1) % len(series)
        open_file(self.window, series[index])
