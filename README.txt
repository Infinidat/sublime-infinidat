FEATURES
========

Select All Lines
----------------
    Extend the cursor to all lines of the file. By default, sublime has commands to extend the cursor one line up
    or one line down. Using this feature, the user can select multiple lines at once: either all the way down from the
    current position to the end of the file, or all the way up from the current cursor position to the beginning of the
    file, or all the lines in the file regardless of current cursor position.
    To use, define keyboard shortcuts, for exmaple:

        { "keys": ["alt+shift+pageup"], "command": "select_all_lines", "args": {"direction": "backward"} },
        { "keys": ["alt+shift+pagedown"], "command": "select_all_lines", "args": {"direction": "forward"} },
        { "keys": ["alt+shift+f3"], "command": "select_all_lines", "args": {"direction": "all"} }

Open Everywhere
---------------
    Use Sublime's quick panel to open files anywhere on the computer, not just files in the current project.
    Activate using Command Palette (Infinidat: Open Anything) or define keyboard shortcut, for example:

        { "keys": ["ctrl+o"], "command": "open_everywhere" }

Grep
----
    Find all lines containing the current selection and remove all other lines (grep the current selection)
    or exclude them (i.e. grep -v).
    Also supports grepping in log files, where some log entries expand over multiple lines, so the grep extends
    to all entry lines.

    Activate using the Command Palette:
        Infinidat: Grep
        Infinidat: Grep Exclude
        Infinidat: Log Grep
        Infinidat: Log Grep Exclude
        Infinidat: Grep Traceback
        Infinidat: Expand Log Message

    Or define keyboard shortcut, for example:

        { "keys": ["ctrl+shift+g"], "command": "grep" }


INFINIDAT-SPECIFIC FEATURES
===========================

Diagnostics
-----------
    This feature allows easy navigation in log qfiles and sets of log files (with log rotation)
    written in a specific format.

    Activate using the Command Palette:
        Infinidat: Goto Log
        Infinidat: Goto Date
        Infinidat: Goto Timestamp
        Infinidat: Goto Trace
        Infinidat: Goto Other Node
        Infinidat: Open Next File
        Infinidat: Open Previous File

Gitorious clone
---------------
    Quickly clone a git repository from a Gitorious server. When activated, the plugin fetches the
    repository list and shows the list using Sublime's quick panel.
    Fetching the list and cloning are done by infi.projector - the path to the projector executable must
    be defined in the plugin settings.

    Activate using the Command Palette (Infinidat: Gitorious Clone) or define keyboard shortcut, for example:

        { "keys": ["ctrl+shift+c"], "command": "gitorious_clone" }
