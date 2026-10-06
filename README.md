# exercices-scolaires

Fiches d'exercices à imprimer, créées à partir des notions travaillées en classe (Suisse romande, de la 1P à l'université). Textes et dessins originaux.

**Site : <https://ctalpaert.github.io/exercices-scolaires/>**

Chaque fiche est une page HTML autonome au format A4, prête à imprimer (bouton « Imprimer »), souvent avec un corrigé. La page d'accueil `index.html` les classe par degré scolaire, par matière, et permet de les chercher.

## Utiliser les fiches hors ligne

Téléchargez l'archive du dépôt (bouton « Télécharger tous les exercices en zip » sur le site), décompressez-la et ouvrez `index.html`.

## Ajouter une fiche

1. Créer la page HTML à partir de `outils/modele-fiche.html`.
2. Renseigner ses balises `<meta>` (description, matière, degré, date d'ajout).
3. Copier les fichiers publiables vers le clone git (le catalogue est régénéré au passage) : `py outils/publier.py`
4. Dans le clone : commit, puis push sur `main`.

Les conventions détaillées sont dans [CLAUDE.md](CLAUDE.md).

## Licence

Les exercices sont publiés sous licence [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr). Vous pouvez les copier, les imprimer, les distribuer et les adapter. Mentionnez « Exercices scolaires, ctalpaert » avec un lien vers le site et vers la licence, et signalez vos modifications. **Aucune utilisation commerciale** : la revente est interdite. Les versions modifiées doivent être partagées sous la même licence. Texte complet : [LICENSE](LICENSE).

## Contact

Une question, une erreur dans une fiche, ou une demande de retrait concernant des droits d'auteur : ouvrez une [issue sur GitHub](https://github.com/ctalpaert/exercices-scolaires/issues).
