#!/usr/bin/env python3
"""Génère catalogue.js : la liste des fiches d'exercices affichée par index.html.

Le script parcourt le dossier du site, lit les balises <title> et <meta> de
chaque page HTML (voir CLAUDE.md, « Métadonnées d'une fiche ») et écrit
catalogue.js à la racine. Il ne dépend que de la bibliothèque standard.

Utilisation (depuis n'importe quel dossier) :
    py outils/generer_catalogue.py            # régénère catalogue.js
    py outils/generer_catalogue.py --strict   # code de sortie 1 s'il y a des avertissements
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "catalogue.js"

# Pages et dossiers qui ne sont pas des fiches d'exercices
FICHIERS_EXCLUS = {"index.html"}
DOSSIERS_EXCLUS = {"outils", "node_modules"}

# Degrés scolaires de Suisse romande, dans l'ordre. Garder synchronisé avec NIVEAUX dans index.html.
NIVEAUX = ["1P", "2P", "3P", "4P", "5P", "6P", "7P", "8P", "9S", "10S", "11S", "SEC2", "UNI"]

# Matières connues. Garder synchronisé avec MATIERES dans index.html.
MATIERES = {
    "Français", "Allemand", "Anglais", "Italien", "Latin", "Grec",
    "Mathématiques", "Sciences de la nature", "Physique", "Chimie", "Biologie",
    "Géographie", "Histoire", "Citoyenneté", "Éthique et cultures religieuses",
    "Philosophie", "Économie et droit",
    "Arts visuels", "Activités créatrices et manuelles", "Musique",
    "Éducation physique", "Éducation numérique", "Informatique",
}

NOM_FICHIER_OK = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.html$")
TEXTE_DU_MODELE = re.compile(r"\[[^\]]+\]")   # « [Titre de la fiche] » oublié


class LecteurFiche(HTMLParser):
    """Relève le titre, les <meta>, les boutons connus et le nombre de feuilles A4."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titre = ""
        self.metas = {}
        self.ids = set()
        self.feuilles = 0
        self.retour = None   # href du lien « ← Tous les exercices »
        self._dans_titre = False
        self._dans_head = True

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "title" and self._dans_head:
            self._dans_titre = True
        elif tag == "meta" and a.get("name"):
            self.metas[a["name"].strip().lower()] = a.get("content", "").strip()
        elif tag == "body":
            self._dans_head = False
        if a.get("id"):
            self.ids.add(a["id"])
        classes = a.get("class", "").split()
        if "page" in classes:
            self.feuilles += 1
        if tag == "a" and "retour" in classes and self.retour is None:
            self.retour = a.get("href", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self._dans_titre = False
        elif tag == "head":
            self._dans_head = False

    def handle_data(self, data):
        if self._dans_titre:
            self.titre += data


def lister_niveaux(valeur, avert):
    """« 4P », « 3P-4P » ou « 7P, 8P » -> liste ordonnée de codes connus."""
    trouves = set()
    for morceau in re.split(r"[,;]", valeur):
        morceau = morceau.strip().upper().replace("–", "-")
        if not morceau:
            continue
        if "-" in morceau:
            debut, _, fin = (m.strip() for m in morceau.partition("-"))
            if debut in NIVEAUX and fin in NIVEAUX and NIVEAUX.index(debut) <= NIVEAUX.index(fin):
                trouves.update(NIVEAUX[NIVEAUX.index(debut):NIVEAUX.index(fin) + 1])
            else:
                avert(f"plage de niveaux inconnue « {morceau} »")
        elif morceau in NIVEAUX:
            trouves.add(morceau)
        else:
            avert(f"niveau inconnu « {morceau} » (attendus : {', '.join(NIVEAUX)})")
    return [n for n in NIVEAUX if n in trouves]


def lire_fiche(chemin, avert):
    relatif = chemin.relative_to(RACINE).as_posix()
    try:
        texte = chemin.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        avert("le fichier n'est pas en UTF-8 ; caractères illisibles remplacés")
        texte = chemin.read_text(encoding="utf-8", errors="replace")
    texte = unicodedata.normalize("NFC", texte)   # « é » composé ou décomposé : même matière

    lecteur = LecteurFiche()
    lecteur.feed(texte)
    m = lecteur.metas

    titre = re.sub(r"\s+", " ", lecteur.titre).strip()
    if not titre:
        avert("pas de <title>")
        titre = chemin.stem.replace("-", " ").capitalize()

    description = m.get("description", "")
    if not description:
        avert('pas de <meta name="description">')

    matiere = m.get("exercice:matiere", "")
    if not matiere:
        avert('pas de <meta name="exercice:matiere">')
    elif matiere not in MATIERES:
        avert(f"matière inconnue « {matiere} » (ajoutez-la à MATIERES ici et dans index.html)")

    niveaux = lister_niveaux(m.get("exercice:niveau", ""), avert)
    if not niveaux:
        avert('pas de <meta name="exercice:niveau"> valide')

    ajout = m.get("exercice:ajout", "")
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ajout):
            raise ValueError
        if date.fromisoformat(ajout) > date.today():
            avert(f"date d'ajout dans le futur « {ajout} »")
    except ValueError:
        avert(f'<meta name="exercice:ajout"> absent ou invalide « {ajout} » (format AAAA-MM-JJ)')
        ajout = ""

    mots_cles = [k.strip() for k in m.get("keywords", "").split(",") if k.strip()]

    if not NOM_FICHIER_OK.match(chemin.name):
        avert("nom de fichier à éviter : minuscules, chiffres et tirets uniquement, sans accent ni espace")

    if lecteur.feuilles == 0:
        avert('aucun élément class="page" (feuille A4) trouvé')

    attendu = "../" * (len(chemin.relative_to(RACINE).parts) - 1) + "index.html"
    if lecteur.retour is None:
        avert(f'pas de lien <a class="retour" href="{attendu}">')
    elif lecteur.retour != attendu:
        avert(f"le lien .retour pointe vers « {lecteur.retour} » au lieu de « {attendu} »")

    for nom, valeur in [("titre", titre), ("description", description), ("mots-clés", ", ".join(mots_cles)),
                        ("matière", matiere), ("niveau", m.get("exercice:niveau", ""))]:
        if TEXTE_DU_MODELE.search(valeur):
            avert(f"{nom} : texte du modèle non remplacé « {TEXTE_DU_MODELE.search(valeur).group()} »")
    for nom, valeur in [("titre", titre), ("description", description)]:
        if "'" in valeur:
            avert(f"{nom} : apostrophe droite ' à remplacer par l'apostrophe typographique ’")

    return {
        "fichier": relatif,
        "titre": titre,
        "description": description,
        "matiere": matiere,
        "niveaux": niveaux,
        "mots_cles": mots_cles,
        "ajout": ajout,
        "pages": max(lecteur.feuilles, 1),
        "corrige": "btn-corrige" in lecteur.ids,
        "aleatoire": "btn-new" in lecteur.ids,
    }


def trouver_fiches():
    """Toutes les pages .html/.htm (toutes casses) hors des dossiers exclus. Les PDF, DOCX, ODT… sont ignorés."""
    for chemin in sorted(RACINE.rglob("*")):
        if not chemin.is_file() or chemin.suffix.lower() not in (".html", ".htm"):
            continue
        relatif = chemin.relative_to(RACINE)
        dossiers = relatif.parts[:-1]
        if any(d.startswith((".", "_")) or d in DOSSIERS_EXCLUS for d in dossiers):
            continue
        if len(relatif.parts) == 1 and relatif.name in FICHIERS_EXCLUS:
            continue
        yield chemin


def comparable(texte):
    """Clé de tri : sans accents ni apostrophes (« L’arbre » se range comme « Larbre »)."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c))
    return re.sub(r"['’]", "", sans_accents).casefold()


def cle_tri(fiche):
    premier = NIVEAUX.index(fiche["niveaux"][0]) if fiche["niveaux"] else len(NIVEAUX)
    return (premier, comparable(fiche["matiere"]), comparable(fiche["titre"]), fiche["fichier"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="échouer s'il y a des avertissements")
    args = parser.parse_args()
    if sys.stdout.isatty():
        sys.stdout.reconfigure(errors="replace")  # consoles Windows sans UTF-8
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # sortie redirigée : toujours en UTF-8

    fiches, nb_avert = [], 0
    for chemin in trouver_fiches():
        relatif = chemin.relative_to(RACINE).as_posix()

        def avert(message, relatif=relatif):
            nonlocal nb_avert
            nb_avert += 1
            print(f"  ! {relatif} : {message}")

        if chemin.suffix != ".html":
            avert("ignoré : renommer le fichier avec l'extension .html en minuscules")
            continue
        fiches.append(lire_fiche(chemin, avert))

    fiches.sort(key=cle_tri)
    contenu = (
        "// Fichier généré par outils/generer_catalogue.py : ne pas modifier à la main.\n"
        "// Pour ajouter une fiche, renseigner ses <meta> puis relancer le script (voir CLAUDE.md).\n"
        "window.CATALOGUE = "
        + json.dumps(fiches, ensure_ascii=False, indent=2)
        + ";\n"
    )

    ancien = SORTIE.read_text(encoding="utf-8") if SORTIE.exists() else None
    if contenu != ancien:
        SORTIE.write_text(contenu, encoding="utf-8", newline="\n")
        etat = "mis à jour"
    else:
        etat = "déjà à jour"

    print(f"catalogue.js {etat} : {len(fiches)} fiche(s), {nb_avert} avertissement(s).")
    for f in fiches:
        print(f"  - {'/'.join(f['niveaux']) or '?':<6} {f['matiere'] or '?':<24} {f['fichier']}")
    if args.strict and nb_avert:
        sys.exit(1)


if __name__ == "__main__":
    main()
