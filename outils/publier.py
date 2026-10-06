#!/usr/bin/env python3
"""Copie les fichiers publiables du dossier de travail vers le clone git du dépôt.

Ne part sur GitHub que ce qui est sur la liste blanche :
- les fiches .html (mêmes règles que generer_catalogue.py) et les fichiers locaux qu'elles utilisent ;
- index.html, catalogue.js, les scripts et le modèle du dossier outils/ ;
- LICENSE, README.md, CLAUDE.md, .gitignore, .nojekyll.
Jamais : PDF, DOCX, ODT, photos ou scans des fiches originales, desktop.ini, dossiers _sources/ et .claude/.

Le script régénère d'abord catalogue.js (mode --strict) et s'arrête s'il y a des avertissements.
Il ne supprime rien dans le clone : il liste les fichiers qui n'y ont plus leur place.

Utilisation :
    py outils/publier.py               # régénère le catalogue, puis copie
    py outils/publier.py --essai       # affiche ce qui serait copié, sans rien écrire
    py outils/publier.py --depot DOSSIER
Ensuite, dans le clone : git add -A, git commit, git push.
"""

import argparse
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

RACINE = Path(__file__).resolve().parent.parent
DEPOT_PAR_DEFAUT = Path.home() / "Documents" / "GitHub" / "exercices-scolaires"

FICHIERS_DU_SITE = ["index.html", "catalogue.js", "LICENSE", "README.md", "CLAUDE.md", ".gitignore", ".nojekyll"]
OUTILS = ["outils/generer_catalogue.py", "outils/publier.py", "outils/modele-fiche.html"]
EXTENSIONS_INTERDITES = {".pdf", ".doc", ".docx", ".odt", ".ods", ".odp", ".xls", ".xlsx", ".ppt", ".pptx", ".rtf"}
DOSSIERS_EXCLUS = {"outils", "node_modules"}
TEXTE = {".html", ".htm", ".js", ".css", ".md", ".py", ".txt", ".svg", ".json", ""}


class LecteurLiens(HTMLParser):
    """Relève les adresses locales utilisées par une page (images, scripts, feuilles de style, liens)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.adresses = []

    def handle_starttag(self, tag, attrs):
        for nom, valeur in attrs:
            if not valeur:
                continue
            if nom in ("src", "href", "poster", "data"):
                self.adresses.append(valeur)
            elif nom == "srcset":
                self.adresses += [morceau.split()[0] for morceau in valeur.split(",") if morceau.strip()]


def fiches():
    """Les fiches publiées, comme dans generer_catalogue.py."""
    for chemin in sorted(RACINE.rglob("*.html")):
        relatif = chemin.relative_to(RACINE)
        if any(d.startswith((".", "_")) or d in DOSSIERS_EXCLUS for d in relatif.parts[:-1]):
            continue
        if chemin.suffix == ".html" and relatif.as_posix() != "index.html":
            yield chemin


def ressources(page, avert):
    """Fichiers locaux référencés par une page, à l'intérieur du dossier de travail."""
    texte = page.read_text(encoding="utf-8", errors="replace")
    lecteur = LecteurLiens()
    lecteur.feed(texte)
    adresses = lecteur.adresses + re.findall(r"url\(\s*['\"]?([^'\")]+)", texte)
    for adresse in adresses:
        morceaux = urlsplit(adresse.strip())
        if morceaux.scheme or morceaux.netloc or not morceaux.path or adresse.startswith(("#", "data:", "mailto:")):
            continue
        cible = (page.parent / unquote(morceaux.path)).resolve()
        if not cible.is_file():
            continue
        try:
            relatif = cible.relative_to(RACINE)
        except ValueError:
            avert(f"{page.relative_to(RACINE).as_posix()} utilise « {adresse} », hors du dossier du site : non copié")
            continue
        if cible.suffix.lower() in EXTENSIONS_INTERDITES or any(d.startswith((".", "_")) for d in relatif.parts[:-1]):
            avert(f"{page.relative_to(RACINE).as_posix()} utilise « {adresse} », qui ne doit pas être publié : non copié")
            continue
        yield cible


def contenu(chemin):
    """Contenu comparable : fins de ligne unifiées pour les fichiers texte (git les convertit sous Windows)."""
    octets = chemin.read_bytes()
    return octets.replace(b"\r\n", b"\n") if chemin.suffix.lower() in TEXTE else octets


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--depot", type=Path, default=DEPOT_PAR_DEFAUT, help=f"clone git (défaut : {DEPOT_PAR_DEFAUT})")
    parser.add_argument("--essai", action="store_true", help="ne rien écrire, seulement afficher")
    args = parser.parse_args()
    if sys.stdout.isatty():
        sys.stdout.reconfigure(errors="replace")  # consoles Windows sans UTF-8
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # sortie redirigée : toujours en UTF-8

    depot = args.depot.resolve()
    if not (depot / ".git").is_dir():
        sys.exit(f"Pas de clone git dans {depot}. Cloner d'abord https://github.com/ctalpaert/exercices-scolaires.")

    generateur = subprocess.run([sys.executable, str(RACINE / "outils" / "generer_catalogue.py"), "--strict"])
    if generateur.returncode != 0:
        sys.exit("Catalogue avec avertissements : corriger les fiches avant de publier.")

    avertissements = []
    a_publier = {RACINE / nom for nom in FICHIERS_DU_SITE + OUTILS}
    for page in fiches():
        a_publier.add(page)
        a_publier.update(ressources(page, avertissements.append))
    manquants = sorted(p.relative_to(RACINE).as_posix() for p in a_publier if not p.is_file())
    if manquants:
        sys.exit("Fichiers attendus introuvables : " + ", ".join(manquants))

    copies = []
    for source in sorted(a_publier):
        relatif = source.relative_to(RACINE)
        cible = depot / relatif
        if cible.is_file() and contenu(cible) == contenu(source):
            continue
        copies.append(relatif.as_posix())
        if not args.essai:
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(source.read_bytes())

    publies = {p.relative_to(RACINE).as_posix() for p in a_publier}
    en_trop = sorted(
        f.relative_to(depot).as_posix() for f in depot.rglob("*")
        if f.is_file() and ".git" not in f.relative_to(depot).parts[:1] and f.relative_to(depot).as_posix() not in publies
    )

    for message in avertissements:
        print(f"  ! {message}")
    verbe = "à copier" if args.essai else "copiés"
    print(f"{len(copies)} fichier(s) {verbe} vers {depot} :" if copies else f"Rien à copier : {depot} est à jour.")
    for nom in copies:
        print(f"  + {nom}")
    if en_trop:
        print("Présents dans le dépôt mais plus publiés (à retirer avec « git rm » si c'est voulu) :")
        for nom in en_trop:
            print(f"  - {nom}")


if __name__ == "__main__":
    main()
