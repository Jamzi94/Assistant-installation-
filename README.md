# Assistant Installation — site web statique

Version web responsive de l’Assistant Installation V5.7. Les visiteurs ouvrent un lien dans leur navigateur : ils n’ont pas à installer le bot, créer un compte GitHub, ni télécharger l’application d’assistance.

## Fonctionnement

Le site est constitué de HTML, CSS, JavaScript natif et d’un fichier JSON public. Il ne comporte ni serveur applicatif, ni base de données, ni connexion utilisateur, ni stockage de conversations, ni clé/API privée. Les choix d’appareil, d’application et d’étape sont placés dans l’URL afin qu’un guide puisse être partagé. Les captures proviennent des URL déjà référencées par le catalogue V5.7; les liens et leurs sources sont nommés. Les aperçus YouTube ne sont chargés qu’après une action volontaire.

Les compatibilités affichées sont celles du catalogue source au moment de l’export; elles ne prouvent pas le fonctionnement sur chaque modèle physique. Les applications sans preuve Fire OS explicite ne sont pas réintroduites dans le parcours Fire TV. Vega OS est séparé de Fire OS. Le site ne promet pas un rafraîchissement automatique des stores ou versions.

## Actualiser les données depuis le projet V5.7

Après toute mise à jour du catalogue, des tutoriels ou des sources, régénérez `data/site-data.json` à partir d’un checkout du projet bot :

```bash
python3 tools/export_public_data.py --source /chemin/vers/assistant-installation-v5.7-experience-pro
```

L’exporteur lit le checkout source sans le modifier; il n’écrit que `data/site-data.json`. Le fichier indique la date d’export. Vérifiez ensuite les liens et les compatibilités, puis republiez le dépôt statique. Aucun workflow automatique de veille ou d’actualisation n’est activé.

## Prévisualiser localement

Python 3 suffit; aucune dépendance à installer :

```bash
python3 -m http.server 8000
```

Ouvrez ensuite `http://localhost:8000`. Un serveur HTTP local est nécessaire car le navigateur bloque le chargement du JSON depuis certaines pages ouvertes en `file://`.

## Hébergement GitHub Pages gratuit

La documentation GitHub indique que Pages est disponible avec GitHub Free pour les dépôts publics, et le plan Free est affiché à 0 USD [1] [2]. Le site peut donc être hébergé sans abonnement d’hébergement séparé, tant qu’il reste dans les conditions de l’offre. GitHub Pages est destiné aux sites statiques; ce projet n’utilise aucune base de données ou fonction serveur [1].

Pour publier : placez le contenu de ce dossier à la racine d’un dépôt GitHub **public**, puis ouvrez Settings → Pages → Deploy from a branch → `main` → `/ (root)` → Save. Les visiteurs n’ont besoin ni d’un compte GitHub ni d’un téléchargement. Le propriétaire du site doit cependant disposer d’un compte GitHub et effectuer la première publication. Ce projet n’a créé aucun dépôt et n’a pas publié de contenu public; la destination doit être choisie et confirmée par le propriétaire.

Les quotas officiels indiquent notamment une taille publiée maximale de 1 Go et une limite de bande passante douce de 100 Go par mois [3]. Les médias hébergés par les éditeurs et YouTube restent soumis à leurs propres règles. GitHub indique également que les visites Pages sont journalisées avec l’adresse IP du visiteur à des fins de sécurité [1] [4]; le code du site lui-même n’intègre aucun outil d’analytique.

Pour un dépôt projet, toutes les références de code et d’images sont relatives (`./src/`, `./data/`, `./assets/`); le site fonctionne sous un préfixe tel que `https://<propriétaire>.github.io/<dépôt>/`. Les paramètres d’URL gardent le choix appareil/application/étape partageable. Les URL canoniques et les métadonnées sociales absolues ne sont pas préremplies avant de connaître l’adresse publique réelle.

## Confidentialité et liens

Aucun champ de mot de passe ou de source privée n’est demandé. Ne collez pas d’identifiants IPTV, d’URL privée ou de code d’association dans les formulaires du site; il n’en contient pas. Les boutons externes utilisent HTTPS, s’ouvrent avec une isolation de fenêtre et n’envoient pas de référent. Dropbox, lorsqu’il apparaît dans une méthode existante du catalogue, est étiqueté comme miroir fourni par l’administrateur et non comme lien officiel. Les raccourcis Downloader/AFTV, les projets tiers et les fiches de store sont eux aussi signalés séparément.

## Contenu

- `index.html` : entrée statique, métadonnées et contenu lisible avant exécution du JavaScript.
- `src/app.js` et `src/styles.css` : interface accessible et adaptative.
- `data/site-data.json` : appareils, applications, méthodes, guides, dépannage, médias et vidéos exportés.
- `tools/export_public_data.py` : exporteur depuis le projet bot V5.7.
- `manus-routes.json` : déclaration de la route racine pour l’aperçu de développement.

## Sources officielles

[1]: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages "À propos de GitHub Pages"
[2]: https://github.com/pricing "Tarifs GitHub"
[3]: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits "Limites de GitHub Pages"
[4]: https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement "Déclaration de confidentialité générale GitHub"
