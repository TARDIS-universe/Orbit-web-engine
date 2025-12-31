from typing import Dict, List, Optional, Tuple
from tkinter import messagebox

from .renderer import TkRenderer


class ScriptEngine:
    """
    Lightweight, custom JavaScript-like evaluator.
    Translates a small subset of JS syntax into Python and executes it against
    a sandboxed environment that exposes renderer helpers (DOM setters/getters,
    styles, events, cookies, and a stubbed fetch).
    """

    def __init__(self, renderer: TkRenderer, network_log: Optional[List[Tuple[str, str]]] = None, cookies: Optional[Dict[str, str]] = None):
        self.renderer = renderer
        self.network_log = network_log if network_log is not None else []
        self.cookies = cookies if cookies is not None else {}
        safe_builtins = {
            "len": len,
            "min": min,
            "max": max,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "print": print,
            "range": range,
        }
        self.env: Dict[str, object] = {"__builtins__": safe_builtins}
        self._bind_helpers()

    def _bind_helpers(self) -> None:
        class Console:
            @staticmethod
            def log(*args: object) -> None:
                print("[JS]", *args)

        helpers = {
            "alert": lambda msg: messagebox.showinfo("Alert", str(msg)),
            "setText": lambda selector, value: self.renderer.set_text(selector, str(value)),
            "getText": lambda selector: self.renderer.get_text(selector),
            "setStyle": lambda selector, prop, value: self.renderer.set_style(selector, prop, str(value)),
            "onClick": lambda selector, cb: self.renderer.on_click(selector, cb),
            "console": Console(),
            "setCookie": lambda name, value: self._set_cookie(str(name), str(value)),
            "getCookie": lambda name: self.cookies.get(str(name), ""),
            "fetch": lambda url: self._fake_fetch(str(url)),
            "True": True,
            "False": False,
            "None": None,
        }
        self.env.update(helpers)

    def run_scripts(self, scripts: List[str]) -> None:
        for script in scripts:
            try:
                self.execute(script)
            except Exception as exc:  # noqa: BLE001
                print(f"Script error: {exc}")

    def execute(self, js_code: str) -> None:
        python_code = self._translate(js_code)
        exec(python_code, self.env)

    def evaluate(self, js_snippet: str) -> object:
        python_code = self._translate(js_snippet)
        try:
            compiled = compile(python_code, "<js-eval>", "eval")
            return eval(compiled, self.env)
        except SyntaxError:
            exec(python_code, self.env)
            return None

    def _set_cookie(self, name: str, value: str) -> None:
        self.cookies[name] = value

    def _fake_fetch(self, url: str) -> str:
        self.network_log.append((url, "200 OK"))
        return f"Fetched {url}"

    def _translate(self, js_code: str) -> str:
        """Translate a tiny subset of JS into executable Python code."""

        def normalize_line(line: str) -> str:
            replacements = {
                "const ": "",
                "let ": "",
                "var ": "",
                "===": "==",
                "!==": "!=",
                "&&": " and ",
                "||": " or ",
                "true": "True",
                "false": "False",
                "null": "None",
            }
            for key, value in replacements.items():
                line = line.replace(key, value)
            return line.rstrip(";")

        lines: List[str] = []
        indent = 0

        for raw_line in js_code.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            while stripped.startswith("}"):
                indent = max(0, indent - 1)
                stripped = stripped[1:].lstrip()

            if not stripped:
                continue

            opens_block = stripped.endswith("{")
            if opens_block:
                stripped = stripped[:-1].rstrip()

            if stripped.startswith("function "):
                after = stripped[len("function ") :]
                name, _, rest = after.partition("(")
                args, _, _ = rest.partition(")")
                lines.append(f"{'    ' * indent}def {name.strip()}({args.strip()}):")
                indent += 1
                continue

            if stripped.startswith("return"):
                expression = stripped[len("return") :].strip()
                normalized = normalize_line(expression)
                lines.append(f"{'    ' * indent}return {normalized}".rstrip())
                continue

            if stripped.startswith("if "):
                condition = normalize_line(stripped[len("if ") :])
                lines.append(f"{'    ' * indent}if {condition}:")
                if opens_block:
                    indent += 1
                continue

            if stripped.startswith("else if "):
                condition = normalize_line(stripped[len("else if ") :])
                lines.append(f"{'    ' * indent}elif {condition}:")
                if opens_block:
                    indent += 1
                continue

            if stripped.startswith("else"):
                lines.append(f"{'    ' * indent}else:")
                if opens_block:
                    indent += 1
                continue

            normalized = normalize_line(stripped)
            suffix = ":" if opens_block else ""
            lines.append(f"{'    ' * indent}{normalized}{suffix}")
            if opens_block:
                indent += 1

        return "\n".join(lines)
