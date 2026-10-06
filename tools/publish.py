#!/usr/bin/env python3
"""Copy the publishable files from the working folder to the git clone of the repository.

Only what is on the allow list goes to GitHub:
- the .html worksheets (same rules as build_catalog.py) and the local files they use;
- index.html, catalog.js, the scripts and the template of the tools/ folder;
- LICENSE, README.md, CLAUDE.md, .gitignore, .nojekyll.
Never: PDF, DOCX, ODT, photos or scans of the original worksheets, desktop.ini, _sources/ and .claude/ folders.

The script first rebuilds catalog.js (--strict mode) and stops if there are warnings.
It deletes nothing in the clone: it lists the files that no longer belong there.

Usage:
    py tools/publish.py                # rebuild the catalog, then copy
    py tools/publish.py --dry-run      # show what would be copied, without writing anything
    py tools/publish.py --repo FOLDER
Then, in the clone: git add -A, git commit, git push.
"""

import argparse
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "exercices-scolaires"

SITE_FILES = ["index.html", "catalog.js", "LICENSE", "README.md", "CLAUDE.md", ".gitignore", ".nojekyll"]
TOOLS = ["tools/build_catalog.py", "tools/publish.py", "tools/modele-fiche.html"]
FORBIDDEN_EXTENSIONS = {".pdf", ".doc", ".docx", ".odt", ".ods", ".odp", ".xls", ".xlsx", ".ppt", ".pptx", ".rtf"}
EXCLUDED_DIRS = {"tools", "node_modules"}
TEXT_EXTENSIONS = {".html", ".htm", ".js", ".css", ".md", ".py", ".txt", ".svg", ".json", ""}


class LinkReader(HTMLParser):
    """Collects the local addresses used by a page (images, scripts, stylesheets, links)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.addresses = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if not value:
                continue
            if name in ("src", "href", "poster", "data"):
                self.addresses.append(value)
            elif name == "srcset":
                self.addresses += [part.split()[0] for part in value.split(",") if part.strip()]


def worksheets():
    """The published worksheets, as in build_catalog.py."""
    for path in sorted(ROOT.rglob("*.html")):
        relative = path.relative_to(ROOT)
        if any(d.startswith((".", "_")) or d in EXCLUDED_DIRS for d in relative.parts[:-1]):
            continue
        if path.suffix == ".html" and relative.as_posix() != "index.html":
            yield path


def resources(page, warn):
    """Local files referenced by a page, inside the working folder."""
    text = page.read_text(encoding="utf-8", errors="replace")
    reader = LinkReader()
    reader.feed(text)
    addresses = reader.addresses + re.findall(r"url\(\s*['\"]?([^'\")]+)", text)
    for address in addresses:
        parts = urlsplit(address.strip())
        if parts.scheme or parts.netloc or not parts.path or address.startswith(("#", "data:", "mailto:")):
            continue
        target = (page.parent / unquote(parts.path)).resolve()
        if not target.is_file():
            continue
        try:
            relative = target.relative_to(ROOT)
        except ValueError:
            warn(f'{page.relative_to(ROOT).as_posix()} uses "{address}", outside the site folder: not copied')
            continue
        if target.suffix.lower() in FORBIDDEN_EXTENSIONS or any(d.startswith((".", "_")) for d in relative.parts[:-1]):
            warn(f'{page.relative_to(ROOT).as_posix()} uses "{address}", which must not be published: not copied')
            continue
        yield target


def comparable_content(path):
    """Content to compare: line endings unified for text files (git converts them on Windows)."""
    data = path.read_bytes()
    return data.replace(b"\r\n", b"\n") if path.suffix.lower() in TEXT_EXTENSIONS else data


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help=f"git clone (default: {DEFAULT_REPO})")
    parser.add_argument("--dry-run", action="store_true", help="write nothing, only show")
    args = parser.parse_args()
    if sys.stdout.isatty():
        sys.stdout.reconfigure(errors="replace")  # Windows consoles without UTF-8
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # redirected output: always UTF-8

    repo = args.repo.resolve()
    if not (repo / ".git").is_dir():
        sys.exit(f"No git clone in {repo}. First clone https://github.com/ctalpaert/exercices-scolaires.")

    builder = subprocess.run([sys.executable, str(ROOT / "tools" / "build_catalog.py"), "--strict"])
    if builder.returncode != 0:
        sys.exit("Catalog has warnings: fix the worksheets before publishing.")

    warnings = []
    to_publish = {ROOT / name for name in SITE_FILES + TOOLS}
    for page in worksheets():
        to_publish.add(page)
        to_publish.update(resources(page, warnings.append))
    missing = sorted(p.relative_to(ROOT).as_posix() for p in to_publish if not p.is_file())
    if missing:
        sys.exit("Expected files not found: " + ", ".join(missing))

    copied = []
    for source in sorted(to_publish):
        relative = source.relative_to(ROOT)
        target = repo / relative
        if target.is_file() and comparable_content(target) == comparable_content(source):
            continue
        copied.append(relative.as_posix())
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    published = {p.relative_to(ROOT).as_posix() for p in to_publish}
    extra = sorted(
        f.relative_to(repo).as_posix() for f in repo.rglob("*")
        if f.is_file() and ".git" not in f.relative_to(repo).parts[:1] and f.relative_to(repo).as_posix() not in published
    )

    for message in warnings:
        print(f"  ! {message}")
    verb = "to copy" if args.dry_run else "copied"
    print(f"{len(copied)} file(s) {verb} to {repo}:" if copied else f"Nothing to copy: {repo} is up to date.")
    for name in copied:
        print(f"  + {name}")
    if extra:
        print('In the repository but no longer published (remove them with "git rm" if intended):')
        for name in extra:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
