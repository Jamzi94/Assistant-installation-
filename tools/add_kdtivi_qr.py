import json
from pathlib import Path
from datetime import datetime, timezone
p=Path(__file__).resolve().parents[1] / 'data' / 'site-data.json'
d=json.loads(p.read_text())
k=d['apps']['kdtivi']

def s(title, body, url=None):
    x={'title':title,'body':body,'links':[]}
    if url: x['url']=url
    return x

def pairing(device):
    name=d['devices'][device]['name'].split(' ',1)[-1]
    return {'id':'qr_pairing','label':'📷 QR / associer KDTIVI et gérer à distance','steps':[
        s('Affiche le QR ou le code de jumelage',f'Sur {name.lower()}, ouvre Paramètres → Sync ou choisis Dashboard Login si cette option est proposée. KDTIVI affiche alors un QR ou un code de jumelage.'),
        s('Associe l’appareil depuis le téléphone ou le web','Scanne le QR avec ton téléphone ou ouvre le dashboard KDTIVI et choisis Associer un appareil. Saisis le code affiché si le dashboard le demande.', 'https://kdtapps.com/dashboard'),
        s('Gère les playlists et les profils','Depuis l’application téléphone ou le dashboard, ajoute ou modifie tes playlists, serveurs, profils et réglages. Les changements se synchronisent vers les appareils associés.', 'https://kdtapps.com/kdtivi'),
        s('Ne confonds pas les comptes','Ce QR associe l’appareil à ton compte KDTIVI. Il ne connecte pas un compte Nuvio ou Stremio et le code n’est pas documenté comme un code à usage unique.')
    ]}

def management(device):
    name=d['devices'][device]['name'].split(' ',1)[-1]
    return {'id':'dashboard','label':'🖥️ Gérer depuis le téléphone ou le web','steps':[
        s('Ouvre le dashboard KDTIVI','Connecte-toi au dashboard KDTIVI depuis un navigateur ou l’application téléphone.', 'https://kdtapps.com/dashboard'),
        s('Ajoute ou modifie tes sources',f'Gère les playlists, serveurs et profils sans saisir les informations sur {name.lower()}. Utilise uniquement tes propres accès autorisés.'),
        s('Vérifie la synchronisation','Retourne dans KDTIVI et ouvre Paramètres → Sync si l’option existe. Vérifie que les changements apparaissent sur l’appareil associé.'),
        s('Sépare IPTV, Nuvio et Stremio','Le dashboard gère le compte KDTIVI. Il ne prouve pas une connexion QR à Nuvio ou à un compte Stremio.')
    ]}

for dev, options in k['configure'].items():
    by={x['id']:x for x in options}
    if dev in {'android_tv','apple_tv','android_phone','iphone'}:
        by['qr_pairing']=pairing(dev)
    elif dev in {'android_tablet','ipad'}:
        by['dashboard']=management(dev)
    elif dev=='fire_tv':
        # Fire TV reste conditionnel : la source officielle ne documente pas QR/Sync séparément.
        by['dashboard']={'id':'dashboard','label':'🖥️ Dashboard KDTIVI (si l’appareil est associé)','steps':[
            s('Vérifie l’association Fire TV','KDTIVI distribue une version Fire TV, mais le QR et Sync ne sont pas documentés séparément pour Fire OS. N’utilise ce guide que si l’option apparaît dans ta version.'),
            s('Associe uniquement si un QR ou un code apparaît','Si KDTIVI affiche un QR ou un code, utilise le dashboard KDTIVI. Sinon arrête ce parcours et configure la source dans l’application.', 'https://kdtapps.com/dashboard'),
            s('Ne force pas la compatibilité','Vega OS et les appareils Fire non compatibles ne doivent pas suivre ce parcours. Le pairing n’est pas confirmé pour tous les modèles Fire TV.')
        ]}
    priority=['profiles','qr_pairing','dashboard','nuvio_media','iptv_live','m3u','xtream','general','library','addons','unsure']
    k['configure'][dev]=sorted(by.values(),key=lambda x: priority.index(x['id']) if x['id'] in priority else 99)

k['integration_notes']['qr'] = 'QR/code confirmé pour associer une TV ou Apple TV au compte KDTIVI et gérer playlists/profils depuis le dashboard. Aucun QR Nuvio ou Stremio confirmé.'
d['generated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('KDTIVI QR guides added')
