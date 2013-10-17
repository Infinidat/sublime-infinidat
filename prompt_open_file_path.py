import sublime
import sublime_plugin
from os import listdir, sep, getenv
from os.path import commonprefix, isdir, exists, split, dirname, basename, commonprefix, join
from math import ceil, floor


class PromptOpenFilePath(sublime_plugin.WindowCommand):
    def run(self):
        self.scratch_file_list_buffer = None
        self.last_text = None

        current_dir = getenv('HOME') + sep
        active_view = self.window.active_view()
        if active_view:
            current_file_path = active_view.file_name()
            if current_file_path:
                current_dir = dirname(current_file_path) + sep
        self.input_panel = self.window.show_input_panel("Open:", current_dir, self.on_done_open, self.on_change,
                                                        self.panel_was_closed)

    def on_change(self, text):
        if not text:
            return

        # This hack is needed to circumvent sublime's pesky insert_best_completion key binding for tab that changes
        # our excellent completion.
        if self.last_text is not None and (len(text) - len(self.last_text)) > 1:
            text = self.last_text + "\t"

        self.last_text = text

        need_completion = text.startswith('\t') or text.endswith('\t')
        if text == "~" or text.endswith(sep + "~"):
            text = getenv("HOME") + sep
            need_completion = True

        full_path = text.strip('\t')
        fname = basename(full_path)
        fdir = dirname(full_path)
        new_path = full_path

        all_files_in_dir = listdir(fdir)
        files_in_dir = [name for name in all_files_in_dir if fname.lower() in name.lower()]

        if need_completion:
            if files_in_dir:
                if len(files_in_dir) > 1:
                    new_path = full_path
                    # if all the possible completions start with the same prefix, use that.
                    prefix = commonprefix(files_in_dir)
                    if prefix and len(prefix) > len(fname):
                        new_path = join(fdir, prefix)
                        files_in_dir = [name for name in all_files_in_dir if prefix.lower() in name.lower()]
                else:
                    new_path = join(fdir, files_in_dir[0])
                    # if the new path is a directory, append a / automatically.
                    if isdir(new_path):
                        new_path += sep
                        all_files_in_dir = listdir(new_path)
                        files_in_dir = []
            else:
                new_path = full_path
                sublime.status_message('No files match "%s"' % fname)

        if new_path != full_path or need_completion:
            self.last_text = new_path
            self.input_panel.run_command('open_file_path_replace_panel', dict(contents=new_path))
        self.set_scratch_file_list(fname, all_files_in_dir, files_in_dir)

    def on_done_open(self, text):
        self.panel_was_closed()

        if not exists(text):
            # 'touch' file if it doesn't exist
            try:
                try:
                    f = open(text, 'w')
                finally:
                    f.close()
            except IOError:
                self.message('Unable to create file "[%s]"' % text)

        if isdir(text):
            try:
                import subprocess
                return subprocess.Popen([self.get_sublime_path(), "-a", text])
            except:
                sublime.status_message('Unable to open "%s"' % text)
        else:
            try:
                self.window.open_file(text)
                numGroups = self.window.num_groups()
                currentGroup = self.window.active_group()
                if currentGroup < numGroups - 1:
                    newGroup = currentGroup + 1
                else:
                    newGroup = 0
                self.window.run_command("move_to_group", {"group": newGroup})
            except:
                sublime.status_message('Unable to open "%s"' % text)

    def panel_was_closed(self):
        self.last_text = None
        self.close_scratch_file_list_if_exists()

    def get_view_content(self):
        view = self.window.active_view()

        # Get the default encoding from the settings
        encoding = view.encoding() if view.encoding() != 'Undefined' else 'UTF-8'

        # Get the correctly encoded contents of the view
        file_contents = view.substr(sublime.Region(0, view.size())).encode(encoding)
        return file_contents

    def set_scratch_file_list(self, fname, all_files, completion_files):
        if not self.scratch_file_list_buffer:  # create scratch file list if it doesn't already exist
            self.scratch_file_list_buffer = self.window.new_file()
            self.scratch_file_list_buffer.set_scratch(True)

        titles = []
        highlights = []
        rows = []
        # First create a list of highlighted files:
        if completion_files and len(completion_files) < len(all_files):
            titles.append(len(rows))
            rows.append(u"%d files can be chosen:" % (len(completion_files),))
            rows.append(u"")
            rows += self.create_file_list(completion_files)
            rows.append(u"")
        elif fname and not completion_files:
            titles.append(len(rows))
            rows.append(u"Possible matches:")
            rows.append(u"")
            rows.append(u"No match for file name '{}'".format(fname))
            rows.append(u"")

        if all_files:
            titles.append(len(rows))
            rows.append(u"%d files in the directory:" % (len(all_files),))
            rows.append(u"")
            rows += self.create_file_list(all_files)
        else:
            rows.append(u"No files found in current directory")

        self.scratch_file_list_buffer.run_command('open_file_path_set_buffer_contents',
                                                  dict(contents="\n".join(rows), titles=titles, highlights=highlights))

    def create_file_list(self, files):
        vp_width, vp_height = self.scratch_file_list_buffer.viewport_extent()
        view_height_chars = int(floor(vp_height / self.scratch_file_list_buffer.line_height()))
        view_width_chars = int(floor(vp_width / self.scratch_file_list_buffer.em_width()))

        files = sorted(files)
        num_files = len(files)
        file_max_len = max(len(f) for f in files) if files else 0
        col_size = file_max_len + 5
        max_num_cols = max(1, int(floor(float(view_width_chars) / col_size)))

        num_rows = -1
        num_cols = max_num_cols
        for n_cols in range(max_num_cols):
            num_rows = int(ceil(float(num_files) / (n_cols + 1)))
            if num_rows <= view_height_chars - 5:
                num_cols = n_cols + 1

        if num_rows == -1:
            num_cols = max_num_cols
            num_rows = int(ceil(float(num_files) / num_cols))

        rows = [u"" for i in range(num_rows)]
        files_i = 0
        for c in range(num_cols):
            for r in range(min(num_rows, num_files - c * num_rows)):
                rows[r] += files[files_i].ljust(col_size)
                files_i += 1
        rows = [r.strip() for r in rows]
        return rows

    def close_scratch_file_list_if_exists(self):
        if self.scratch_file_list_buffer:
            self.window.focus_view(self.scratch_file_list_buffer)
            if self.scratch_file_list_buffer.id() == self.window.active_view().id():
                self.window.run_command('close')

    def get_sublime_path(self):
        import sys
        if sublime.platform() == 'osx':
            return '/Applications/Sublime Text 2.app/Contents/SharedSupport/bin/subl'
        if sublime.platform() == 'linux':
            cmd = open('/proc/self/cmdline').read().split(chr(0))[0]
            if cmd.endswith("plugin_host"):
                return sep.join([dirname(cmd), "sublime_text"])
            else:
                return cmd
        return sys.executable


class OpenFilePathSetBufferContentsCommand(sublime_plugin.TextCommand):
    def run(self, edit, contents, titles, highlights, block=False):
        self.view.set_read_only(False)
        self.view.erase(edit, sublime.Region(0, self.view.size()))
        self.view.insert(edit, 0, contents)

        def line_to_region(line):
            tp = self.view.text_point(line, 0)
            return self.view.line(sublime.Region(tp, tp + 1))
        title_regions = [line_to_region(line) for line in titles]

        self.view.add_regions("titles", title_regions, "highlight", "", sublime.DRAW_NO_OUTLINE)

        self.view.set_read_only(True)


class OpenFilePathReplacePanel(sublime_plugin.TextCommand):
    def run(self, edit, contents, block=False):
        region = self.view.full_line(0)
        self.view.replace(edit, region, contents)
