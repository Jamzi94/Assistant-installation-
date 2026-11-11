import json, re
from pathlib import Path
p=Path('/home/ubuntu/installv57_audit/data/site-data.json')
d=json.loads(p.read_text())

# Helpers

def walk(v, fn):
    if isinstance(v, dict): return {k: walk(x, fn) for k,x in v.items()}
    if isinstance(v, list): return [walk(x, fn) for x in v]
    return fn(v)

def text_clean(s):
    if not isinstance(s,str): return s
    replacements={
      'Plex/Emby/Jellyfin pour KDTIVI':'Plex, Emby ou Jellyfin',
      'Nuvio, Stremio et KDTIVI':'Nuvio, Stremio et cette application',
      'Nuvio et KDTIVI':'Nuvio et cette application',
      'KDTIVI/Plex/Emby/Jellyfin':'Plex, Emby ou Jellyfin',
      'KDTIVI / Plex / Emby / Jellyfin':'Plex, Emby ou Jellyfin',
      'Stremio Web/AltStore PAL':'la méthode officielle de cette application',
      'AltStore PAL/Stremio':'la méthode officielle de cette application',
      'dans Telegram':'dans un espace public',
      'dans le bot':'dans l’application',
      'dans le chatbot':'dans l’application',
      'chatbot':'application',
      'Chatbot':'application',
      'Telegram':'messagerie',
    }
    for a,b in replacements.items(): s=s.replace(a,b)
    # phrases de guidage trop vagues ou répétitives
    s=s.replace('téléphone, tablette ou box Android TV','appareil sélectionné')
    s=s.replace('Sur ton téléphone ou ordinateur','Sur cet appareil')
    s=s.replace('Sur le téléphone ou la tablette','Sur cet appareil')
    s=s.replace('sur ton téléphone ou ordinateur','sur cet appareil')
    return re.sub(r'\n{3,}','\n\n',s).strip()

d=walk(d,text_clean)

# Platform support déclaratif. Les statuts prudents évitent de transformer une revendication éditeur en test réel.
def support(status, url, note, checked='2026-11-11'):
    return {'status':status,'checked_on':checked,'evidence_url':url,'note':note}

apps=d['apps']
apps['nuvio_mobile']['platform_support']={
 'android_phone':support('confirmed','https://play.google.com/store/apps/details?id=com.nuvio.app','Android 7+ ; utiliser Google Play en priorité et vérifier l’architecture pour l’APK.'),
 'android_tablet':support('confirmed','https://play.google.com/store/apps/details?id=com.nuvio.app','Android 7+ ; interface tablette à vérifier selon la version.'),
 'iphone':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioMobile/releases','IPA/source Nuvio publiée ; vérifier iOS 16.1 minimum et renouvellement AltStore/SideStore.'),
 'ipad':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioMobile/releases','IPA/source Nuvio publiée ; vérifier iPadOS 16.1 minimum et compatibilité iPad.')
}
apps['nuvio_desktop']['platform_support']={
 'windows':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioDesktop/releases','Alpha Windows : utiliser uniquement l’asset Windows publié dans la release.'),
 'mac':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioDesktop/releases','Alpha macOS : vérifier Intel/Apple Silicon et l’asset réellement publié.'),
 'linux':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioDesktop/releases','Alpha Linux : vérifier le format réellement publié avant installation.')
}
apps['nuvio_smart']['platform_support']={
 'samsung_tv':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioTVSmart-Installer','Tizen : capacités différentes selon Tizen 4, 5 et 6+ ; installation via l’installateur officiel.'),
 'lg_tv':support('publisher_claim_unverified','https://github.com/NuvioMedia/NuvioTVSmart-Installer','webOS 5+ : Developer Mode, Key Server et IPK requis ; vérifier le modèle.')
}
apps['nuvio_plus_tv']['platform_support']={
 'android_tv':support('publisher_claim_unverified','https://github.com/homelessbrian/NuvioPlusIPTV','Fork tiers : Android TV revendiqué ; vérifier la release et les menus affichés.'),
 'fire_tv':support('publisher_claim_unverified','https://github.com/homelessbrian/NuvioPlusIPTV','Fire OS 6+ revendiqué mais non validé sur chaque modèle ; exclure Vega OS et Fire TV Stick 4K Select.')
}
apps['nuvio_plus_mobile']['platform_support']={
 'android_phone':support('publisher_claim_unverified','https://github.com/homelessbrian/NuvioPlusIPTV','Android 7+ ; APK tiers, variantes arm64-v8a, armeabi-v7a et x86_64.'),
 'android_tablet':support('publisher_claim_unverified','https://github.com/homelessbrian/NuvioPlusIPTV','Android 7+ ; vérifier l’architecture et l’interface tablette.')
}
apps['ipvio_stream']['platform_support']={
 'android_tv':support('publisher_claim_unverified','https://github.com/Emrodev/IPVIO-Stream','Android TV/Google TV revendiqué ; vérifier l’asset et les menus de la build.'),
 'fire_tv':support('publisher_claim_unverified','https://github.com/Emrodev/IPVIO-Stream','Fire TV revendiqué mais non testé ici ; interrompre si Vega OS.')
}
apps['fjordplayer']['platform_support']={
 'iphone':support('publisher_claim_unverified','https://apps.apple.com/','iOS 17+ à vérifier dans la fiche App Store.'),
 'ipad':support('publisher_claim_unverified','https://apps.apple.com/','iPadOS 17+ à vérifier dans la fiche App Store.'),
 'apple_tv':support('publisher_claim_unverified','https://apps.apple.com/','tvOS 17+ à vérifier dans la fiche Apple TV.'),
 'mac':support('publisher_claim_unverified','https://apps.apple.com/','macOS 14+ à vérifier dans le Mac App Store.')
}
apps['nyxplayer']['platform_support']={
 'android_phone':support('publisher_claim_unverified','https://github.com/','Android téléphone : vérifier la release APK.'),
 'android_tablet':support('publisher_claim_unverified','https://github.com/','Android tablette : vérifier l’architecture et la release.'),
 'android_tv':support('publisher_claim_unverified','https://github.com/','Android TV non confirmé par une fiche dédiée ; ne pas promettre la compatibilité.'),
 'windows':support('publisher_claim_unverified','https://github.com/','Windows x64 : vérifier l’asset exact et son intégrité.')
}

# Corrections d’intégration et de portée.
apps['nuvio_tv']['integrations']=['nuvio']
apps['nuvio_tv']['integration_notes']={'nuvio':'Compte Nuvio et extensions compatibles Nuvio. Pas d’IPTV M3U/Xtream confirmé. QR de compte et gestion d’extensions par téléphone documentés sur Android TV.'}
apps['nuvio_mobile']['integrations']=['nuvio']
apps['nuvio_mobile']['integration_notes']={'nuvio':'Compte et extensions Nuvio uniquement. Pas d’IPTV M3U/Xtream ni Stremio confirmés.'}
apps['nuvio_desktop']['integrations']=['nuvio']
apps['nuvio_desktop']['integration_notes']={'nuvio':'Alpha desktop Nuvio. IPTV, M3U, Xtream et Stremio non confirmés.'}
apps['nuvio_smart']['integrations']=['nuvio']
apps['nuvio_smart']['integration_notes']={'nuvio':'Nuvio Smart TV sur Tizen/webOS. IPTV M3U/Xtream et Stremio non confirmés.'}
apps['nuvio_plus_tv']['publisher_type']='third_party'
apps['nuvio_plus_mobile']['publisher_type']='third_party'
apps['nuvio_plus_tv']['integrations']=['iptv','nuvio']
apps['nuvio_plus_mobile']['integrations']=['iptv','nuvio']
apps['stremio']['integrations']=['stremio']
apps['stremio']['integration_notes']={'stremio':'Compte et extensions Stremio. Aucune intégration native Nuvio ou IPTV M3U/Xtream confirmée.'}
apps['alder']['integrations']=['stremio']
apps['alder']['integration_notes']={'stremio':'Client tiers Stremio : compte, addons et service debrid compatible. Pas de Nuvio ou IPTV M3U/Xtream natif.'}
apps['ipvio_stream']['integrations']=['iptv']
apps['ipvio_stream']['integration_notes']={'iptv':'M3U, Xtream et portail Stalker revendiqués par le README ; libellés UI à vérifier dans la build.'}
apps['fjordplayer']['integrations']=['iptv']
apps['fjordplayer']['integration_notes']={'iptv':'M3U/M3U8 et Xtream déclarés ; chemins de menus à confirmer par appareil.'}
apps['nyxplayer']['integrations']=['iptv']
apps['nyxplayer']['integration_notes']={'iptv':'Xtream est le seul parcours actif confirmé. M3U, Nuvio, Stremio et extensions ne sont pas confirmés.'}

# Nettoyage des méthodes étrangères et des doublons les plus problématiques.
for appid in ('stremio','alder','ipvio_stream','fjordplayer','nyxplayer'):
    app=apps[appid]
    for key in ('install','configure','troubleshooting'):
        for dev,items in app.get(key,{}).items():
            for item in items:
                for field in ('label','text'):
                    if field in item and isinstance(item[field],str):
                        item[field]=text_clean(item[field])
            # Retirer les branches manifestement étrangères par identifiant.
            if appid=='nyxplayer':
                app[key][dev]=[x for x in items if x.get('id') not in {'nuvio_login','nuvio-addons','nuvio-addon_url','stremio','m3u'}]
            if appid=='fjordplayer':
                app[key][dev]=[x for x in items if x.get('id') not in {'altstore','stremio','apk'}]

# Nuvio Mobile : canaux non prouvés retirés des liens de distribution.
for dev in ('android_phone','android_tablet'):
    links=apps['nuvio_mobile'].get('distribution_links',{}).get(dev,[])
    apps['nuvio_mobile'].setdefault('distribution_links',{})[dev]=[
      pair for pair in links if not any(term in pair[0].lower() for term in ('dropbox','downloader'))
    ]

# Nuvio TV : ne pas afficher Fire OS dans les textes Android TV.
for item in apps['nuvio_tv'].get('troubleshooting',{}).get('android_tv',[]):
    if item.get('id')=='downloader':
        item['text']='📥 Downloader sur Android TV\n\nOuvre Google Play, installe Downloader by AFTVnews, puis ouvre-le. N’utilise pas Amazon Appstore : ce parcours est réservé à Fire OS.'
    if item.get('id')=='account':
        item['text']='🔑 Connexion Nuvio\n\nUtilise le QR de compte documenté par Nuvio. La saisie e-mail dépend de la version. Nuvio TV ne confirme pas une source IPTV M3U/Xtream native.'

# Titres d’options plus honnêtes.
apps['nuvio_plus_tv']['note']='Fork tiers Nuvio + IPTV : Live/TV via M3U, Xtream et EPG ; compte Nuvio séparé si la build l’affiche.'
apps['nuvio_plus_mobile']['note']='Fork tiers Nuvio + IPTV pour Android : connexion Nuvio, puis Live/TV via M3U, Xtream et EPG.'
apps['stremio']['note']='Stremio officiel : compte et extensions Stremio. Pas un lecteur IPTV M3U/Xtream natif.'
apps['nyxplayer']['note']='Lecteur IPTV : parcours Xtream confirmé ; les autres sources restent non confirmées.'

# Re-tri après suppression et corrections.
def key(m):
    mid=m.get('id','').lower(); lab=m.get('label','').lower()
    if 'app_store' in mid or 'store' in lab or 'boutique' in lab or 'google play' in lab: return 0
    if mid in {'official','developer'} or 'officiel' in lab or 'github' in lab: return 1
    if 'downloader' in mid or 'code' in lab: return 2
    return 3
for app in apps.values():
    for dev,items in app.get('install',{}).items(): items.sort(key=key)

d['generated_at']='2026-11-11T00:28:00+00:00'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('exhaustive corrections applied')
