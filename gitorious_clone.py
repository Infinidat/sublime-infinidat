import sublime, sublime_plugin
import os
import json
import subprocess
import threading
import time
import itertools


class GitLabClone(sublime_plugin.WindowCommand):
    def _projector_clone(self, git_url, clone_dst):
        proc = subprocess.Popen([self._projector_path, "repository", "clone", git_url], cwd=clone_dst)
        returncode = proc.wait()
        if returncode == 0:
            self.window.active_view().set_status("tkc", "Cloning done")
        else:
            self.window.active_view().set_status("tkc", "Cloning failed with code {}".format(returncode))

    def _refresh_progress(self):
        if self.selected:
            # user has already selected the repo, stop bugging with status messages
            return
        p = next(self._progress)
        verb = "Refreshing" if self.repo_list else "Loading"
        self.window.active_view().set_status("tkc", verb + " repository list [" + " " * p + "=" + " " * (4 - p) + "]")

    def _refresh_repo_items(self):
        self._progress = itertools.cycle(list(range(5)) + list(reversed(list(range(1, 4)))))
        proc = subprocess.Popen([self._projector_path, "gitlab", "list"], stdout=subprocess.PIPE)
        while proc.poll() is None:
            self._refresh_progress()
            time.sleep(0.2)
        data = proc.stdout.read()
        self.repo_list = json.loads(data.decode("ascii").replace("'", "\""))
        json.dump(self.repo_list, open(self._cache_file, "w"))
        repo_items = sorted(list(self.repo_list.items()), key=lambda kv: kv[0])
        if self.repo_items == repo_items:
            self.window.active_view().set_status("tkc", "")
            return
        self.repo_items = repo_items
        if not self.selected:
            # user is still viewing the repository list, so reload it
            self.window.run_command("hide_overlay")
            self.window.show_quick_panel([k for k, v in self.repo_items], self.on_repo_select, selected_index=self._current_index)

    def on_dst_select(self, clone_dst):
        clone_dst = os.path.expanduser(clone_dst)
        self.window.active_view().set_status("tkc", "Cloning {} into {}...".format(self.git_url, clone_dst))
        clone_thread = threading.Thread(target=self._projector_clone, args=(self.git_url, clone_dst))
        clone_thread.start()

    def on_repo_select(self, index):
        self.selected = True
        self.window.active_view().set_status("tkc", "")
        if index < 0:
            return
        self.git_url = self.repo_items[index][1]
        self.window.show_input_panel("Clone destination: ", "", self.on_dst_select, None, None)

    def _load_settings(self):
        settings = sublime.load_settings("Infinidat.sublime-settings")
        self._projector_path = os.path.expanduser(settings.get("projector-path"))
        self._cache_file = os.path.expanduser(settings.get("gitlab-cache-file"))

    def _on_highlighted(self, item_index):
        self._current_index = item_index

    def run(self):
        self._load_settings()
        if not os.path.exists(self._projector_path):
            return
        self.selected = False
        self._current_index = 0
        self.repo_list = dict()
        if os.path.exists(self._cache_file):
            self.repo_list = json.load(open(self._cache_file))
        self.repo_items = sorted(list(self.repo_list.items()), key=lambda kv: kv[0])
        self.refresh_thread = threading.Thread(target=self._refresh_repo_items)
        self.refresh_thread.start()
        self.window.show_quick_panel([k for k, v in self.repo_items], self.on_repo_select, on_highlight=self._on_highlighted)
