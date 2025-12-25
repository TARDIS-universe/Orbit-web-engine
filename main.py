import tkinter as tk

from orbit_engine.dom import collect_rules, collect_scripts, parse_html
from orbit_engine.css import StyleResolver
from orbit_engine.renderer import TkRenderer
from orbit_engine.scripts import ScriptEngine
from orbit_engine.devtools import DeveloperTools
from orbit_engine.sample_html import SAMPLE_HTML


def render_html(html: str) -> None:
    dom = parse_html(html)
    styles = StyleResolver(collect_rules(dom))
    root = tk.Tk()
    root.title("Orbit Web Engine Prototype")
    root.geometry("960x640")
    renderer = TkRenderer(root, dom, styles)
    renderer.render()

    network_log = []
    cookies = {}
    engine = ScriptEngine(renderer, network_log=network_log, cookies=cookies)
    devtools = DeveloperTools(root, renderer, engine)
    root.bind("<F12>", devtools.toggle)
    root.bind("<Control-Alt-d>", devtools.toggle)
    scripts = collect_scripts(dom)
    engine.run_scripts(scripts)
    root.mainloop()


if __name__ == "__main__":
    render_html(SAMPLE_HTML)
