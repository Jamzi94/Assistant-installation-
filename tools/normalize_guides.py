import json
from pathlib import Path

p = Path('/home/ubuntu/installv57_audit/data/site-data.json')
d = json.loads(p.read_text())

# Textes de sécurité utiles, mais sans répétitions de bot/chat/Telegram.
replacements = {
    'Ne les saisis jamais dans le chatbot.': 'Saisis ces données uniquement dans l’application.',
    'Ne les publie pas ici.': 'Ne partage jamais ces données.',
    'Ne colle pas cette adresse dans Telegram.': 'Ne partage pas cette adresse.',
    'ne doivent pas être partagés dans un chatbot.': 'ne doivent pas être partagés.',
    'dans le bot': 'dans l’application',
    'via le bot': 'dans l’application',
    'reviens dans le bot': 'reviens dans l’application',
}

def clean_text(value):
    if not isinstance(value, str):
        return value
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = value.replace('  ', ' ')
    return value.strip()

def clean_tree(value):
    if isinstance(value, dict):
        return {k: clean_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_tree(v) for v in value]
    return clean_text(value)

d = clean_tree(d)

# Tri global : les méthodes officielles et vérifiables avant les raccourcis/sideload.
def install_key(m):
    mid = m.get('id','').lower()
    label = m.get('label','').lower()
    if 'app_store' in mid or 'google play' in label or 'boutique' in label or 'store' in label:
        return 0
    if mid in {'official','developer'} or 'officiel' in label or 'github' in label:
        return 1
    if 'downloader' in mid or 'code' in label:
        return 2
    return 3

for app in d.get('apps', {}).values():
    for device, methods in app.get('install', {}).items():
        methods.sort(key=install_key)

# KDTIVI : parcours distincts par source et par appareil.
k = d['apps']['kdtivi']
k['integration_notes'] = {
    'iptv': 'Fonction principale : Live/TV via M3U, M3U8 ou Xtream selon la version et la source autorisée.',
    'nuvio': 'Bêta limitée aux appareils Apple déclarés. Sert aux films/séries, profil et synchronisation Nuvio, pas aux chaînes IPTV.',
    'stremio': 'Compatibilité éventuelle non confirmée : ne pas présenter comme connexion de compte ni comme méthode obligatoire.'
}

def step(title, body, url=None):
    x = {'title': title, 'body': body, 'links': []}
    if url: x['url'] = url
    return x

def kdtivi_profile(device):
    label = d['devices'][device]['name'].split(' ', 1)[-1]
    return {
        'id': 'profiles',
        'label': '👤 Profils et contrôle du compte',
        'steps': [
            step('Ouvre les profils dans KDTIVI', f'Sur {label.lower()}, ouvre le menu Profil, Compte ou Utilisateur affiché par KDTIVI. Si ce menu n’existe pas dans ta version, passe au réglage de la source.'),
            step('Crée ou sélectionne le profil', 'Choisis un profil existant ou crée-en un avec un nom et une image si ces options sont proposées. Ne crée pas un compte IPTV à cet endroit : le profil organise l’application.'),
            step('Règle les options du profil', 'Active uniquement les options visibles dans ta version : langue, affichage, contrôle parental ou profil enfant. Enregistre, puis vérifie que le bon profil est actif avant de configurer les contenus.'),
        ]
    }

def kdtivi_iptv(device):
    label = d['devices'][device]['name'].split(' ', 1)[-1]
    return {
        'id': 'iptv_live',
        'label': '📡 IPTV : Live / TV / EPG',
        'steps': [
            step('Prépare ton accès IPTV', f'Sur {label.lower()}, prépare soit une URL ou un fichier M3U/M3U8, soit une adresse de serveur, un identifiant et un mot de passe Xtream. Ces données viennent uniquement de ton fournisseur autorisé.'),
            step('Ajoute la source Live / TV', 'Dans KDTIVI, ouvre l’ajout de source ou de playlist affiché par ta version, puis choisis M3U/M3U8 ou Xtream. Ne suis pas le chemin d’une autre application si le libellé est différent.'),
            step('Règle le guide TV et les catégories', 'Après l’ajout, configure l’EPG uniquement si ton fournisseur fournit une URL EPG et si le champ existe. Sélectionne ensuite les catégories Live, TV ou chaînes que tu veux afficher.'),
            step('Teste la lecture Live', 'Lance une chaîne autorisée. Si la liste est vide, vérifie l’URL, les identifiants, la date d’expiration et l’EPG dans l’application, sans modifier le compte fournisseur.'),
        ]
    }

def kdtivi_nuvio(device):
    label = d['devices'][device]['name'].split(' ', 1)[-1]
    return {
        'id': 'nuvio_media',
        'label': '🎬 Nuvio : films / séries / profil',
        'steps': [
            step('Ouvre la connexion Nuvio', f'Sur {label.lower()}, ouvre Nuvio Login, Compte ou Sync uniquement si ce bouton est présent dans KDTIVI. Cette fonction est bêta et limitée à cette version Apple.'),
            step('Associe ton compte Nuvio', 'Utilise le QR, le lien ou les identifiants affichés par KDTIVI selon la méthode proposée. Le compte Nuvio est distinct de l’accès IPTV et ne remplace pas tes identifiants Xtream ou M3U.'),
            step('Choisis le profil Nuvio', 'Après la connexion, sélectionne le profil Nuvio à utiliser. Vérifie que le nom du profil, la progression et la bibliothèque de films/séries correspondent à ton compte.'),
            step('Teste un film puis une série', 'Ouvre un film et un épisode de série autorisés. Si la bibliothèque est vide, vérifie le compte, le profil et la synchronisation Nuvio ; ne modifie pas la source Live / TV.'),
        ]
    }

# Ajouter les blocs continus et ordonner le sélecteur.
for device, options in list(k.get('configure', {}).items()):
    existing = {x.get('id'): x for x in options}
    # Le général devient un point d’entrée court, sans mélange de comptes.
    if 'general' in existing:
        existing['general']['label'] = 'Vue d’ensemble : choisir son accès'
        existing['general']['steps'] = [
            step('Choisis ce que tu veux régler', 'KDTIVI sépare trois usages : Profils pour l’organisation du compte, Nuvio pour les films et séries, IPTV pour le Live et la télévision.'),
            step('Ouvre le guide correspondant', 'Choisis ensuite Profils, Nuvio ou IPTV dans la liste. Ne mélange pas un compte Nuvio avec un identifiant IPTV.'),
        ]
    else:
        existing['general'] = {'id':'general','label':'Vue d’ensemble : choisir son accès','steps':[
            step('Choisis ce que tu veux régler','KDTIVI sépare Profils, Nuvio pour les films/séries et IPTV pour le Live/TV.'),
            step('Ouvre le guide correspondant','Choisis le guide adapté à ton accès. Ne mélange pas compte Nuvio et identifiants IPTV.')
        ]}
    existing['profiles'] = kdtivi_profile(device)
    existing['iptv_live'] = kdtivi_iptv(device)
    if device in {'apple_tv','iphone','ipad'}:
        existing['nuvio_media'] = kdtivi_nuvio(device)
    else:
        existing.pop('nuvio_login', None)
        existing.pop('nuvio_media', None)
    priority = ['profiles','nuvio_media','iptv_live','m3u','xtream','general','library','addons','unsure']
    k['configure'][device] = sorted(existing.values(), key=lambda x: priority.index(x.get('id')) if x.get('id') in priority else 99)

# Nuvio/IPTV/Stremio labels de compatibilité plus explicites.
k['note'] = 'KDTIVI est d’abord IPTV : Live/TV via M3U, M3U8 ou Xtream. Nuvio est une intégration bêta Apple pour films/séries et profils. Stremio reste non confirmé.'

# Nettoyage de mentions étrangères dans les guides de toutes les applications.
foreign = {
    'Plex/Emby/Jellyfin pour KDTIVI': 'Plex, Emby ou Jellyfin',
    'Stremio Web/AltStore PAL': 'la source officielle de cette application',
    'AltStore PAL/Stremio': 'la méthode officielle de cette application',
}
for app in d.get('apps', {}).values():
    def scrub(v):
        if isinstance(v, dict):
            return {kk: scrub(vv) for kk,vv in v.items()}
        if isinstance(v, list): return [scrub(x) for x in v]
        if isinstance(v, str):
            for a,b in foreign.items(): v=v.replace(a,b)
        return v
    # avoid re-cleaning metadata keys
    app.update(scrub(app))

d['generated_at'] = '2026-11-11T00:20:00+00:00'
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('normalized', len(d['apps']), 'apps')
