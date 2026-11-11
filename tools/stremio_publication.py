#!/usr/bin/env python3
"""Correct and validate the public iPhone/iPad Stremio guide.

This module is called by export_public_data.py and can also update the checked-in
static JSON directly. It refuses unknown guide shapes rather than silently applying
step-index assumptions to a changed source.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
APP_DOWNLOADS = "https://www.stremio.com/downloads"
STREMIO_WEB = "https://web.stremio.com/"
ALTSTORE_DOWNLOAD = "https://altstore.io/download"
PAL_SOURCE = "https://altstore.io/source/dl.strem.io/apple/altstore/source.json?app=com.stremio.pal"
PAL_EU_JAPAN = "https://blog.stremio.com/stremio-released-on-apple-altstore-for-europe-and-japan/"
PAL_BRAZIL = "https://blog.stremio.com/stremio-released-on-apple-altstore-for-brazil/"
ADDONS_HELP = "https://stremio.zendesk.com/hc/en-us/articles/360021348391-How-to-install-uninstall-Add-ons"
CLASSIC_WINDOWS = "https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows"
CLASSIC_MACOS = "https://faq.altstore.io/altstore-classic/how-to-install-altstore-macos"
CLASSIC_OVERVIEW = "https://faq.altstore.io/altstore-classic/your-altstore"


def _one(items: list[dict[str, Any]], item_id: str, context: str) -> dict[str, Any]:
    found = [item for item in items if item.get("id") == item_id]
    if len(found) != 1:
        raise ValueError(f"{context}: attendu un élément id={item_id!r}, trouvé {len(found)}")
    return found[0]


def _set_step(
    step: dict[str, Any], *, title: str, body: str,
    url: str | None = None, url_label: str | None = None,
    links: list[list[str]] | None = None, substeps: list[str] | None = None,
    hide_image: bool = False,
) -> None:
    step["title"] = title
    step["body"] = body
    if url:
        step["url"] = url
    else:
        step.pop("url", None)
    if url_label:
        step["url_label"] = url_label
    else:
        step.pop("url_label", None)
    if links is not None:
        step["links"] = links
    if substeps is not None:
        step["substeps"] = substeps
    else:
        step.pop("substeps", None)
    if hide_image:
        # The supplied PAL step-2 illustration says to open the app, while this
        # step opens the download site. Hide it rather than display a false cue.
        step.pop("image", None)


def _update_pal(app: dict[str, Any], device: str) -> None:
    methods = app.get("install", {}).get(device, [])
    pal = _one(methods, "pal", f"stremio.install.{device}")
    steps = pal.get("steps", [])
    if len(steps) not in (6, 7):
        raise ValueError(f"Stremio {device} PAL: 6 ou 7 étapes attendues, trouvé {len(steps)}")
    if not any("AltStore" in str(step.get("title", "")) for step in steps[:4]):
        raise ValueError(f"Stremio {device} PAL: structure d’étapes inattendue; export interrompu")

    region_body = (
        "Pour iPhone, il faut iOS 18 ou plus, être physiquement dans l’Union européenne, au Japon ou au Brésil, "
        "et utiliser un compte App Store de la région correspondante. Si une condition manque, choisis Stremio Web."
        if device == "iphone" else
        "Pour installer Stremio sur iPad via PAL, il faut iPadOS 18 ou plus, être physiquement dans l’Union européenne "
        "et utiliser un compte App Store de l’UE. Stremio ne propose pas son app PAL pour iPad au Japon ni au Brésil. "
        "Sinon, choisis Stremio Web."
    )
    _set_step(
        steps[0], title="Vérifie l’éligibilité de ton appareil", body=region_body,
        links=[["Annonce Stremio · Europe et Japon", PAL_EU_JAPAN], ["Annonce Stremio · Brésil", PAL_BRAZIL]],
        hide_image=(device == "ipad"),
    )
    _set_step(
        steps[1], title="Télécharge AltStore PAL", 
        body="Sur ton iPhone ou iPad, saisis altstore.io/download dans Safari, Chrome ou Vivaldi, puis touche « Download ». "
             "Cela télécharge la place de marché; confirme son installation à l’étape 4.",
        url=ALTSTORE_DOWNLOAD, url_label="Télécharger AltStore PAL · site officiel", links=[], hide_image=True,
    )
    steps[1]["image"] = "assets/methods/stremio/pal-download.svg"
    steps[1]["image_alt"] = "Illustration : page altstore.io dans un navigateur, bouton Download, puis téléchargement sur un appareil mobile."
    _set_step(
        steps[2], title="Autorise la place de marché", 
        body="Si iOS/iPadOS affiche une demande, ouvre Réglages et autorise « Marketplace From AltStore LLC » "
             "(le libellé peut varier selon la langue). Reviens ensuite à l’onglet AltStore du navigateur et touche "
             "« Download » une seconde fois. Ne quitte pas la page avant la fin de cette autorisation.",
        links=[],
    )
    _set_step(
        steps[3], title="Confirme l’installation d’AltStore PAL", 
        body="Dans l’alerte d’installation qui suit, confirme « Install App Marketplace » ou son équivalent localisé. "
             "Attends que l’icône AltStore PAL apparaisse sur l’écran d’accueil.",
        links=[],
    )
    _set_step(
        steps[4], title="Ajoute la source officielle Stremio",
        body="La recherche dans AltStore PAL suffit si Stremio est déjà visible. Si la fiche Stremio manque, ajoute la "
             "source officielle à l’aide du lien ci-dessous. Le lien ouvre AltStore Preview; il faut confirmer « Add Source ». "
             "Cela ajoute la source, mais n’installe pas encore Stremio.",
        links=[["Source officielle Stremio pour AltStore PAL", PAL_SOURCE]],
        substeps=[
            "Ouvre AltStore PAL et cherche « Stremio » dans Browse; vérifie que l’éditeur affiché est Stremio.",
            "Si l’app est absente, touche le lien officiel ci-dessus. Dans AltStore Preview, confirme « Add Source ».",
            "Retourne dans AltStore PAL et recherche Stremio de nouveau. Passe à l’étape 6 pour installer l’app.",
        ],
    )
    _set_step(
        steps[5], title="Installe Stremio dans AltStore PAL",
        body="Dans AltStore PAL, ouvre la fiche Stremio publiée par Stremio et lance l’installation. Confirme les écrans "
             "demandés par PAL, puis attends la fin. Si l’éditeur n’est pas Stremio ou si l’installation ne correspond pas "
             "à l’app attendue, annule et ne télécharge pas d’IPA depuis un tiers.",
        links=[],
    )
    final_step = {
        "title": "Ouvre Stremio",
        "body": "Après l’installation, ouvre Stremio depuis l’écran d’accueil. Connecte-toi à ton compte Stremio et "
                "teste un contenu auquel tu as légalement accès. Ne partage jamais ton mot de passe.",
        "links": [],
    }
    if len(steps) == 6:
        steps.append(final_step)
    else:
        steps[6].clear()
        steps[6].update(final_step)


def _update_classic(app: dict[str, Any], device: str) -> None:
    method = _one(app.get("install", {}).get(device, []), "classic_info", f"stremio.install.{device}")
    method["label"] = "⚠️ AltStore Classic — IPA officielle Stremio requise"
    steps = method.get("steps", [])
    if len(steps) != 3:
        raise ValueError(f"Stremio {device} Classic: 3 étapes attendues, trouvé {len(steps)}")
    _set_step(
        steps[0], title="Vérifie qu’une IPA Stremio officielle est publiée",
        body="Au contrôle du 11 novembre 2026, la page de téléchargements Stremio présente l’option iOS PAL et Stremio Web, "
             "mais aucun fichier IPA iOS/iPadOS autonome à télécharger. Ne continue que si une IPA est effectivement "
             "publiée par Stremio sur sa page officielle au moment de l’installation. Sinon, arrête le parcours et choisis "
             "AltStore PAL si tu es éligible, ou Stremio Web. N’utilise jamais une IPA d’un site tiers.",
        url=APP_DOWNLOADS, url_label="Vérifier les téléchargements Stremio officiels", links=[],
    )
    _set_step(
        steps[1], title="Installe AltStore Classic sur ton iPhone/iPad depuis un ordinateur",
        body="Cette étape n’est utile qu’après avoir vérifié l’existence d’une IPA officielle. AltServer doit être installé "
             "sur un PC Windows ou un Mac; choisis uniquement le tutoriel correspondant à ton ordinateur. Les instructions "
             "Windows et macOS ne sont pas interchangeables.",
        links=[["AltStore Classic · guide Windows", CLASSIC_WINDOWS], ["AltStore Classic · guide macOS", CLASSIC_MACOS]],
    )
    _set_step(
        steps[2], title="Ajoute l’IPA officielle depuis My Apps",
        body="Sur l’appareil, ouvre AltStore Classic, va dans « My Apps », touche « + » et sélectionne uniquement l’IPA "
             "Stremio publiée officiellement. Avec un compte Apple gratuit, les apps sideloadées demandent un rafraîchissement "
             "périodique (souvent tous les 7 jours); vérifie la limite actuelle dans la FAQ AltStore. Sans IPA officielle "
             "disponible, n’effectue pas cette étape.",
        links=[["AltStore Classic · fonctionnement de My Apps", CLASSIC_OVERVIEW]],
    )


def apply_stremio_overrides(document: dict[str, Any]) -> dict[str, Any]:
    """Apply the verified guide overrides to a static site-data or fresh export."""
    apps = document.get("apps")
    if not isinstance(apps, dict) or "stremio" not in apps:
        raise ValueError("Données invalides: application Stremio absente")
    app = apps["stremio"]

    for device in ("iphone", "ipad"):
        _update_pal(app, device)
        _update_classic(app, device)

        web = _one(app.get("install", {}).get(device, []), "web", f"stremio.install.{device}")
        web_steps = web.get("steps", [])
        if len(web_steps) != 3:
            raise ValueError(f"Stremio {device} Web: 3 étapes attendues, trouvé {len(web_steps)}")
        _set_step(web_steps[0], title="Ouvre Stremio Web", 
                  body="Sur ton iPhone ou iPad, touche le bouton ci-dessous pour ouvrir Stremio Web dans le navigateur. "
                       "Aucune application n’est à installer; cette version Web peut avoir des limites sur iOS/iPadOS.",
                  url=STREMIO_WEB, url_label="Ouvrir Stremio Web", links=[])
        _set_step(web_steps[1], title="Connecte-toi à ton compte Stremio",
                  body="Sur Stremio Web, connecte-toi à ton compte. Les menus et la lecture peuvent différer de l’application "
                       "complète; si une fonction manque, vérifie la documentation officielle avant de changer de méthode.",
                  links=[])
        _set_step(web_steps[2], title="Crée un accès rapide (facultatif)",
                  body="Dans Safari, touche Partager puis « Sur l’écran d’accueil » si tu veux un raccourci. Si une lecture "
                       "ou une fonction n’est pas disponible, reviens au choix des méthodes et vérifie l’éligibilité PAL; "
                       "ne télécharge pas d’IPA depuis un site tiers.", links=[])

        # The general app-level area keeps Web and the official download hub; PAL
        # links live in the PAL tutorial only, where their actions are explained.
        app.setdefault("distribution_links", {})[device] = [
            pair for pair in app.get("distribution_links", {}).get(device, [])
            if "altstore.io" not in str(pair[1]).lower()
            and "altstore" not in str(pair[0]).lower()
        ]

        config = _one(app.get("configure", {}).get(device, []), "general", f"stremio.configure.{device}")
        config_steps = config.get("steps", [])
        if len(config_steps) < 3:
            raise ValueError(f"Stremio {device} configuration: au moins 3 étapes attendues")
        _set_step(config_steps[0], title="Connecte ton compte Stremio",
                  body="Ouvre Stremio sur cet appareil et connecte-toi à ton compte Stremio. Utilise le même compte "
                       "sur tes appareils pour retrouver les éléments associés au compte. Le code d’association affiché "
                       "sur une télévision ne fait pas partie de ce parcours iPhone/iPad.", links=[])
        _set_step(config_steps[1], title="Gère les extensions depuis une interface documentée",
                  body="La documentation Stremio décrit l’ajout d’extensions sur Web/ordinateur et Android, mais pas un menu "
                       "équivalent dans l’app iOS. Pour ajouter une extension, connecte-toi au même compte depuis Stremio Web "
                       "ou un ordinateur, ouvre « Add-ons » (icône puzzle), puis vérifie ce qui est disponible sur iPhone/iPad. "
                       "Stremio ne contrôle pas toutes les extensions communautaires; choisis uniquement des sources légales et fiables.",
                  url=ADDONS_HELP, url_label="Aide officielle Stremio · extensions", links=[])
        _set_step(config_steps[2], title="Vérifie le compte et la lecture",
                  body="Retourne dans Stremio sur iPhone/iPad et vérifie que tu es connecté au bon compte. Teste un contenu "
                       "auquel tu as légalement accès. Si une extension ou une fonction n’apparaît pas sur iOS/iPadOS, vérifie-la "
                       "sur Stremio Web ou ordinateur: le menu mobile n’est pas garanti identique.", links=[])

        issues = app.setdefault("troubleshooting", {}).get(device, [])
        if not isinstance(issues, list):
            raise ValueError(f"Stremio {device} dépannage invalide")
        issues_by_id = {entry.get("id"): entry for entry in issues}
        for issue_id, label, text, links in (
            ("download", "⬇️ Téléchargement iPhone/iPad impossible", 
             "Vérifie la connexion, l’espace libre, la version du système et la région de ton compte. Pour PAL, utilise "
             "uniquement le guide AltStore PAL de cette fiche; si les critères ne sont pas réunis, ouvre Stremio Web. "
             "N’installe pas d’IPA provenant d’un site tiers.",
             [["Téléchargements Stremio officiels", APP_DOWNLOADS], ["Stremio Web", STREMIO_WEB]]),
            ("install", "🚫 Installation iPhone/iPad refusée",
             "Pour AltStore PAL, recontrôle iOS/iPadOS 18+, la présence physique et le compte App Store de la région "
             "éligible (sur iPad, Stremio PAL est limité à l’UE). Pour AltStore Classic, continue uniquement si une IPA "
             "est publiée par Stremio. Si une condition manque, arrête et utilise Stremio Web.",
             [["Téléchargements Stremio officiels", APP_DOWNLOADS], ["Stremio Web", STREMIO_WEB]]),
            ("altstore_pal", "🍎 AltStore PAL · Stremio absent",
             "Reviens à Installer → AltStore PAL → étape 5. Le lien « Source officielle Stremio pour AltStore PAL » ajoute "
             "la source; il n’installe pas l’application. Après confirmation « Add Source », retourne dans AltStore PAL et "
             "recherche Stremio. Si la page ne s’ouvre pas, vérifie AltStore PAL et la région avant de réessayer.", []),
            ("altstore_classic", "🧰 AltStore Classic · IPA absente",
             "AltStore Classic ne peut installer Stremio que si Stremio publie une IPA iOS/iPadOS officielle. Au contrôle "
             "du 11 novembre 2026, aucun fichier IPA autonome n’était proposé sur la page Stremio. N’importe pas une IPA "
             "tierce; choisis PAL si éligible ou Stremio Web.",
             [["Vérifier les téléchargements Stremio officiels", APP_DOWNLOADS]]),
        ):
            entry = issues_by_id.get(issue_id, {"id": issue_id})
            entry.update({"label": label, "text": text, "links": links})
            issues_by_id[issue_id] = entry
        # Remove the old combined branch; it repeated PAL/Classic advice outside
        # their installation paths and encouraged opening the store generically.
        issues_by_id.pop("altstore", None)
        ordered = ["download", "install", "altstore_pal", "altstore_classic"]
        new_issues = [issues_by_id.pop(item_id) for item_id in ordered if item_id in issues_by_id]
        for entry in issues:
            issue_id = entry.get("id")
            if issue_id in issues_by_id:
                new_issues.append(issues_by_id.pop(issue_id))
        new_issues.extend(issues_by_id.values())
        app["troubleshooting"][device] = new_issues

    for device in ("iphone", "ipad"):
        pal = _one(app["install"][device], "pal", f"stremio.install.{device}")
        if len(pal["steps"]) != 7:
            raise ValueError(f"Stremio {device} PAL: le guide doit contenir 7 étapes")

    for video in document.get("videos", []):
        if video.get("id") == "altstore_classic_windows":
            video["method_ids"] = ["classic_info"]
            video["disclaimer"] = (
                "Vidéo tierce en anglais sur AltStore Classic sous Windows; elle ne montre ni AltStore PAL ni "
                "l’installation de Stremio. Contenu non visionné; préfère les guides officiels AltStore."
            )

    return document


def validate_stremio_overrides(document: dict[str, Any]) -> list[str]:
    """Raise on regressions and return concise evidence of the contract checked."""
    apps = document.get("apps", {})
    app = apps.get("stremio", {})
    errors: list[str] = []
    for device in ("iphone", "ipad"):
        methods = app.get("install", {}).get(device, [])
        try:
            pal = _one(methods, "pal", f"stremio.install.{device}")
            classic = _one(methods, "classic_info", f"stremio.install.{device}")
            steps = pal.get("steps", [])
            if len(steps) != 7:
                errors.append(f"{device}: PAL doit avoir 7 étapes")
                continue
            source_links = [link for link in steps[4].get("links", []) if len(link) == 2 and link[1] == PAL_SOURCE]
            if len(source_links) != 1:
                errors.append(f"{device}: lien source direct absent ou dupliqué hors de l’étape 5")
            if steps[1].get("url") != ALTSTORE_DOWNLOAD:
                errors.append(f"{device}: téléchargement PAL doit être dans l’étape 2")
            if steps[1].get("image") != "assets/methods/stremio/pal-download.svg":
                errors.append(f"{device}: l’illustration navigateur/téléchargement manque à l’étape 2")
            if device == "ipad" and steps[0].get("image"):
                errors.append("ipad: image régionale générique affichée malgré la restriction Stremio PAL UE")
            step5_text = " ".join([steps[4].get("title", ""), steps[4].get("body", ""), *steps[4].get("substeps", [])]).lower()
            if step5_text.count("ouvre altstore pal") != 1:
                errors.append(f"{device}: l’étape 5 doit contenir une seule instruction d’ouverture d’AltStore PAL")
            for index in (0, 1, 2, 3, 5, 6):
                text = (steps[index].get("title", "") + " " + steps[index].get("body", "")).lower()
                if "ouvre altstore pal" in text:
                    errors.append(f"{device}: instruction d’ouverture AltStore PAL répétée à l’étape {index + 1}")
            if "ipa" not in (classic["steps"][0].get("body", "").lower()):
                errors.append(f"{device}: branche Classic ne précise pas l’IPA officielle requise")
            if any(link[1] == PAL_SOURCE for s in classic.get("steps", []) for link in s.get("links", []) if len(link) == 2):
                errors.append(f"{device}: source PAL affichée dans la branche Classic")
            if any("altstore.io" in str(pair[1]).lower() or "altstore" in str(pair[0]).lower()
                   for pair in app.get("distribution_links", {}).get(device, [])):
                errors.append(f"{device}: lien AltStore générique affiché hors du guide d’installation")
            trouble = app.get("troubleshooting", {}).get(device, [])
            if any(issue.get("id") == "altstore" for issue in trouble):
                errors.append(f"{device}: ancienne aide AltStore combinée non supprimée")
            if any("code d’association affiché sur la TV" in str(step.get("body", ""))
                   for cfg in app.get("configure", {}).get(device, []) for step in cfg.get("steps", [])):
                errors.append(f"{device}: instruction de code TV affichée dans la configuration mobile")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"{device}: {exc}")

    video = next((item for item in document.get("videos", []) if item.get("id") == "altstore_classic_windows"), None)
    if video and video.get("method_ids") != ["classic_info"]:
        errors.append("la vidéo AltStore Classic n’est pas filtrée par méthode")
    if errors:
        raise ValueError("\n".join(errors))
    return [
        "PAL iPhone/iPad: 7 étapes cohérentes; le lien source officiel apparaît uniquement à l’étape 5.",
        "AltStore PAL: une instruction d’ouverture, au bon moment; captures ambiguës masquées.",
        "AltStore Classic: parcours conditionné à une IPA officielle, sans lien source PAL.",
        "Configuration et dépannage iOS/iPadOS: aucun code d’association TV ni téléchargement AltStore hors du guide.",
        "Vidéo AltStore Classic: filtrée par méthode.",
    ]


def main() -> int:
    import argparse
    from datetime import datetime, timezone

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="valider les données actuelles sans les modifier")
    args = parser.parse_args()
    document = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if args.check:
        checks = validate_stremio_overrides(document)
        print("Données valides — aucune écriture effectuée.")
    else:
        apply_stremio_overrides(document)
        document["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        checks = validate_stremio_overrides(document)
        DATA_PATH.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Correction appliquée à", DATA_PATH)
    print("\n".join(f"OK — {line}" for line in checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
