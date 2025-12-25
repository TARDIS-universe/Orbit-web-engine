from typing import Dict, List, Optional, Tuple
from tkinter import messagebox

import js2py

from .renderer import TkRenderer


class ScriptEngine:
    def __init__(self, renderer: TkRenderer, network_log: Optional[List[Tuple[str, str]]] = None, cookies: Optional[Dict[str, str]] = None):
        self.renderer = renderer
        self.context = js2py.EvalJs()
        self.network_log = network_log if network_log is not None else []
        self.cookies = cookies if cookies is not None else {}
        self._bind_helpers()

    def _bind_helpers(self) -> None:
        self.context.alert = lambda msg: messagebox.showinfo("Alert", str(msg))
        self.context.setText = lambda selector, value: self.renderer.set_text(selector, str(value))
        self.context.getText = lambda selector: self.renderer.get_text(selector)
        self.context.setStyle = lambda selector, prop, value: self.renderer.set_style(selector, prop, str(value))
        self.context.onClick = lambda selector, cb: self.renderer.on_click(selector, cb)
        self.context.console = {"log": lambda *args: print("[JS]", *args)}
        self.context.setCookie = lambda name, value: self._set_cookie(str(name), str(value))
        self.context.getCookie = lambda name: self.cookies.get(str(name), "")
        self.context.fetch = lambda url: self._fake_fetch(str(url))

    def run_scripts(self, scripts: List[str]) -> None:
        for script in scripts:
            try:
                self.context.execute(script)
            except Exception as exc:  # noqa: BLE001
                print(f"Script error: {exc}")

    def _set_cookie(self, name: str, value: str) -> None:
        self.cookies[name] = value

    def _fake_fetch(self, url: str) -> str:
        self.network_log.append((url, "200 OK"))
        return f"Fetched {url}"
