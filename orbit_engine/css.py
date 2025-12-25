from typing import Any, Dict, List

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
    def __init__(self, rules: List[StyleRule]):
        self.rules = rules

    def for_node(self, node: DOMNode) -> Dict[str, str]:
        style: Dict[str, str] = {}
        for rule in self.rules:
            if matches_selector(node, rule.selector):
                style.update(rule.declarations)
        if "style" in node.attrs:
            style.update(inline_style_to_dict(node.attrs["style"]))
        return style

    def accent_color(self, themes: Dict[str, Dict[str, str]], current: str) -> str:
        return themes.get(current, {}).get("accent", "#38bdf8")

    def apply_widget_styles(self, widget: Any, theme: Dict[str, str]) -> None:
        try:
            widget.configure(bg=theme.get("bg"), fg=theme.get("fg"))
        except Exception:  # noqa: BLE001
            pass
