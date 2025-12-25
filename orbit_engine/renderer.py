from typing import Any, Dict, List, Optional
import tkinter as tk

from .css import StyleResolver
from .dom import DOMNode


class RenderedElement:
    def __init__(self, node: DOMNode, widget: tk.Widget):
        self.node = node
        self.widget = widget


class TkRenderer:
    def __init__(self, root: tk.Tk, dom: DOMNode, styles: StyleResolver):
        self.root = root
        self.dom = dom
        self.styles = styles
        self.widgets: Dict[DOMNode, RenderedElement] = {}
        self.id_map: Dict[str, RenderedElement] = {}
        self.class_map: Dict[str, List[RenderedElement]] = {}
        self.event_handlers: Dict[tk.Widget, Any] = {}
        self.current_theme: str = "dark"
        self.themes: Dict[str, Dict[str, str]] = {
            "dark": {"bg": "#0f172a", "fg": "#e2e8f0", "accent": "#38bdf8", "muted": "#1f2937"},
            "light": {"bg": "#f8fafc", "fg": "#0f172a", "accent": "#2563eb", "muted": "#e2e8f0"},
            "forest": {"bg": "#0b1d14", "fg": "#d9ead3", "accent": "#34d399", "muted": "#123222"},
            "sunset": {"bg": "#2c0f1c", "fg": "#ffe4e6", "accent": "#fb7185", "muted": "#3b1428"},
        }

    def render(self) -> None:
        body = next((child for child in self.dom.children if child.tag == "body"), self.dom)
        container = tk.Frame(self.root, bg=self.themes[self.current_theme]["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        self._render_children(body, container)
        self.apply_theme(self.current_theme)

    def _render_children(self, node: DOMNode, parent: tk.Widget) -> None:
        for child in node.children:
            if child.tag in {"script", "style"}:
                continue
            if child.is_text():
                label = tk.Label(parent, text=child.text, anchor="w", justify="left")
                label.pack(fill=tk.X, anchor="w")
                continue
            widget = self._create_widget_for_tag(child, parent)
            if widget is None:
                self._render_children(child, parent)
                continue
            self._apply_styles(child, widget)
            self._register_node(child, widget)
            if child.children:
                self._render_children(child, widget)

    def _register_node(self, node: DOMNode, widget: tk.Widget) -> None:
        rendered = RenderedElement(node, widget)
        self.widgets[node] = rendered
        node_id = node.attrs.get("id")
        if node_id:
            self.id_map[node_id] = rendered
        for cls in node.attrs.get("class", "").split():
            self.class_map.setdefault(cls, []).append(rendered)

    def _apply_styles(self, node: DOMNode, widget: tk.Widget) -> None:
        style = self.styles.for_node(node)
        if not style:
            widget.pack(fill=tk.X, anchor="w", pady=4)
            return
        config: Dict[str, Any] = {}
        pack_kwargs: Dict[str, Any] = {"fill": tk.X, "anchor": "w", "pady": 4, "padx": 2}
        for key, value in style.items():
            if key in {"background", "background-color"}:
                config["bg"] = value
            elif key in {"color", "font-color"}:
                config["fg"] = value
            elif key == "font-size":
                try:
                    size = int(value.replace("px", ""))
                    config["font"] = ("TkDefaultFont", size)
                except ValueError:
                    pass
            elif key == "text-align":
                if value == "center":
                    config["anchor"] = "center"
                    config["justify"] = tk.CENTER
                elif value == "right":
                    config["anchor"] = "e"
                    config["justify"] = tk.RIGHT
            elif key == "padding":
                try:
                    pad = int(value.replace("px", ""))
                    pack_kwargs["padx"] = pad
                    pack_kwargs["pady"] = pad
                except ValueError:
                    pass
        if config:
            widget.configure(**config)
        widget.pack(**pack_kwargs)

    def _create_widget_for_tag(self, node: DOMNode, parent: tk.Widget) -> Optional[tk.Widget]:
        tag = node.tag.lower()
        text = node.attrs.get("text", "") or node.text
        if tag in {"div", "body", "section"}:
            return tk.Frame(parent)
        if tag in {"p", "span", "label"}:
            return tk.Label(parent, text=text, anchor="w", justify="left")
        if tag in {"h1", "h2", "h3"}:
            size = {"h1": 24, "h2": 20, "h3": 18}.get(tag, 16)
            return tk.Label(parent, text=text, font=("TkDefaultFont", size, "bold"), anchor="w", justify="left")
        if tag == "button":
            return tk.Button(parent, text=text or node.attrs.get("value", "Button"), relief=tk.FLAT, bd=0, pady=6, padx=12)
        if tag == "input":
            entry = tk.Entry(parent)
            if "value" in node.attrs:
                entry.insert(0, node.attrs.get("value", ""))
            return entry
        return tk.Label(parent, text=f"<{tag}>", fg="#555", anchor="w", justify="left")

    def set_text(self, selector: str, value: str) -> None:
        for element in self._select(selector):
            if isinstance(element.widget, tk.Entry):
                element.widget.delete(0, tk.END)
                element.widget.insert(0, value)
            else:
                element.widget.configure(text=value)

    def get_text(self, selector: str) -> str:
        values: List[str] = []
        for element in self._select(selector):
            if isinstance(element.widget, tk.Entry):
                values.append(element.widget.get())
            else:
                values.append(element.widget.cget("text"))
        return " ".join(values)

    def set_style(self, selector: str, prop: str, value: str) -> None:
        for element in self._select(selector):
            element.widget.configure(**self._tk_style_from_prop(prop, value))

    def _tk_style_from_prop(self, prop: str, value: str) -> Dict[str, Any]:
        if prop in {"background", "background-color"}:
            return {"bg": value}
        if prop in {"color", "font-color"}:
            return {"fg": value}
        if prop == "font-size":
            try:
                size = int(value.replace("px", ""))
                return {"font": ("TkDefaultFont", size)}
            except ValueError:
                return {}
        return {}

    def apply_theme(self, name: str) -> None:
        theme = self.themes.get(name, self.themes["dark"])
        self.current_theme = name
        self.root.configure(bg=theme["bg"])
        for element in self.widgets.values():
            widget = element.widget
            try:
                widget.configure(bg=theme["bg"], fg=theme.get("fg"))
                if isinstance(widget, tk.Button):
                    widget.configure(bg=theme.get("accent"), fg=theme.get("bg"), activebackground=theme.get("muted"))
            except tk.TclError:
                pass

    def accent_color(self) -> str:
        return self.themes.get(self.current_theme, {}).get("accent", "#38bdf8")

    def on_click(self, selector: str, callback: Any) -> None:
        for element in self._select(selector):
            if isinstance(element.widget, tk.Button):
                element.widget.configure(command=lambda cb=callback: cb())

    def _select(self, selector: str) -> List[RenderedElement]:
        selector = selector.strip()
        if selector.startswith("#"):
            node_id = selector[1:]
            result = self.id_map.get(node_id)
            return [result] if result else []
        if selector.startswith("."):
            return list(self.class_map.get(selector[1:], []))
        return [elem for elem in self.widgets.values() if elem.node.tag == selector]
