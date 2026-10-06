# Exercices scolaires : conventions du projet

Fiches d'exercices à imprimer (A4), écrites en HTML, publiées sur GitHub Pages.
Ce fichier sert de référence pour créer de nouvelles fiches et maintenir `index.html` de façon cohérente.

- Dépôt : <https://github.com/ctalpaert/exercices-scolaires> (branche `main`, public)
- Site : <https://ctalpaert.github.io/exercices-scolaires/>
- Publication : GitHub Pages servi directement depuis la racine de `main`. Pas d'étape de compilation, pas de GitHub Action.
- Public visé : élèves de Suisse romande (degrés 1P à 11S, secondaire II, université), leurs parents et enseignants. Les fiches actuelles sont en 4P.
- **Deux dossiers** : le dossier de travail sur Google Drive (sans git : fiches, documents de travail, photos des fiches reçues) et le clone git `%USERPROFILE%\Documents\GitHub\exercices-scolaires`, qui ne reçoit que les fichiers publiables via `outils/publier.py`. On travaille toujours dans le dossier Drive ; on ne modifie jamais directement le clone.
- Ce fichier est publié avec le dépôt : n'y écrire aucune donnée personnelle (prénom de l'enfant, chemins locaux complets, adresse e-mail). Ne pas ajouter de données personnelles dans les fiches sans l'accord de l'utilisateur.

## Fichiers

| Fichier | Rôle |
|---|---|
| `index.html` | Page d'accueil : liste des fiches, filtres, recherche, téléchargement zip avec acceptation de la licence. Ne pas y écrire la liste des fiches à la main. |
| `catalogue.js` | **Généré** par `outils/generer_catalogue.py`. Jamais modifié à la main. |
| `outils/generer_catalogue.py` | Lit les `<meta>` de chaque page HTML, vérifie les conventions et écrit `catalogue.js`. Python 3, bibliothèque standard uniquement. |
| `outils/publier.py` | Régénère le catalogue (`--strict`) puis copie la liste blanche des fichiers publiables vers le clone git. |
| `outils/modele-fiche.html` | Modèle de départ pour une nouvelle fiche. |
| `*.html` (racine ou sous-dossiers) | Les fiches. Un sous-dossier par thème quand la fiche a plusieurs variantes ou des images (ex. `Arbres/`). |
| `LICENSE` | Texte officiel CC BY-NC-SA 4.0 (anglais). |
| `.nojekyll` | Désactive Jekyll sur GitHub Pages (fichiers servis tels quels). |
| `.gitignore` | Filet de sécurité dans le clone (PDF, DOCX, ODT, photos des fiches originales, `desktop.ini`…). |

Le générateur et `publier.py` ignorent : `index.html` à la racine, le dossier `outils/` (sauf les trois fichiers d'outils publiés), et tout dossier commençant par `.` ou `_`.

**Règles de publication**
- Seules les pages `.html` sont recensées. Les fichiers PDF, DOCX, ODT (et autres documents bureautiques) sont des documents de travail : jamais indexés dans `index.html`, jamais publiés.
- Les photos ou scans des fiches reçues en classe (ex. `Arbres/*.jpg`) appartiennent à leurs auteurs : ne jamais les publier ni les intégrer aux pages. Les nouvelles vont dans un dossier `_sources/`.
- D'une fiche reçue, ne reprendre que l'idée de l'exercice et la notion travaillée : jamais le texte, les illustrations, la mise en page ni le titre exact. Textes et dessins (SVG) sont créés pour nos fiches.
- `publier.py` ne copie que : les fiches, les fichiers locaux qu'elles utilisent (images…), `index.html`, `catalogue.js`, les trois fichiers d'`outils/`, `LICENSE`, `README.md`, `CLAUDE.md`, `.gitignore`, `.nojekyll`. Il ne supprime rien dans le clone : il liste les fichiers en trop, à retirer avec `git rm` si c'est voulu.

## Ajouter une fiche : marche à suivre

1. Copier `outils/modele-fiche.html` vers son emplacement final. Nom de fichier : minuscules, chiffres et tirets, sans accent ni espace, extension `.html` (ex. `les-nombres-jusqu-a-100.html`).
2. Remplacer tout ce qui est entre [crochets] : métadonnées (section suivante), titre, consignes. Adapter le lien `.retour` : `index.html` à la racine, `../index.html` dans un sous-dossier, `../../index.html` deux niveaux plus bas.
3. Écrire les exercices en respectant les conventions de design ci-dessous.
4. Vérifier le catalogue, jusqu'à zéro avertissement :
   ```
   py outils/generer_catalogue.py --strict
   ```
   Il signale : métadonnées manquantes ou invalides, texte du modèle oublié, apostrophe droite dans le titre ou la description, lien `.retour` absent ou de mauvaise profondeur, date future, extension `.htm`, nom de fichier non conforme.
   (Dans le Bash de Claude Code, `python` n'est pas dans le PATH : utiliser `py`, avec `PYTHONIOENCODING=utf-8` si l'affichage des accents est faux.)
5. Ouvrir la fiche dans le navigateur (un serveur local est décrit dans `.claude/launch.json` : `py -m http.server 8765`) : rendu écran, une feuille A4 par `.page` sans débordement (y compris la mention de licence en bas), corrigé, bouton « Nouveaux exercices » s'il existe.
6. Ouvrir `index.html` : la fiche apparaît au bon degré, dans la bonne matière, avec son aperçu ; la recherche la trouve.
7. Publier (section « Publication »).

Modifier une fiche existante : mêmes étapes 4 à 7. Ne pas changer son nom de fichier (les liens partagés casseraient).

## Métadonnées d'une fiche

Dans le `<head>`, juste après `<title>` :

```html
<title>Les triangles</title>
<meta name="description" content="Nommer six triangles (équilatéral, isocèle, rectangle, obtusangle…) en lisant le codage des côtés et des angles.">
<meta name="keywords" content="géométrie, triangle, isocèle, équilatéral, angle droit">
<meta name="exercice:matiere" content="Mathématiques">
<meta name="exercice:niveau" content="4P">
<meta name="exercice:ajout" content="2026-09-30">
<link rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr">
```

| Balise | Contenu |
|---|---|
| `<title>` | Titre court affiché sur la carte. Pas de nom de site. Apostrophe typographique `’`. |
| `description` | Une phrase qui dit ce que fait l'élève (verbes à l'infinitif), environ 160 caractères au plus. Apostrophe `’`, espace insécable (U+00A0) avant `:`. |
| `keywords` | Mots-clés séparés par des virgules ; servent à la recherche (accents, apostrophes et tirets ignorés). |
| `exercice:matiere` | Une seule matière, exactement l'un des noms de la liste ci-dessous. |
| `exercice:niveau` | Un code, une plage (`3P-4P`) ou une liste (`7P, 8P`). Codes ci-dessous. |
| `exercice:ajout` | Date de mise en ligne, `AAAA-MM-JJ`. La fiche porte le ruban « Nouveau » pendant 30 jours. |

Détectés automatiquement (ne rien déclarer) :
- **nombre de feuilles A4** : nombre d'éléments ayant la classe `page` ;
- **corrigé** : présence d'un élément `id="btn-corrige"` ;
- **exercices à volonté** : présence d'un élément `id="btn-new"` (bouton « 🎲 Nouveaux exercices »).

### Codes de degré (Suisse romande)

| Code | Affiché | Groupe dans l'index |
|---|---|---|
| `1P` … `4P` | 1P … 4P | Cycle 1 |
| `5P` … `8P` | 5P … 8P | Cycle 2 |
| `9S`, `10S`, `11S` | 9S … 11S | Cycle 3 |
| `SEC2` | Sec II | Secondaire II (gymnase, ECG, formation professionnelle) |
| `UNI` | Uni | Tertiaire (haute école, université) |

Une fiche sur plusieurs degrés est rangée sous le cycle de son degré le plus bas.

### Matières reconnues

Français, Allemand, Anglais, Italien, Latin, Grec, Mathématiques, Sciences de la nature, Physique, Chimie, Biologie, Géographie, Histoire, Citoyenneté, Éthique et cultures religieuses, Philosophie, Économie et droit, Arts visuels, Activités créatrices et manuelles, Musique, Éducation physique, Éducation numérique, Informatique.

Ajouter une matière ou un degré : modifier **les deux** listes, `MATIERES`/`NIVEAUX` dans `outils/generer_catalogue.py` et `MATIERES`/`CYCLES` dans le script de `index.html` (emoji + teinte de 0 à 360, choisie loin des teintes voisines).

## Conventions de design des fiches

Le modèle `outils/modele-fiche.html` applique tout ceci ; `exercices-alphabet-voyelles.html` et `exercices-phrases-mots.html` sont les fiches de référence.

- **Autonomie** : une fiche = un fichier HTML, CSS et JS en ligne, dessins en SVG en ligne. Seule dépendance externe autorisée : Google Fonts. Pas de bibliothèque JS. Si une image est indispensable, la placer dans le sous-dossier de la fiche, et seulement si elle est libre de droits ou créée par nous.
- **Format A4** : `@page { size: A4 portrait; margin: 0; }`, chaque feuille est un élément `.page` de `210mm × 297mm` avec `overflow: hidden`, ombre et marge à l'écran, supprimées à l'impression (`height: 296mm` à l'impression pour éviter une page blanche). Unités en `mm` et `pt` dans la feuille. Le contenu ne doit jamais déborder d'une feuille. Garder au moins 4 mm de marge intérieure en bas.
- **Mention de licence** : chaque `.page` est en `position: relative` et son `::after` imprime, à 1,2 mm du bas, « Exercices scolaires · ctalpaert.github.io/exercices-scolaires · Licence CC BY-NC-SA 4.0 · pas d’utilisation commerciale » (6,5 pt, gris `#7b8591`). Ne pas utiliser `.page::after` pour autre chose.
- **Écran seulement** : la barre `.toolbar` (fixe en haut à droite : « Imprimer », éventuellement « 🎲 Nouveaux exercices », « Afficher le corrigé ») et le lien `.retour` (fixe en haut à gauche, « ← Tous les exercices », bleu `#1864ab`) sont masqués à l'impression. Garder ces classes et ces `id` : l'index s'en sert pour les aperçus et la détection.
- **Typographie** : Lexend (lisibilité) pour les fiches de lecture/écriture ; Andika + Fredoka pour les fiches illustrées des petits. Texte d'au moins 9 pt, consignes 10 à 12 pt.
- **Couleurs** : encre `#1f2933`, violet `#5146e5` (en-tête), accents par exercice : rose `#d6528c`, vert `#3fa45b`, orange `#ec9a2f` ; réponses du corrigé en rouge `#e03131`. Fond écran `#e9edf1`. Boutons écran bleu `#1c7ed6`.
- **Structure** : en-tête `.head` (titre avec emoji, étoiles ☆☆☆ d'auto-évaluation, « Prénom : » et « Date : » avec ligne pointillée, badge « Corrigé »), puis blocs `.ex` numérotés avec onglet `.tab` (« Exercice 1 », « Défi 🏆 »), consigne `.consigne` commençant par un emoji, pied « Bravo pour ton travail ! 🌟 ».
- **Corrigé** : réponses dans des `.ans` (cachées par `visibility: hidden` pour que la mise en page ne bouge pas), affichées par `body.corrige`. Le bouton porte `aria-pressed`.
- **Saisie au clavier** : chaque zone où l'élève écrit (ligne, case, bulle, étiquette, case à cocher) reçoit un `<input class="saisie" type="text">` transparent, en `position: absolute` sur la zone (qui passe en `position: relative`), pour qu'il puisse s'entraîner à taper sa réponse. Attributs : `aria-label` qui dit ce qu'on écrit, `autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false"` (le correcteur et la majuscule automatique donneraient la réponse), `maxlength` pour une lettre ou un nombre. Texte tapé en bleu `#1864ab`, imprimé avec la fiche, masqué par `body.corrige`. Entrée passe au champ suivant. Pas de champ pour entourer, relier ou colorier. Dans les fiches générées, les champs sont créés avec les questions (fonction `saisie()`), pour qu'un nouveau tirage les vide.
- **Exercices aléatoires** : quand c'est pertinent, une fonction `generate()` tire les questions dans des listes de mots ou de nombres, et le corrigé suit les questions tirées.
- **Langue** : français de Suisse romande. Tutoyer l'élève, phrases courtes, impératif (« Entoure », « Relie », « Écris »). Vocabulaire local : septante, nonante ; pour 80, « quatre-vingts » (ou les deux formes, « quatre-vingts (huitante) », si l'utilisateur le souhaite) ; pive (pomme de pin).
- **Typographie française** : espace insécable avant `: ; ! ?` et à l'intérieur des guillemets « », apostrophe `’`. Dans le HTML, `&nbsp;` ; dans le JS, ` `.
- **Accessibilité** : `lang="fr"`, SVG décoratifs en `aria-hidden="true"`, SVG porteurs de sens avec `role="img"` et `aria-label`, contrastes suffisants même imprimés en noir et blanc.

## index.html

- Lit `window.CATALOGUE` (dans `catalogue.js`) et affiche : frise des degrés (Cycle 1 → Tertiaire), filtres par matière, recherche plein texte, tri (par degré, plus récentes, A → Z). Les filtres sont reflétés dans l'adresse (`?niveau=4P&matiere=Français&q=arbre&tri=recent`) pour pouvoir partager un lien.
- Aperçus : chaque carte charge la fiche dans une `<iframe>` mise à l'échelle (largeur A4 = 794 px), seulement quand la carte approche de l'écran (IntersectionObserver). Sur le même domaine, l'index masque `.toolbar`, `.print-btn`, `.retour` et `.saisie` dans l'aperçu. Les filtres masquent les cartes sans les reconstruire (pas de rechargement des aperçus) ; seul le changement de tri reconstruit la liste.
- Design : papier quadrillé, Fraunces (titres) + Lexend (texte), couleurs en variables CSS dans `:root`, mode sombre via `prefers-color-scheme`, teintes de matière/cycle via `--h` et la classe `.t` (repli `hsl()`, `oklch()` si pris en charge). Contrastes vérifiés WCAG AA : texte clair sur `--t-fort`, jamais sur `--t-vif` en mode clair ; `--encre-3` est le gris le plus pâle autorisé pour du texte.
- **Téléchargement zip** : les boutons `[data-telecharger]` ouvrent la boîte de dialogue de licence (`<dialog id="licence">`). « J'accepte et je télécharge » lance `https://github.com/ctalpaert/exercices-scolaires/archive/refs/heads/main.zip` (constantes `DEPOT` et `BRANCHE` en haut du script) ; « Annuler », Échap ou un clic à côté ferment sans télécharger. Le lien « Lire la licence » du pied de page ouvre la même boîte sans bouton de téléchargement.
- Le texte officiel français de la licence est intégré entre `<!-- TEXTE_LICENCE:DEBUT -->` et `<!-- TEXTE_LICENCE:FIN -->` (source : <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.fr>, texte dans le domaine public CC0). Ne pas le résumer ni le modifier.
- Ne jamais lister les fiches à la main dans `index.html` : tout passe par `catalogue.js`.

## Licence

**CC BY-NC-SA 4.0** (choix de l'utilisateur, à la place de la GPL-3 initiale qui autorise la revente). Attribution demandée, partout la même : « Mentionnez « Exercices scolaires, ctalpaert » avec un lien vers le site et vers la licence, et signalez vos modifications. » Usage commercial et revente interdits ; dérivés sous la même licence. Ne pas réintroduire la GPL ni ajouter de clause qui contredirait la licence. Demandes de retrait : issues GitHub.

## Publication

Committer et pousser seulement quand l'utilisateur le demande ; la publication se fait directement sur `main` (c'est ce que sert GitHub Pages). Pour chaque publication :

1. Dans le dossier Drive : `py outils/publier.py` (régénère le catalogue en `--strict`, puis copie vers le clone). `--essai` pour voir sans copier.
2. Dans le clone : `git status` et `git diff --stat` ; vérifier qu'aucun PDF, DOCX, ODT, photo de fiche originale ni `desktop.ini` n'apparaît.
3. `git add -A`, commit (message en français, à l'impératif, ex. « Ajoute la fiche Les nombres jusqu'à 100 »), `git push origin main`.
4. Une à deux minutes plus tard : `curl -sI https://ctalpaert.github.io/exercices-scolaires/` renvoie 200 et la nouvelle fiche s'ouvre en ligne.

Réglages à faire une seule fois par l'utilisateur sur GitHub (Claude ne touche pas aux réglages du dépôt) : Settings › Pages › « Deploy from a branch », branche `main`, dossier `/ (root)` ; dans « About », description et lien vers le site.

## Avant de dire « c'est publié »

- [ ] `py outils/generer_catalogue.py --strict` : 0 avertissement.
- [ ] Chaque nouvelle fiche s'ouvre, s'imprime sur le bon nombre de feuilles A4, son corrigé fonctionne, la mention de licence est lisible et ne chevauche rien.
- [ ] `index.html` affiche la fiche au bon endroit ; filtres et recherche la trouvent.
- [ ] `git status` dans le clone : uniquement des fichiers attendus.
- [ ] Push effectué et site en ligne vérifié.
