from typing import Any, Optional
import tkinter as tk
from tkinter import ttk

from .renderer import TkRenderer
from .scripts import ScriptEngine


class DeveloperTools:
    def __init__(self, root: tk.Tk, renderer: TkRenderer, engine: ScriptEngine):
        self.root = root
        self.renderer = renderer
        self.engine = engine
        self.window: Optional[tk.Toplevel] = None
        self.network_log = engine.network_log
        self.console_output: Optional[tk.Text] = None
        self.dom_selector: Optional[tk.Entry] = None
        self.dom_text: Optional[tk.Text] = None
        self.cookie_list: Optional[tk.Listbox] = None

    def toggle(self, event: Optional[tk.Event] = None) -> None:  # noqa: ARG002
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.destroy()
            self.window = None
        else:
            self._open_window()

    def _open_window(self) -> None:
        self.window = tk.Toplevel(self.root)
        self.window.title("Developer Tools")
        self.window.geometry("820x520")
        self._apply_window_theme()
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        notebook.add(self._build_console_tab(notebook), text="Console")
        notebook.add(self._build_dom_tab(notebook), text="DOM")
        notebook.add(self._build_network_tab(notebook), text="Network")
        notebook.add(self._build_settings_tab(notebook), text="Settings")
        notebook.add(self._build_cookies_tab(notebook), text="Cookies")

    def _apply_window_theme(self) -> None:
        theme = self.renderer.themes[self.renderer.current_theme]
        self.window.configure(bg=theme["bg"])
        style = ttk.Style(self.window)
        style.configure("TNotebook", background=theme["bg"], foreground=theme["fg"], padding=6)
        style.configure("TNotebook.Tab", background=theme["muted"], foreground=theme["fg"], padding=(10, 6))
        style.map("TNotebook.Tab", background=[("selected", theme["accent"])], foreground=[("selected", theme["bg"])])
        style.configure("Accent.TButton", background=theme["accent"], foreground=theme["bg"], padding=6, relief=tk.FLAT)

    def _build_console_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.renderer.themes[self.renderer.current_theme]["bg"])
        header = tk.Label(frame, text="JavaScript Console", bg=frame["bg"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], font=("TkDefaultFont", 12, "bold"))
        header.pack(anchor="w", padx=8, pady=4)
        input_box = tk.Entry(frame)
        input_box.pack(fill=tk.X, padx=8, pady=4)
        output = tk.Text(frame, height=14, state=tk.DISABLED, bg=self.renderer.themes[self.renderer.current_theme]["muted"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], insertbackground=self.renderer.themes[self.renderer.current_theme]["fg"])
        output.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.console_output = output

        def run_command() -> None:
            code = input_box.get()
            if not code.strip():
                return
            try:
                result = self.engine.evaluate(code)
                result = self.engine.context.eval(code)
                self._append_console(f">>> {code}\n{result}\n")
            except Exception as exc:  # noqa: BLE001
                self._append_console(f"Error: {exc}\n")
            input_box.delete(0, tk.END)

        tk.Button(frame, text="Run", command=run_command, bg=self.renderer.accent_color(), fg=self.renderer.themes[self.renderer.current_theme]["bg"], relief=tk.FLAT).pack(padx=8, pady=6, anchor="e")
        return frame

    def _append_console(self, text: str) -> None:
        if not self.console_output:
            return
        self.console_output.configure(state=tk.NORMAL)
        self.console_output.insert(tk.END, text)
        self.console_output.configure(state=tk.DISABLED)
        self.console_output.see(tk.END)

    def _build_dom_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.renderer.themes[self.renderer.current_theme]["bg"])
        selector_label = tk.Label(frame, text="Selector:", bg=frame["bg"], fg=self.renderer.themes[self.renderer.current_theme]["fg"])
        selector_label.pack(anchor="w", padx=8, pady=2)
        selector_entry = tk.Entry(frame)
        selector_entry.pack(fill=tk.X, padx=8, pady=2)
        editor = tk.Text(frame, height=8, bg=self.renderer.themes[self.renderer.current_theme]["muted"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], insertbackground=self.renderer.themes[self.renderer.current_theme]["fg"])
        editor.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.dom_selector = selector_entry
        self.dom_text = editor

        def load_text() -> None:
            selector = selector_entry.get().strip()
            if not selector:
                return
            elements = self.renderer._select(selector)
            if not elements:
                editor.delete("1.0", tk.END)
                editor.insert(tk.END, "No match")
                return
            editor.delete("1.0", tk.END)
            editor.insert(tk.END, "\n".join([el.widget.cget("text") for el in elements]))

        def apply_text() -> None:
            selector = selector_entry.get().strip()
            new_text = editor.get("1.0", tk.END).strip()
            if selector:
                self.renderer.set_text(selector, new_text)

        button_frame = tk.Frame(frame, bg=frame["bg"])
        button_frame.pack(anchor="e", padx=8, pady=4)
        tk.Button(button_frame, text="Load", command=load_text, bg=self.renderer.themes[self.renderer.current_theme]["muted"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Apply", command=apply_text, bg=self.renderer.accent_color(), fg=self.renderer.themes[self.renderer.current_theme]["bg"], relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=4)
        return frame

    def _build_network_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.renderer.themes[self.renderer.current_theme]["bg"])
        tk.Label(frame, text="Requests", bg=frame["bg"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=8, pady=4)
        listbox = tk.Listbox(frame, bg=self.renderer.themes[self.renderer.current_theme]["muted"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], highlightthickness=0, borderwidth=0)
        listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        for url, status in self.network_log:
            listbox.insert(tk.END, f"{url} -> {status}")
        return frame

    def _build_settings_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.renderer.themes[self.renderer.current_theme]["bg"])
        tk.Label(frame, text="Theme", bg=frame["bg"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=8, pady=4)
        theme_var = tk.StringVar(value=self.renderer.current_theme)
        theme_menu = ttk.Combobox(frame, textvariable=theme_var, values=list(self.renderer.themes.keys()), state="readonly")
        theme_menu.pack(fill=tk.X, padx=8)

        def apply_theme(*args: Any) -> None:  # noqa: ANN401
            self.renderer.apply_theme(theme_var.get())
            self._apply_window_theme()

        theme_menu.bind("<<ComboboxSelected>>", apply_theme)
        return frame

    def _build_cookies_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.renderer.themes[self.renderer.current_theme]["bg"])
        tk.Label(frame, text="Cookies", bg=frame["bg"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=8, pady=4)
        listbox = tk.Listbox(frame, bg=self.renderer.themes[self.renderer.current_theme]["muted"], fg=self.renderer.themes[self.renderer.current_theme]["fg"], highlightthickness=0, borderwidth=0)
        listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.cookie_list = listbox
        self._refresh_cookies()

        form = tk.Frame(frame, bg=frame["bg"])
        form.pack(fill=tk.X, padx=8, pady=4)
        name_entry = tk.Entry(form)
        value_entry = tk.Entry(form)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def save_cookie() -> None:
            name = name_entry.get().strip()
            value = value_entry.get().strip()
            if name:
                self.engine._set_cookie(name, value)
                self._refresh_cookies()

        tk.Button(frame, text="Save", command=save_cookie, bg=self.renderer.accent_color(), fg=self.renderer.themes[self.renderer.current_theme]["bg"], relief=tk.FLAT, padx=10, pady=4).pack(anchor="e", padx=8, pady=4)
        return frame

    def _refresh_cookies(self) -> None:
        if not self.cookie_list:
            return
        self.cookie_list.delete(0, tk.END)
        for name, value in self.engine.cookies.items():
            self.cookie_list.insert(tk.END, f"{name}={value}")
