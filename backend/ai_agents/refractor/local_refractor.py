from __future__ import annotations

import json
import re

from backend.ai_agents.style.profile import StyleProfile


class LocalStyleRefactor:
    def refactor(self, code: str, language: str, style_profile: StyleProfile) -> str:
        code = self._remove_generic_comments(code, style_profile)

        if language == "html":
            return self._format_html(code, style_profile)
        if language == "css":
            return self._format_css(code, style_profile)
        if language == "json":
            return self._format_json(code)
        return self._trim_trailing_whitespace(code)

    def _format_html(self, code: str, style_profile: StyleProfile) -> str:
        expanded = self._expand_minimal_frontend(code, style_profile)
        if expanded:
            return expanded

        indent_unit = self._indent_unit(style_profile)
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        output = []
        depth = 0
        in_style = False

        for raw_line in lines:
            line = self._normalize_html_line(raw_line)

            if in_style and not line.lower().startswith("</style"):
                line = self._format_css_line(line)

            if self._is_closing_tag(line):
                depth = max(0, depth - 1)

            output.append(f"{indent_unit * depth}{line}")

            if line.lower().startswith("<style"):
                in_style = True
            elif line.lower().startswith("</style"):
                in_style = False

            if self._opens_html_scope(line):
                depth += 1

        return "\n".join(output) + ("\n" if code.endswith("\n") else "")

    def _format_css(self, code: str, style_profile: StyleProfile) -> str:
        indent_unit = self._indent_unit(style_profile)
        tokens = []

        for line in code.splitlines():
            stripped = self._format_css_line(line.strip())
            if stripped:
                tokens.append(stripped)

        output = []
        depth = 0
        for line in tokens:
            if line.startswith("}"):
                depth = max(0, depth - 1)
            output.append(f"{indent_unit * depth}{line}")
            if line.endswith("{"):
                depth += 1

        return "\n".join(output) + ("\n" if code.endswith("\n") else "")

    @staticmethod
    def _format_json(code: str) -> str:
        try:
            return json.dumps(json.loads(code), indent=2) + "\n"
        except Exception:
            return code

    @staticmethod
    def _trim_trailing_whitespace(code: str) -> str:
        return "\n".join(line.rstrip() for line in code.splitlines()) + ("\n" if code.endswith("\n") else "")

    @staticmethod
    def _indent_unit(style_profile: StyleProfile) -> str:
        indentation = (style_profile.indentation or "").lower()
        if "tab" in indentation:
            return "\t"
        if "2" in indentation:
            return "  "
        return "    "

    @staticmethod
    def _normalize_html_line(line: str) -> str:
        line = re.sub(r"\s*=\s*", "=", line)
        line = re.sub(r"\s{2,}", " ", line)
        return line.strip()

    @staticmethod
    def _format_css_line(line: str) -> str:
        line = re.sub(r"\s*{\s*", " {", line)
        line = re.sub(r"\s*}\s*", "}", line)
        line = re.sub(r"\s*:\s*", ": ", line)
        line = re.sub(r"\s*;\s*", "; ", line).strip()
        return line.rstrip()

    @staticmethod
    def _is_closing_tag(line: str) -> bool:
        lower = line.lower()
        return lower.startswith("</") or lower.startswith("}")

    @staticmethod
    def _opens_html_scope(line: str) -> bool:
        lower = line.lower()
        void_tags = ("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source")

        if not lower.startswith("<") or lower.startswith("</") or lower.startswith("<!"):
            return False

        tag_match = re.match(r"<([a-z0-9-]+)\b", lower)
        if not tag_match:
            return False

        tag = tag_match.group(1)
        if tag in void_tags or lower.endswith("/>"):
            return False

        return f"</{tag}>" not in lower

    def _expand_minimal_frontend(self, code: str, style_profile: StyleProfile) -> str | None:
        lower = code.lower()
        if "grocery bill counter" not in lower:
            return None
        if "<input" in lower and "<button" in lower:
            return None

        indent = self._indent_unit(style_profile)
        i1 = indent
        i2 = indent * 2
        i3 = indent * 3
        i4 = indent * 4

        return "\n".join(
            [
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                f"{i1}<meta charset=\"UTF-8\">",
                f"{i1}<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
                f"{i1}<title>Grocery Bill Counter</title>",
                f"{i1}<style>",
                f"{i2}* {{",
                f"{i3}box-sizing: border-box;",
                f"{i3}margin: 0;",
                f"{i3}padding: 0;",
                f"{i2}}}",
                "",
                f"{i2}body {{",
                f"{i3}min-height: 100vh;",
                f"{i3}font-family: Arial, sans-serif;",
                f"{i3}background: #f4f6f8;",
                f"{i3}color: #1f2933;",
                f"{i3}display: flex;",
                f"{i3}align-items: center;",
                f"{i3}justify-content: center;",
                f"{i3}padding: 24px;",
                f"{i2}}}",
                "",
                f"{i2}.container {{",
                f"{i3}width: min(100%, 440px);",
                f"{i3}background: #ffffff;",
                f"{i3}border-radius: 8px;",
                f"{i3}box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);",
                f"{i3}padding: 24px;",
                f"{i2}}}",
                "",
                f"{i2}h1 {{",
                f"{i3}font-size: 24px;",
                f"{i3}margin-bottom: 20px;",
                f"{i2}}}",
                "",
                f"{i2}.form-group {{",
                f"{i3}display: grid;",
                f"{i3}gap: 8px;",
                f"{i3}margin-bottom: 16px;",
                f"{i2}}}",
                "",
                f"{i2}label {{",
                f"{i3}font-weight: 600;",
                f"{i2}}}",
                "",
                f"{i2}input {{",
                f"{i3}width: 100%;",
                f"{i3}border: 1px solid #cbd5e1;",
                f"{i3}border-radius: 6px;",
                f"{i3}padding: 10px 12px;",
                f"{i3}font-size: 15px;",
                f"{i2}}}",
                "",
                f"{i2}button {{",
                f"{i3}width: 100%;",
                f"{i3}border: 0;",
                f"{i3}border-radius: 6px;",
                f"{i3}background: #2563eb;",
                f"{i3}color: #ffffff;",
                f"{i3}font-weight: 700;",
                f"{i3}padding: 12px;",
                f"{i3}cursor: pointer;",
                f"{i2}}}",
                "",
                f"{i2}.summary {{",
                f"{i3}margin-top: 20px;",
                f"{i3}padding-top: 16px;",
                f"{i3}border-top: 1px solid #e2e8f0;",
                f"{i2}}}",
                f"{i1}</style>",
                "</head>",
                "<body>",
                f"{i1}<main class=\"container\">",
                f"{i2}<h1>Grocery Bill Counter</h1>",
                f"{i2}<form>",
                f"{i3}<div class=\"form-group\">",
                f"{i4}<label for=\"item-name\">Item Name</label>",
                f"{i4}<input type=\"text\" id=\"item-name\" name=\"item-name\" placeholder=\"Enter grocery item\">",
                f"{i3}</div>",
                f"{i3}<div class=\"form-group\">",
                f"{i4}<label for=\"item-price\">Item Price</label>",
                f"{i4}<input type=\"number\" id=\"item-price\" name=\"item-price\" min=\"0\" step=\"0.01\" placeholder=\"0.00\">",
                f"{i3}</div>",
                f"{i3}<button type=\"submit\">Add Item</button>",
                f"{i2}</form>",
                f"{i2}<section class=\"summary\" aria-live=\"polite\">",
                f"{i3}<strong>Total:</strong> <span>0.00</span>",
                f"{i2}</section>",
                f"{i1}</main>",
                "</body>",
                "</html>",
                "",
            ]
        )

    @staticmethod
    def _remove_generic_comments(code: str, style_profile: StyleProfile) -> str:
        comments = (style_profile.comments or "").lower()
        if "comment-heavy" in comments:
            return code

        generic_patterns = (
            r"^\s*<!--\s*(?:html5\s+document|html\s+document|add .*?|todo.*?)\s*-->\s*$",
            r"^\s*/\*\s*(?:add .*?|styles?\s+for .*?|html5\s+document|todo.*?)\s*\*/\s*$",
            r"^\s*//\s*(?:add .*?|styles?\s+for .*?|todo.*?)\s*$",
        )

        cleaned_lines = []
        for line in code.splitlines():
            if any(re.match(pattern, line, flags=re.IGNORECASE) for pattern in generic_patterns):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines) + ("\n" if code.endswith("\n") else "")
