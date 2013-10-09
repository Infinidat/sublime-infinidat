
import sublime, sublime_plugin
from glob import glob
from os import path, pardir
from time import sleep
from datetime import datetime, timedelta
from re import search, finditer, escape
from itertools import product
from datetime import datetime
from functools import wraps

STRPTIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DATE_FORMATS = [
                "%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y",
                "%m/%d/%y", "%m/%d/%Y", "%m-%d-%y", "%m-%d-%Y",
                "%d/%m/%y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d-%m-%y %H:%M:%S", "%d-%m-%Y %H:%M:%S",
                "%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%m-%d-%y %H:%M:%S", "%m-%d-%Y %H:%M:%S",
                "%d/%m/%y-%H-%M-%S", "%m/%d/%y-%H-%M-%S",
                "%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%y %H:%M", "%d-%m-%Y %H:%M",
                "%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m-%d-%y %H:%M", "%m-%d-%Y %H:%M",
                "%H:%M:%S", "%H:%M",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M"]


def parse_datestring(datestring):
    from argparse import ArgumentTypeError
    from datetime import datetime
    if datestring == "now":
        datestring = get_default_timestamp()
    for format in DATE_FORMATS:
        try:
            return datetime.strptime(datestring, format)
        except:
            pass
    raise ArgumentTypeError("Invalid datetime string: {!r}".format(datestring))


def get_file_prefix(filepath):
    if filepath[-1].isdigit():
        return filepath.rsplit('.', 1)[0]
    return filepath


def get_file_series(prefix):
    return sorted(glob(prefix + "*"))


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


def get_files_of_other_node(window):
    filepath = window.active_view().file_name()
    prefix = get_file_prefix(filepath)
    diagnostics_dir, hostname, timestamp, files, var, log, dirname, basename = prefix.rsplit(path.sep, 7)
    other_hostname = hostname[:-1] + ("1" if hostname[-1] == "2" else "2")
    return get_file_series(path.join(diagnostics_dir, other_hostname, "*", files, var, log, "*", basename))


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


def get_files_timeframes(files):
    """:returns: from oldest to newest"""
    def generator():
        for filepath in files:
            start, finish = get_timeframe_in_file(filepath)
            yield dict(start=start, finish=finish, filepath=filepath)
    def key(item):
        return item['start']
    return sorted(generator(), key=key)


def show_timestamp_as_close_as_possible(view, t0):
    datestring = strftime(t0)
    for substring in [datestring[:count] for count in range(0, -len(datestring), -1)]:
        location = view.find(substring, 0, sublime.LITERAL)
        if location.a == -1:  # found nothing
            continue
        view.show_at_center(location)
        view.sel().clear()
        view.sel().add(location)
        return


def goto_timestamp_in_files(window, files, t0, ident):
    try:
        [filepath] = [item['filepath'] for item in files if item['start'] <= t0 and t0 <= item['finish']]
    except ValueError:  # there is no file containing t0
        sublime.error_message("{} not found in {}".format(t0, ident))
        return
    view = window.open_file(filepath)
    view.settings().set("word_wrap", False)
    show_timestamp_as_close_as_possible(view, t0)


class OpenNextFile(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        series = get_file_series(get_file_prefix(filepath))
        index = (series.index(filepath)+1) % len(series)
        self.window.open_file(series[index]).settings().set("word_wrap", False)


class OpenPreviousFile(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        series = get_file_series(get_file_prefix(filepath))
        index = (series.index(filepath)-1) % len(series)
        self.window.open_file(series[index]).settings().set("word_wrap", False)


class GotoTrace(sublime_plugin.WindowCommand):
    def run(self):
        t0 = get_datetime_from_current_line(self.window)
        files = get_files_timeframes(get_traces(self.window))
        goto_timestamp_in_files(self.window, files, t0, "traces")


class GotoLog(sublime_plugin.WindowCommand):
    def run(self):
        t0 = get_datetime_from_current_line(self.window)
        files = get_files_timeframes(get_logs(self.window))
        goto_timestamp_in_files(self.window, files, t0, "logs")


class GotoOtherNode(sublime_plugin.WindowCommand):
    def run(self):
        t0 = get_datetime_from_current_line(self.window)
        files = get_files_timeframes(get_files_of_other_node(self.window))
        goto_timestamp_in_files(self.window, files, t0, "other node")


class GotoDate(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        files = get_files_timeframes(get_file_series(get_file_prefix(filepath)))

        def innerfunc(datestring):
            t0 = parse_datestring(datestring)
            goto_timestamp_in_files(self.window, files, t0, "this type of files")

        self.window.show_input_panel("Enter timestamp", "", innerfunc, None, None)


class GotoTimestamp(sublime_plugin.WindowCommand):
    def run(self):
        filepath = self.window.active_view().file_name()
        files = get_files_timeframes(get_file_series(get_file_prefix(filepath)))

        def innerfunc(timestamp_string):
            timestamp = int(timestamp_string)
            try:
                t0 = datetime.utcfromtimestamp(timestamp_string)
            except ValueError:
                t0 = datetime.utcfromtimestamp(timestamp_string/1000)
            goto_timestamp_in_files(self.window, files, t0, "this type of files")

        self.window.show_input_panel("Enter timestamp", "", innerfunc, None, None)

