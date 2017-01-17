import sublime_plugin
import os
import json


def find_packages_in(folder, exclude, depth=1):
    package = folder + "/package.json"
    if os.path.exists(package):
        yield package
    elif depth <= 0:
        return
    else:
        children = (os.path.join(folder, i) for i in os.listdir(folder)
                    if i not in exclude)
        subdirs = filter(os.path.isdir, children)
        for dir in subdirs:
            yield from find_packages_in(dir, exclude, depth - 1)


def get_scripts(package):
    with open(package, "r") as f:
        obj = json.load(f)
        return obj.get("scripts", {})


def create_pallette(packages):
    for pkg in packages:
        for script in get_scripts(pkg):
            yield [script, os.path.dirname(pkg)]


def run_script(window, script):
    cmd = ["npm", "run", script[0]]
    # FIXME
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
    cwd = script[1]
    window.run_command("exec", {
        "cmd": cmd,
        "env": env,
        "working_dir": cwd
    })


class NpmRunCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self.selected = 0
        self.load_scripts()

    def load_scripts(self):
        self.scripts = list(create_pallette(self.find_packages()))

    def is_enabled(self):
        return len(self.scripts) > 0

    def find_packages(self):
        exclude = (self.window.active_view()
                   .settings().get("folder_exclude_patterns"))
        for folder in self.window.folders():
            yield from find_packages_in(folder, exclude)

    def choose_script(self, sidx):
        if sidx != -1:
            self.selected = sidx
            run_script(self.window, self.scripts[sidx])

    def run(self):
        self.load_scripts()  # do we really have to call it each time?
        self.window.show_quick_panel(
            self.scripts, self.choose_script, 0, self.selected
        )
