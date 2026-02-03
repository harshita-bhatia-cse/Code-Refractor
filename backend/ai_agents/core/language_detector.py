import os
import re


EXTENSION_MAP = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".cs": "csharp",
    ".php": "php",
    ".rs": "rust",
    ".html": "html",
    ".css": "css",
}


def detect_language(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    return EXTENSION_MAP.get(ext, "unknown")


def detect_language_from_code(code: str) -> str:
    c = code.lower()

    # ---------- HTML ----------
    if "<!doctype html" in c or "<html" in c:
        return "html"

    # ---------- Python ----------
    if re.search(r"\bdef\s+\w+", c) or re.search(r"\bimport\s+\w+", c):
        return "python"

    # ---------- Java (VERY IMPORTANT ORDER) ----------
    if (
        "public class" in c
        or "class solution" in c
        or "math." in c
        or "arraylist" in c
        or "hashmap" in c
        or re.search(r"\bint\s+\w+\s*\(", c)
    ):
        return "java"

    # ---------- JavaScript ----------
    if (
        "console.log" in c
        or "document.getelementbyid" in c
        or re.search(r"\bfunction\s+\w+", c)
        or "=>" in c
    ):
        return "javascript"

    # ---------- Go ----------
    if "package main" in c or "fmt.println" in c:
        return "go"

    # ---------- C++ ----------
    if "#include" in c and "std::" in c:
        return "cpp"

    # ---------- C ----------
    if "#include" in c:
        return "c"

    # ---------- LAST RESORT: generic C-like ----------
    if re.search(r"\bfor\s*\(.*\)", c) and "{" in c and "}" in c:
        return "c"

    return "unknown"
