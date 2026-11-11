# Données du site

`site-data.json` est un instantané public construit à partir du catalogue, des tutoriels et des médias de l’Assistant Installation V5.7. `generated_at` indique la date de l’export; `refresh_policy` rappelle que les releases, les stores et les pages éditeur ne sont pas surveillés automatiquement. Les corrections de liens et l’état de fraîcheur sont suivis dans [`AUDIT_ACTUALISATION_2026-11-11.md`](../AUDIT_ACTUALISATION_2026-11-11.md).

## Mise à jour reproductible

Après une modification du catalogue ou des tutoriels du bot, exécutez depuis la racine de cette copie du site :

```bash
python3 tools/export_public_data.py --source /chemin/vers/assistant-installation-v5.7-experience-pro
python3 tools/stremio_publication.py --check
```

L’exporteur lit le checkout du bot sans le modifier. Il régénère `data/site-data.json`, applique automatiquement les corrections iPhone/iPad Stremio PAL/Classic puis valide leurs invariants avant d’écrire. En cas de structure inattendue, il s’arrête au lieu de produire un guide silencieusement décalé. Le module `stremio_publication.py` peut aussi appliquer ses corrections au JSON actuel; ses chemins sont relatifs à la racine du dépôt.

Les scripts `normalize_guides.py`, `add_kdtivi_qr.py`, `deep_text_cleanup_pass1.py` et `execute_exhaustive_todo.py` sont des outils de migration qui modifient les données. N’exécutez-les que si vous souhaitez réellement réappliquer leurs transformations, et faites une copie du JSON avant tout changement manuel.

## Champs de présentation

Les objets d’étape peuvent contenir `title`, `body`, `url`, `url_label`, `links`, `substeps`, `image`, `image_alt` et `video`. `substeps` est une liste de textes numérotés; `url_label` donne un intitulé précis au bouton externe; `image_alt` décrit une illustration à un lecteur d’écran. Les objets vidéo peuvent contenir `method_ids` pour n’apparaître que dans une méthode sélectionnée, par exemple AltStore Classic.

## Règles Stremio PAL / Classic

Le guide iPhone PAL indique les régions annoncées par Stremio (UE, Japon et Brésil); le guide iPad PAL limite Stremio à l’UE, conformément aux annonces consultées le 11 novembre 2026. Le lien source actuel affiché par la page officielle Stremio Downloads est `https://altstore.io/source/dl.strem.io/apple/altstore/source.json?app=com.stremio.pal`; il ouvre la confirmation « Add Source » d’AltStore PAL. Il ajoute une source et ne télécharge pas une IPA ni n’installe à lui seul l’application.

La source Stremio n’apparaît que dans l’étape 5 du parcours PAL. AltStore Classic demeure conditionnel à une IPA iOS/iPadOS publiée par Stremio; si cette IPA n’est pas disponible sur la page officielle, il faut arrêter cette branche et choisir PAL (si éligible) ou Web. Le site Stremio ne publie pas automatiquement les mises à jour dans ce JSON : recontrôlez les sources avant toute rediffusion.

## Médias et publication

Les URL de captures et de vidéos peuvent changer ou devenir indisponibles. Les images locales sont inventoriées dans `assets/asset-manifest.json`; certaines ont une provenance ou des droits de redistribution non établis. Leur licence doit être vérifiée avant une publication publique.
