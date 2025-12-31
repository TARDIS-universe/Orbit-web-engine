from typing import Any, Dict, List, Optional

from .dom import DOMNode


class StyleRule:
    def __init__(self, selector: str, declarations: Dict[str, str]):
        self.selector = selector.strip()
        self.declarations = declarations


def parse_css(css_text: str) -> List[StyleRule]:
    rules: List[StyleRule] = []
    for block in css_text.split("}"):
        if "{" not in block:
            continue
        selector, declarations = block.split("{", 1)
        selector = selector.strip()
        if not selector:
            continue
        decls: Dict[str, str] = {}
        for line in declarations.split(";"):
            if ":" not in line:
                continue
            prop, value = line.split(":", 1)
            decls[prop.strip()] = value.strip()
        rules.append(StyleRule(selector, decls))
    return rules


def inline_style_to_dict(style_value: str) -> Dict[str, str]:
    declarations: Dict[str, str] = {}
    for part in style_value.split(";"):
        if ":" not in part:
            continue
        prop, value = part.split(":", 1)
        declarations[prop.strip()] = value.strip()
    return declarations


def matches_selector(node: DOMNode, selector: str) -> bool:
    if selector.startswith("#"):
        return node.attrs.get("id") == selector[1:]
    if selector.startswith("."):
        classes = node.attrs.get("class", "").split()
        return selector[1:] in classes
    return node.tag == selector


class StyleResolver:
    def __init__(self, rules: List[StyleRule], class_defaults: Optional[Dict[str, Dict[str, str]]] = None):
        self.rules = rules
        self.class_defaults = class_defaults or self._default_class_styles()

    def for_node(self, node: DOMNode) -> Dict[str, str]:
        style: Dict[str, str] = {}
        for rule in self.rules:
            if matches_selector(node, rule.selector):
                style.update(rule.declarations)
        for cls in node.attrs.get("class", "").split():
            if cls and cls in self.class_defaults:
                style.update(self.class_defaults[cls])
        if "style" in node.attrs:
            style.update(inline_style_to_dict(node.attrs["style"]))
        return style

    def _default_class_styles(self) -> Dict[str, Dict[str, str]]:
        return {
            "text-center": {"text-align": "center"},
            "text-right": {"text-align": "right"},
            "muted": {"color": "#94a3b8"},
            "card": {"background": "#1f2937", "color": "#e5e7eb", "padding": "12px"},
            "panel": {"background": "#111827", "color": "#e5e7eb", "padding": "12px"},
            "input": {"padding": "6px"},
            "btn": {"padding": "8px", "background": "#1f2937", "color": "#e5e7eb"},
            "btn-primary": {"padding": "8px", "background": "#2563eb", "color": "#f8fafc"},
            "btn-secondary": {"padding": "8px", "background": "#475569", "color": "#f8fafc"},
            "btn-danger": {"padding": "8px", "background": "#ef4444", "color": "#f8fafc"},
            "badge": {"padding": "4px", "background": "#334155", "color": "#e5e7eb"},
        }

    def accent_color(self, themes: Dict[str, Dict[str, str]], current: str) -> str:
        return themes.get(current, {}).get("accent", "#38bdf8")

    def apply_widget_styles(self, widget: Any, theme: Dict[str, str]) -> None:
        try:
            widget.configure(bg=theme.get("bg"), fg=theme.get("fg"))
        except Exception:  # noqa: BLE001
            pass
