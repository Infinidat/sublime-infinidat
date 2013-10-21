import sublime, sublime_plugin
import os


class OpenEverywhereInsertText(sublime_plugin.TextCommand):
	# the only way to insert text (into the overlay, and in general) is using a TextCommand plugin,
	# so we create one for the sole purpose of adding text to the overlay
	def run(self, edit, text):
		self.view.insert(edit, 0, text)



class OpenEverywhere(sublime_plugin.WindowCommand):
	active = False
	items = None
	dirname = None
	current_item = None

	def run(self):
		OpenEverywhere.active = True
		OpenEverywhere.dirname = None
		OpenEverywhere.current_item = None
		def cancel(index):
			OpenEverywhere.active = False
		# just pop up the window, the listener will take over then
		self.window.show_quick_panel([""], cancel)


class OpenEverywhereListener(sublime_plugin.EventListener):
	def on_done(self, index):
		""" dialog selection callback """
		OpenEverywhere.active = False
		if index == -1:
			return
		item = OpenEverywhere.items[index]
		window = sublime.active_window()
		if os.path.isdir(item):
			sublime.set_timeout(lambda: self.rerun(window, item, item))
		elif os.path.isfile(item):
			window.open_file(item)

	def on_highlighted(self, index):
		if OpenEverywhere.items and len(OpenEverywhere.items) > index:
			item = OpenEverywhere.items[index]
			OpenEverywhere.current_item = item
			sublime.status_message(os.path.basename(item.rstrip(os.sep)))

	def get_dir_items(self, dirname):
		try:
			items = [os.path.join(dirname, f) for f in os.listdir(dirname)]
		except OSError:
			return []
		items = [f + (os.sep if os.path.isdir(f) else "") for f in items]		# add directory indicators
		# put dirs last.
		# TODO IMO they should be first instead, but reversing this sort doesn't change the order in the popup anyway
		items.sort(key=lambda x: os.path.isdir(x))
		return items

	def rerun(self, window, text, dirname):
		"""
		Recalculates the items to show and re-popus the overlay (with the text specified in the parameter).
		Called when the dirname component of the entered text changes, or when we select a directory from the list
		Note that we can't change the items in the overlay dynamically, so we close it and recreate it
		"""
		items = self.get_dir_items(dirname)
		if len(items) == 0:
			# empty dirs or dirs without permissions: we want to reopen the overlay but we can't open it without items,
			# so we use the same items as before and nothing will change. Hope the user understands...
			items = OpenEverywhere.items
		window.run_command("hide_overlay")
		window.show_quick_panel(items, self.on_done, 0, 0, self.on_highlighted)
		OpenEverywhere.items = items
		OpenEverywhere.active = True		# the "hide" command called on_done, which caused this flag to reset
		window.run_command("open_everywhere_insert_text", {"text": text})

	def check_special_text(self, text, window):
		""" quick jump access to other overlay dialogs """
		commands = {"@": ("show_overlay", {"overlay": "goto", "text": "@"} ),
					"#": ("show_overlay", {"overlay": "goto", "text": "#"} ),
					":": ("show_overlay", {"overlay": "goto", "text": ":"} ),
					"ff": ("show_overlay", {"overlay": "goto", "show_files": True} ),
					"cc": ("show_overlay", {"overlay": "command_palette"} ),
					}
		for key, command in commands.items():
			if key in "@#:" and text.endswith(key) and \
			   OpenEverywhere.current_item is not None and os.path.isfile(OpenEverywhere.current_item):
				window.open_file(OpenEverywhere.current_item)
				window.run_command("hide_overlay")
				window.run_command(command[0], command[1])
			elif text == key:
				window.run_command("hide_overlay")
				window.run_command(command[0], command[1])

	def on_modified_async(self, view):
		"""main plugin callback"""
		# We don't check that the view/window is the dialog's, so if the user can somehow open the dialog and then
		# start typing in another buffer/view/dialog/window, it won't be ok. Looks like Sublime doesn't allow this.
		if not OpenEverywhere.active:
			return
		# get text from "view" (it's the dialog)
		text = view.substr(sublime.Region(0, view.size()))
		self.check_special_text(text, view.window())
		text = os.path.expandvars(os.path.expanduser(text))
		dirname = os.path.dirname(text)
		# if the dirname component hasn't changed, there is nothing to do
		if not os.path.exists(dirname) or dirname == OpenEverywhere.dirname:
			return
		OpenEverywhere.dirname = dirname
		self.rerun(view.window(), text, dirname)
