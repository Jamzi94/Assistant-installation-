import json
from pathlib import Path
p=Path('/home/ubuntu/installv57_audit/data/site-data.json')
d=json.loads(p.read_text())
A=d['apps']

def replace_all(obj, old, new):
    if isinstance(obj, dict):
        for k,v in obj.items(): obj[k]=replace_all(v,old,new)
    elif isinstance(obj,list):
        obj=[replace_all(v,old,new) for v in obj]
    elif isinstance(obj,str): return obj.replace(old,new)
    return obj

def set_text(appid, section, dev, mid, text):
    for x in A[appid].get(section,{}).get(dev,[]):
        if x.get('id')==mid:
            if 'text' in x: x['text']=text
            elif x.get('steps'):
                x['steps'][0]['body']=text
            return True
    return False

# Alder : compte Stremio/debrid uniquement, sans comparaison Nuvio.
for dev in ('android_tv','fire_tv'):
    set_text('alder','troubleshooting',dev,'account','🔑 Connexion refusée ?\n\nUtilise le compte demandé par Alder et vérifie les identifiants affichés par l’application. Alder ne remplace pas le compte Stremio et ne fournit aucun accès IPTV. Ne partage pas ton mot de passe.')

# IPVIO : lecteur IPTV autonome, aucun serveur média étranger dans le dépannage.
for dev in ('android_tv','fire_tv'):
    set_text('ipvio_stream','troubleshooting',dev,'account','🔑 Source refusée ?\n\nIPVIO Stream ne fournit aucun compte ni aucune chaîne. Vérifie uniquement l’URL, les identifiants Xtream, la playlist M3U ou les paramètres Stalker fournis par ton service autorisé.')

# Nyx : Xtream uniquement et aucun compte Nuvio/Stremio dans le dépannage.
for dev in ('android_phone','android_tablet','android_tv','windows'):
    set_text('nyxplayer','troubleshooting',dev,'account','🔑 Connexion refusée ?\n\nNyx Player demande le compte Nyx si la version l’affiche, puis les identifiants Xtream de ta source. Vérifie les champs dans Nyx et ne partage pas tes identifiants.')
    for x in A['nyxplayer'].get('install',{}).get(dev,[]):
        if x.get('id')=='developer':
            for s in x.get('steps',[]):
                s['body']=s.get('body','').replace(' Fire TV n’est pas confirmé par l’éditeur; n’utilise pas ce guide pour Fire TV.','')

# Fjord : dépannage Apple/macOS propre, sans AltStore, Stremio ou Nuvio.
for dev in ('iphone','ipad','apple_tv','mac'):
    set_text('fjordplayer','troubleshooting',dev,'account','🔑 Accès refusé ?\n\nFjord Player ne fournit ni compte, ni abonnement, ni chaînes. Vérifie uniquement les informations demandées par la source IPTV que tu as choisie et les autorisations de l’application.')
    set_text('fjordplayer','troubleshooting',dev,'download','⬇️ Téléchargement impossible ?\n\nVérifie la connexion, l’espace libre, la version du système et la disponibilité de l’application dans la boutique de cet appareil.')
    set_text('fjordplayer','troubleshooting',dev,'install','🍎 Installation refusée ?\n\nVérifie la version minimale du système, les restrictions de l’appareil et l’espace disponible. Utilise uniquement la fiche officielle de la boutique.')

# Stremio : supprimer le renvoi KDTIVI dans le parcours tvOS.
for x in A['stremio'].get('install',{}).get('apple_tv',[]):
    for s in x.get('steps',[]): s['body']=s.get('body','').replace(' et reviens choisir KDTIVI si ton appareil est compatible.','')

# KDTIVI : ses branches de dépannage Apple ne doivent pas ouvrir un tutoriel Stremio/AltStore.
for dev in ('apple_tv','iphone','ipad'):
    set_text('kdtivi','troubleshooting',dev,'download','⬇️ Téléchargement impossible ?\n\nVérifie la boutique officielle de l’appareil, l’espace disponible et la connexion. Pour iPhone/iPad, utilise uniquement la fiche KDTIVI officielle ou la méthode Apple validée dans ce guide.')
    set_text('kdtivi','troubleshooting',dev,'install','🍎 Installation refusée ?\n\nVérifie la version du système, les restrictions de l’appareil et la boutique officielle. N’installe pas un APK Android sur un appareil Apple.')
    set_text('kdtivi','troubleshooting',dev,'altstore','🍎 Installation Apple avancée\n\nCette branche concerne uniquement une installation Apple explicitement proposée par KDTIVI. Si elle n’apparaît pas dans ta version, reviens à la boutique officielle. Ne mélange pas cette branche avec un compte Nuvio ou Stremio.')

# Nettoyage de formulations génériques résiduelles dans ces applications.
for aid in ('alder','ipvio_stream','fjordplayer','nyxplayer'):
    replace_all(A[aid],'dans ce application','dans cette application')
    replace_all(A[aid],'dans cette application application','dans cette application')

d['generated_at']='2026-11-11T00:32:00+00:00'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('pass1 deep text cleanup applied')
