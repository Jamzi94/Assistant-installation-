# Données du site

`site-data.json` est un instantané public généré à partir du catalogue, des tutoriels et des médias de l’Assistant Installation V5.7. Le champ `generated_at` indique quand cet instantané a été créé; `refresh_policy` précise qu’il ne se met pas à jour automatiquement.

Pour conserver les routes et le vocabulaire des guides en phase avec le bot, exécuter depuis la racine de ce site :

```bash
python3 tools/export_public_data.py --source /chemin/vers/assistant-installation-v5.7-experience-pro
```

Les URL de captures et de vidéos proviennent des métadonnées de médias du projet source et restent hébergées par leurs fournisseurs respectifs. Elles peuvent changer ou devenir indisponibles.
