#!/usr/bin/env python3
"""Export public static JSON from an Assistant Installation V5.7 source checkout.

Usage:
  python tools/export_public_data.py --source /path/to/assistant-installation-v5.7

The source project is read only. Only data/site-data.json in this website is written.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def clean_step(step: dict) -> dict:
    clean = {key: step[key] for key in ('title', 'body', 'url', 'video', 'image', 'links') if step.get(key)}
    if clean.get('url') and urlsplit(clean['url']).scheme != 'https':
        clean.pop('url', None)
    if clean.get('image') and isinstance(clean['image'], str):
        clean['image'] = clean['image'] if clean['image'].startswith(('https://', 'assets/')) else None
        if clean['image'] is None:
            clean.pop('image', None)
    clean['links'] = [
        [str(label), str(url)] for label, url in clean.get('links', [])
        if urlsplit(str(url)).scheme == 'https'
    ]
    return clean


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='Racine du projet Assistant Installation V5.7')
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    if not (source / 'install_assistant' / 'catalog.py').is_file():
        parser.error('Le chemin --source doit contenir install_assistant/catalog.py')
    sys.path.insert(0, str(source))

    from install_assistant.catalog import CATALOG
    from install_assistant.downloads import download_buttons
    from install_assistant.engine import act, fresh, render, download_actions
    from install_assistant.media import gallery
    from install_assistant.nuvio_guides import NUVIO_APPS, choices as nuvio_choices, steps as nuvio_steps
    from install_assistant.tutorials import configuration_steps, methods_for, steps as install_steps
    from install_assistant import videos as video_module

    video_path = source / 'videos.json'
    videos = json.loads(video_path.read_text(encoding='utf-8')).get('items', [])
    media_path = source / 'media.json'
    media_doc = json.loads(media_path.read_text(encoding='utf-8'))
    apps_out = {}
    media_out = {}
    for app_id, app in CATALOG['apps'].items():
        public_app = {
            key: json_safe(app[key]) for key in (
                'name', 'services', 'devices', 'method', 'site', 'source', 'links',
                'access', 'note', 'publisher_type', 'prerequisites', 'downloader_code',
                'code_source_status', 'code_target_status', 'platform_support', 'play_store',
                'accounts', 'stremio_addons'
            ) if key in app
        }
        public_app['install'] = {}
        public_app['configure'] = {}
        public_app['troubleshooting'] = {}
        public_app['distribution_links'] = {}

        for device_id in app.get('devices', []):
            methods = methods_for(app_id, device_id)
            install_options = []
            for method in methods:
                state = {
                    'stage': 'tutorial', 'intent': 'install', 'app': app_id,
                    'device': device_id, 'method': method['id'], 'index': 0,
                }
                install_options.append({
                    'id': method['id'], 'label': method['label'],
                    'steps': [clean_step(s) for s in install_steps(state)],
                })
            public_app['install'][device_id] = install_options
            distribution_links = [
                [label, url] for label, url in download_actions(app_id, device_id)
                if urlsplit(url).scheme == 'https'
            ]
            distribution_links.extend(
                [[label, url] for label, url in download_buttons(app_id, device_id)
                 if urlsplit(url).scheme == 'https']
            )
            public_app['distribution_links'][device_id] = []
            seen_links = set()
            for label, url in distribution_links:
                key = (str(label), str(url))
                if key in seen_links:
                    continue
                seen_links.add(key)
                public_app['distribution_links'][device_id].append([str(label), str(url)])

            config_routes = []
            seen = set()
            def add_config(route_id, label, steps):
                if route_id in seen:
                    return
                seen.add(route_id)
                config_routes.append({
                    'id': route_id, 'label': label,
                    'steps': [clean_step(s) for s in steps],
                })

            base_state = {
                'stage': 'tutorial', 'intent': 'configure', 'app': app_id,
                'device': device_id, 'method': 'configuration', 'index': 0,
            }
            add_config('general', 'Configuration générale', configuration_steps(base_state))
            if app_id in NUVIO_APPS:
                for action, label in nuvio_choices(app_id, device_id):
                    if action.startswith('nuvio:'):
                        mode = action.split(':', 1)[1]
                        try:
                            add_config('nuvio-' + mode, label, nuvio_steps(app_id, device_id, mode))
                        except ValueError:
                            continue
            variants = []
            if app_id in ('nuvio_plus_tv', 'nuvio_plus_mobile', 'fjordplayer'):
                variants = [('m3u', 'Ajouter une source M3U'), ('xtream', 'Ajouter une source Xtream'), ('unsure', 'Je ne connais pas mon type de source')]
            elif app_id == 'nyxplayer':
                variants = [('xtream', 'Configurer Xtream'), ('m3u', 'Vérifier la prise en charge M3U'), ('unsure', 'Je ne connais pas mon type de source')]
            elif app_id == 'ipvio_stream':
                variants = [('m3u', 'Configurer M3U'), ('xtream', 'Configurer Xtream'), ('stalker', 'Configurer Stalker / Ministra'), ('unsure', 'Je ne connais pas mon type de source')]
            elif app_id == 'kdtivi':
                variants = [('m3u', 'Configurer M3U'), ('xtream', 'Configurer Xtream'), ('library', 'Connecter une médiathèque'), ('addons', 'Configurer des extensions'), ('unsure', 'Je ne connais pas mon type de source')]
            for variant, label in variants:
                variant_state = dict(base_state, source_kind=variant)
                add_config(variant, label, configuration_steps(variant_state))
            public_app['configure'][device_id] = config_routes

            # Reuse the bot's exact contextual help labels and responses.
            current = fresh()
            for action in (
                'intent:install',
                'group:' + CATALOG['devices'][device_id]['group'],
                'device:' + device_id,
                'app:' + app_id,
            ):
                choices_now = dict(render(current).choices)
                if action not in choices_now:
                    break
                current = act(current, action)
            help_options = dict(render(current).choices)
            if 'help' in help_options:
                help_state = act(current, 'help')
                issues = []
                for action, label in render(help_state).choices:
                    if action.startswith('issue:'):
                        issue_state = act(help_state, action)
                        view = render(issue_state)
                        issues.append({
                            'id': action.split(':', 1)[1], 'label': label,
                            'text': view.text,
                            'links': [[title, url] for title, url in view.links if urlsplit(url).scheme == 'https'],
                        })
                public_app['troubleshooting'][device_id] = issues
            else:
                public_app['troubleshooting'][device_id] = []

            media_out.setdefault(app_id, {})[device_id] = [
                {
                    'title': item.get('title', 'Visuel éditeur'),
                    'url': item.get('url'),
                    'source': item.get('source') or item.get('url'),
                    'kind': item.get('kind', 'image'),
                    'alt': item.get('alt') or item.get('title', 'Visuel publié par l’éditeur'),
                }
                for item in gallery(app_id, device_id)
                if item.get('url') and urlsplit(item['url']).scheme == 'https'
            ]
        apps_out[app_id] = public_app

    # Only include videos relevant to the exact selected device and app.
    videos_out = []
    for video in videos:
        url = video.get('url', '')
        if urlsplit(url).scheme != 'https':
            continue
        videos_out.append({key: json_safe(video[key]) for key in (
            'id', 'title', 'creator', 'lang', 'published', 'url', 'apps', 'devices',
            'topics', 'disclaimer', 'verification_status'
        ) if key in video})

    payload = {
        'schema_version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'source_version': 'Assistant Installation V5.7',
        'refresh_policy': 'Données exportées à la date de génération; aucune actualisation automatique n’est promise.',
        'devices': json_safe(CATALOG['devices']),
        'device_groups': json_safe(CATALOG.get('device_groups', {})),
        'services': json_safe(CATALOG.get('services', {})),
        'apps': apps_out,
        'media': media_out,
        'videos': videos_out,
        'media_checked_on': media_doc.get('checked_on'),
        'video_checked_on': json.loads(video_path.read_text(encoding='utf-8')).get('checked_on'),
        'video_verification_method': json.loads(video_path.read_text(encoding='utf-8')).get('verification_method'),
    }
    output = Path(__file__).resolve().parents[1] / 'data' / 'site-data.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Exporté {len(apps_out)} applications, {len(CATALOG["devices"])} appareils, {len(videos_out)} vidéos : {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
