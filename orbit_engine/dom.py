from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple


class DOMNode:
    def __init__(self, tag: str, attrs: Optional[Dict[str, str]] = None, parent: "DOMNode" = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: List[DOMNode] = []
        self.parent = parent
        self.text: str = ""

    def add_child(self, child: "DOMNode") -> None:
        self.children.append(child)

    def is_text(self) -> bool:
        return self.tag == "__text__"


class TinyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root = DOMNode("document")
        self.stack: List[DOMNode] = [self.root]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = {name: value or "" for name, value in attrs}
        node = DOMNode(tag, attr_dict, parent=self.stack[-1])
        self.stack[-1].add_child(node)
        self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        while len(self.stack) > 1:
            node = self.stack.pop()
            if node.tag == tag:
                break

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        text_node = DOMNode("__text__", parent=self.stack[-1])
        text_node.text = data
        self.stack[-1].add_child(text_node)


def parse_html(html: str) -> DOMNode:
    parser = TinyHTMLParser()
    parser.feed(html)
    return parser.root


def collect_rules(dom: DOMNode) -> List["StyleRule"]:
    from .css import parse_css, StyleRule  # Imported here to avoid a circular import.

    rules: List[StyleRule] = []
    for child in dom.children:
        if child.tag == "style":
            rules.extend(parse_css(child.text))
        else:
            rules.extend(collect_rules(child))
    return rules


def collect_scripts(dom: DOMNode) -> List[str]:
    scripts: List[str] = []
    for child in dom.children:
        if child.tag == "script":
            scripts.append(child.text)
        else:
            scripts.extend(collect_scripts(child))
    return scripts
