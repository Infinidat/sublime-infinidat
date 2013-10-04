
import sublime, sublime_plugin
from glob import glob
from os import path
from time import sleep
from datetime import datetime
from re import search, finditer

STRPTIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
STRFTIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def strptime(datestring):
    return datetime.strptime(datestring, STRPTIME_FORMAT)


def strftime(datetime_object):
    return datetime_object.strftime(STRFTIME_FORMAT)


def get_open_file_prefix(filepath):
    if filepath[-1].isdigit():
        return filepath.rsplit('.', 1)[0]
    return filepath


def get_file_series(prefix):
    return list(glob(prefix + "*"))


def get_datetime_from_current_line(window):
    view = window.active_view()
    line = view.substr(view.line(view.sel()[0]))
    datestring = search("[\d-]+ [\d.:]+", line).group()
    return strptime(datestring)


def get_traces(window):
    filepath = window.active_view().file_name()
    dirname = path.dirname(filepath)
    return get_file_series(path.join(dirname, "izbox-traces.log"))


def get_logs(window):
    filepath = window.active_view().file_name()
    dirname = path.dirname(filepath)
    return get_file_series(path.join(dirname, "izbox.log"))


def pairwise(iterable):
    from itertools import tee, izip
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def get_timeframe_in_file(filepath):
    with open(filepath, 'rb+') as fd:
        start = fd.read(32768).decode("ascii")
        fd.seek(-32769, 2)
        finish = fd.read().decode("ascii")
    first, last = search("[\d-]+ [\d.:]+", start).group(), list(finditer("[\d-]+ [\d.:]+", finish))[-1].group()
    return strptime(first), strptime(last)


def files_by_timestamp(files):
    """:returns: from oldest to newest"""
    def generator():
        for filepath in files:
            start, finish = get_timeframe_in_file(filepath)
            yield dict(start=start, finish=finish, filepath=filepath)
    def key(item):
        return item['start']
    return sorted(generator(), key=key)


class OpenNextFile(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        series = get_file_series(get_open_file_prefix(filepath))
        index = (series.index(filepath)+1) % len(series)
        self.window.open_file(series[index])


class OpenPreviousFile(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        series = get_file_series(get_open_file_prefix(filepath))
        index = (series.index(filepath)-1) % len(series)
        self.window.open_file(series[index])


class GotoTrace(sublime_plugin.WindowCommand):
    def run(self):
        t0 = get_datetime_from_current_line(self.window)
        traces = files_by_timestamp(get_traces(self.window))
        for trace_dict in traces:
            if trace_dict['start'] <= t0 and t0 <= trace_dict['finish']:
                view = self.window.open_file(trace_dict['filepath'])
                view.show_at_center(view.find(strftime(t0), 0))
                return
        sublime.error_message("{} not found in traces".format(t0))


class GotoLog(sublime_plugin.WindowCommand):
    def run(self):
        t0 = get_datetime_from_current_line(self.window)
        logs = files_by_timestamp(get_logs(self.window))
        for trace_dict in logs:
            if trace_dict['start'] <= t0 and t0 <= trace_dict['finish']:
                view = self.window.open_file(trace_dict['filepath'])
                view.show_at_center(view.find(strftime(t0), 0))
                return
        sublime.error_message("{} not found in logs".format(t0))
