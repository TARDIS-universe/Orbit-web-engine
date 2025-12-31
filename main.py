import tkinter as tk
from tkinter import ttk
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from typing import List, Optional, Tuple

from orbit_engine.dom import collect_rules, collect_scripts, parse_html
from orbit_engine.css import StyleResolver
from orbit_engine.renderer import TkRenderer
from orbit_engine.scripts import ScriptEngine
from orbit_engine.devtools import DeveloperTools
from orbit_engine.sample_html import SAMPLE_HTML


class ExternalCollector(HTMLParser):
    """Collect external stylesheet/script references for inlining."""

    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: List[str] = []
        self.scripts: List[str] = []

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        attr_map = {k: v for k, v in attrs}
        if tag.lower() == "link" and attr_map.get("rel") == "stylesheet" and "href" in attr_map:
            self.stylesheets.append(attr_map["href"])
        if tag.lower() == "script" and "src" in attr_map:
            self.scripts.append(attr_map["src"])


def fetch_text(url: str) -> str:
    with urlopen(url, timeout=10) as resp:
        content_type = resp.headers.get_content_charset()
        encoding = content_type or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def inline_external_assets(html: str, base_url: str, network_log: List[Tuple[str, str]]) -> str:
    collector = ExternalCollector()
    collector.feed(html)

    injected: List[str] = []

    def log_and_fetch(resource_url: str) -> str:
        network_log.append((resource_url, "requested"))
        return fetch_text(resource_url)

    for href in collector.stylesheets:
        css_url = urljoin(base_url, href)
        try:
            css_text = log_and_fetch(css_url)
            injected.append(f"<style>\n{css_text}\n</style>")
            network_log.append((css_url, "200 OK"))
        except (HTTPError, URLError) as exc:
            network_log.append((css_url, f"error: {exc}"))
    for src in collector.scripts:
        js_url = urljoin(base_url, src)
        try:
            js_text = log_and_fetch(js_url)
            injected.append(f"<script>\n{js_text}\n</script>")
            network_log.append((js_url, "200 OK"))
        except (HTTPError, URLError) as exc:
            network_log.append((js_url, f"error: {exc}"))

    injection = "\n".join(injected)
    if "</head>" in html:
        return html.replace("</head>", injection + "\n</head>", 1)
    return html + injection


class TabSession:
    def __init__(self, root: tk.Tk, container: ttk.Notebook, title: str, html: str):
        self.root = root
        self.container = container
        self.network_log: List[Tuple[str, str]] = []
        self.cookies: dict = {}
        self.frame = tk.Frame(container, bg="#0f172a")
        self.renderer: Optional[TkRenderer] = None
        self.engine: Optional[ScriptEngine] = None
        self.devtools: Optional[DeveloperTools] = None
        self.base_url: Optional[str] = None
        self.container.add(self.frame, text=title)
        self.load_html(html)

    def load_html(self, html: str, base_url: Optional[str] = None) -> None:
        self.base_url = base_url
        for child in list(self.frame.winfo_children()):
            child.destroy()
        dom = parse_html(html)
        styles = StyleResolver(collect_rules(dom))
        self.renderer = TkRenderer(self.frame, dom, styles)
        self.renderer.render()
        self.engine = ScriptEngine(self.renderer, network_log=self.network_log, cookies=self.cookies)
        self.devtools = DeveloperTools(self.root, self.renderer, self.engine)
        scripts = collect_scripts(dom)
        self.engine.run_scripts(scripts)

    def show_devtools(self) -> None:
        if self.devtools:
            self.devtools.toggle()


class OrbitBrowser:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Orbit Web Engine Prototype")
        self.root.geometry("1100x720")

        self.url_var = tk.StringVar(value="https://example.com")

        top = tk.Frame(self.root)
        top.pack(fill=tk.X, pady=6, padx=8)
        tk.Label(top, text="URL:").pack(side=tk.LEFT, padx=(0, 6))
        url_entry = tk.Entry(top, textvariable=self.url_var)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(top, text="Go", command=self.load_current_tab).pack(side=tk.LEFT, padx=6)
        tk.Button(top, text="New Tab", command=self.new_tab).pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tabs: List[TabSession] = []
        self.tabs.append(TabSession(self.root, self.notebook, "Sample", SAMPLE_HTML))
        self.root.bind("<F12>", lambda event=None: self.toggle_devtools())
        self.root.bind("<Control-Alt-d>", lambda event=None: self.toggle_devtools())

    def current_tab(self) -> TabSession:
        current_id = self.notebook.select()
        for tab in self.tabs:
            if str(tab.frame) == current_id:
                return tab
        return self.tabs[0]

    def new_tab(self) -> None:
        tab = TabSession(self.root, self.notebook, f"Tab {len(self.tabs)+1}", SAMPLE_HTML)
        self.tabs.append(tab)
        self.notebook.select(tab.frame)

    def toggle_devtools(self) -> None:
        self.current_tab().show_devtools()

    def load_current_tab(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            return
        if "://" not in url:
            url = f"http://{url}"
            self.url_var.set(url)
        tab = self.current_tab()
        try:
            html = fetch_text(url)
            html = inline_external_assets(html, url, tab.network_log)
            tab.load_html(html, base_url=url)
            self.notebook.tab(tab.frame, text=url)
        except (HTTPError, URLError) as exc:
            tab.network_log.append((url, f"error: {exc}"))

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    OrbitBrowser().run()
