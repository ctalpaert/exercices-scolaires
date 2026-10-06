#!/usr/bin/env python3
"""Build catalog.js: the list of worksheets shown by index.html.

The script walks the site folder, reads the <title> and <meta> tags of every
HTML page (see CLAUDE.md, "Métadonnées d'une fiche") and writes catalog.js
at the root. It only depends on the standard library.

Usage (from any folder):
    py tools/build_catalog.py            # rebuild catalog.js
    py tools/build_catalog.py --strict   # exit code 1 if there are warnings
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "catalog.js"

# Pages and folders that are not worksheets
EXCLUDED_FILES = {"index.html"}
EXCLUDED_DIRS = {"tools", "node_modules"}

# School levels in French-speaking Switzerland, in order. Keep in sync with CYCLES in index.html (LEVELS there is built from it).
LEVELS = ["1P", "2P", "3P", "4P", "5P", "6P", "7P", "8P", "9S", "10S", "11S", "SEC2", "UNI"]

# Known subjects, as written in the pages. Keep in sync with SUBJECTS in index.html.
SUBJECTS = {
    "Français", "Allemand", "Anglais", "Italien", "Latin", "Grec",
    "Mathématiques", "Sciences de la nature", "Physique", "Chimie", "Biologie",
    "Géographie", "Histoire", "Citoyenneté", "Éthique et cultures religieuses",
    "Philosophie", "Économie et droit",
    "Arts visuels", "Activités créatrices et manuelles", "Musique",
    "Éducation physique", "Éducation numérique", "Informatique",
}

VALID_FILENAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.html$")
TEMPLATE_PLACEHOLDER = re.compile(r"\[[^\]]+\]")   # "[Titre de la fiche]" left from the template

# Saved work (see CLAUDE.md, "Exercices enregistrés"): storage-key prefix and preview guard
# of the localStorage script that every worksheet with answer fields carries
SAVED_WORK_MARKER = "exercices-scolaires:"
PREVIEW_MARKER = "#preview"


class WorksheetReader(HTMLParser):
    """Collects the title, the <meta> tags, the known buttons and the number of A4 sheets."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.metas = {}
        self.ids = set()
        self.sheets = 0
        self.back_link = None   # href of the "← Tous les exercices" link
        self._in_title = False
        self._in_head = True

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "title" and self._in_head:
            self._in_title = True
        elif tag == "meta" and a.get("name"):
            self.metas[a["name"].strip().lower()] = a.get("content", "").strip()
        elif tag == "body":
            self._in_head = False
        if a.get("id"):
            self.ids.add(a["id"])
        classes = a.get("class", "").split()
        if "page" in classes:
            self.sheets += 1
        if tag == "a" and "back-link" in classes and self.back_link is None:
            self.back_link = a.get("href", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            self._in_head = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse_levels(value, warn):
    """Turn "4P", "3P-4P" or "7P, 8P" into an ordered list of known codes."""
    found = set()
    for part in re.split(r"[,;]", value):
        part = part.strip().upper().replace("–", "-")
        if not part:
            continue
        if "-" in part:
            start, _, end = (p.strip() for p in part.partition("-"))
            if start in LEVELS and end in LEVELS and LEVELS.index(start) <= LEVELS.index(end):
                found.update(LEVELS[LEVELS.index(start):LEVELS.index(end) + 1])
            else:
                warn(f'unknown level range "{part}"')
        elif part in LEVELS:
            found.add(part)
        else:
            warn(f'unknown level "{part}" (expected: {", ".join(LEVELS)})')
    return [level for level in LEVELS if level in found]


def read_worksheet(path, warn):
    relative = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        warn("file is not UTF-8; unreadable characters replaced")
        text = path.read_text(encoding="utf-8", errors="replace")
    text = unicodedata.normalize("NFC", text)   # precomposed or decomposed "é": same subject

    reader = WorksheetReader()
    reader.feed(text)
    m = reader.metas

    title = re.sub(r"\s+", " ", reader.title).strip()
    if not title:
        warn("no <title>")
        title = path.stem.replace("-", " ").capitalize()

    description = m.get("description", "")
    if not description:
        warn('no <meta name="description">')

    subject = m.get("worksheet:subject", "")
    if not subject:
        warn('no <meta name="worksheet:subject">')
    elif subject not in SUBJECTS:
        warn(f'unknown subject "{subject}" (add it to SUBJECTS here and to SUBJECTS in index.html)')

    levels = parse_levels(m.get("worksheet:level", ""), warn)
    if not levels:
        warn('no valid <meta name="worksheet:level">')

    added = m.get("worksheet:added", "")
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", added):
            raise ValueError
        if date.fromisoformat(added) > date.today():
            warn(f'date added is in the future "{added}"')
    except ValueError:
        warn(f'<meta name="worksheet:added"> missing or invalid "{added}" (format YYYY-MM-DD)')
        added = ""

    keywords = [k.strip() for k in m.get("keywords", "").split(",") if k.strip()]

    if not VALID_FILENAME.match(path.name):
        warn("file name to avoid: lowercase letters, digits and hyphens only, no accents or spaces")

    if reader.sheets == 0:
        warn('no class="page" element (A4 sheet) found')

    expected = "../" * (len(path.relative_to(ROOT).parts) - 1) + "index.html"
    if reader.back_link is None:
        warn(f'no <a class="back-link" href="{expected}"> link')
    elif reader.back_link != expected:
        warn(f'the .back-link link points to "{reader.back_link}" instead of "{expected}"')

    for name, value in [("title", title), ("description", description), ("keywords", ", ".join(keywords)),
                        ("subject", subject), ("level", m.get("worksheet:level", ""))]:
        if TEMPLATE_PLACEHOLDER.search(value):
            warn(f'{name}: template text not replaced "{TEMPLATE_PLACEHOLDER.search(value).group()}"')
    for name, value in [("title", title), ("description", description)]:
        if "'" in value:
            warn(f"{name}: replace the straight apostrophe ' with the typographic apostrophe ’")

    # Answer fields made by JavaScript (answerInput()) are invisible to the parser: search the raw text
    if "answer-input" in text:
        missing = []
        if SAVED_WORK_MARKER not in text:
            missing.append(f'the saved-work script (storage key "{SAVED_WORK_MARKER}…")')
        if PREVIEW_MARKER not in text:
            missing.append(f'the read-only "{PREVIEW_MARKER}" guard')
        if "btn-clear" not in reader.ids:
            missing.append('a static button with id="btn-clear"')
        if missing:
            warn("answer fields (.answer-input) without " + ", ".join(missing) + " (see CLAUDE.md)")

    return {
        "file": relative,
        "title": title,
        "description": description,
        "subject": subject,
        "levels": levels,
        "keywords": keywords,
        "added": added,
        "pages": max(reader.sheets, 1),
        "answer_key": "btn-answers" in reader.ids,
        "randomized": "btn-new" in reader.ids,
    }


def find_worksheets():
    """All .html/.htm pages (any case) outside excluded folders. PDF, DOCX, ODT… files are ignored."""
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".html", ".htm"):
            continue
        relative = path.relative_to(ROOT)
        folders = relative.parts[:-1]
        if any(d.startswith((".", "_")) or d in EXCLUDED_DIRS for d in folders):
            continue
        if len(relative.parts) == 1 and relative.name in EXCLUDED_FILES:
            continue
        yield path


def comparable(text):
    """Sort key: no accents or apostrophes ("L’arbre" sorts like "Larbre")."""
    no_accents = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    return re.sub(r"['’]", "", no_accents).casefold()


def sort_key(sheet):
    first = LEVELS.index(sheet["levels"][0]) if sheet["levels"] else len(LEVELS)
    return (first, comparable(sheet["subject"]), comparable(sheet["title"]), sheet["file"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="fail if there are warnings")
    args = parser.parse_args()
    if sys.stdout.isatty():
        sys.stdout.reconfigure(errors="replace")  # Windows consoles without UTF-8
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # redirected output: always UTF-8

    sheets, warning_count = [], 0
    for path in find_worksheets():
        relative = path.relative_to(ROOT).as_posix()

        def warn(message, relative=relative):
            nonlocal warning_count
            warning_count += 1
            print(f"  ! {relative}: {message}")

        if path.suffix != ".html":
            warn("skipped: rename the file with a lowercase .html extension")
            continue
        sheets.append(read_worksheet(path, warn))

    sheets.sort(key=sort_key)
    content = (
        "// Generated by tools/build_catalog.py: do not edit by hand.\n"
        "// To add a worksheet, fill in its <meta> tags and run the script again (see CLAUDE.md).\n"
        "window.CATALOG = "
        + json.dumps(sheets, ensure_ascii=False, indent=2)
        + ";\n"
    )

    previous = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    if content != previous:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
        status = "updated"
    else:
        status = "already up to date"

    print(f"catalog.js {status}: {len(sheets)} worksheet(s), {warning_count} warning(s).")
    for s in sheets:
        print(f"  - {'/'.join(s['levels']) or '?':<6} {s['subject'] or '?':<24} {s['file']}")
    if args.strict and warning_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
