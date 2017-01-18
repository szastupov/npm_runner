import sublime_plugin
import os
import json


def getenv():
    path = os.environ.get('PATH', '')
    ulb = "/usr/local/bin"
    env = os.environ.copy()

    # Quick and dirty Mac fix
    if ulb not in path:
        env['PATH'] = "%s:%s" % (path, ulb)

    return env


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


def get_package_scripts(package):
    with open(package, "r") as f:
        obj = json.load(f)
        return obj.get("scripts", {})


def get_scripts(packages):
    for pkg in packages:
        for script in get_package_scripts(pkg):
            dirname = os.path.dirname(pkg)
            projname = os.path.basename(dirname)
            yield (script, dirname, projname)


class NpmRunCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self.selected = 0
        self.load_scripts()
        self.env = getenv()

    def load_scripts(self):
        self.packages = list(self.find_packages())
        self.scripts = list(get_scripts(self.packages))

    def is_enabled(self):
        return len(self.scripts) > 0

    def find_packages(self):
        exclude = (self.window.active_view()
                   .settings().get("folder_exclude_patterns"))
        for folder in self.window.folders():
            yield from find_packages_in(folder, exclude)

    def run_script(self, script):
        cmd = ["npm", "run", script[0]]
        cwd = script[1]
        self.window.run_command("exec", {
            "cmd": cmd,
            "env": self.env,
            "working_dir": cwd
        })

    def choose_script(self, sidx):
        if sidx != -1:
            self.selected = sidx
            self.run_script(self.scripts[sidx])

    def render(self):
        if len(self.packages) > 1:
            return ["%s: %s" % (proj, script)
                    for script, _, proj in self.scripts]
        else:
            return [s[0] for s in self.scripts]

    def run(self):
        self.load_scripts()  # do we really have to call it each time?

        self.window.show_quick_panel(
            self.render(), self.choose_script, 0, self.selected
        )
