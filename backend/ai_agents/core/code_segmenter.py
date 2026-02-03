import re

class CodeSegmenter:
    def segment(self, code: str):
        lines = code.splitlines()

        segments = {
            "html": [],
            "css": [],
            "javascript": []
        }

        current = "html"
        start_lines = {
            "html": [],
            "css": [],
            "javascript": []
        }

        for idx, line in enumerate(lines, start=1):
            line_lower = line.lower()

            if "<style" in line_lower:
                current = "css"
                start_lines["css"].append(idx)
                continue
            if "</style>" in line_lower:
                current = "html"
                continue

            if "<script" in line_lower:
                current = "javascript"
                start_lines["javascript"].append(idx)
                continue
            if "</script>" in line_lower:
                current = "html"
                continue

            segments[current].append(line)

        return segments, start_lines
