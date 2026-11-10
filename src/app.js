const DATA_URL = new URL('../data/site-data.json', import.meta.url);
const VALID_TABS = new Set(['overview', 'install', 'configure', 'help']);
const appRoot = document.querySelector('#app-detail');
const catalogRoot = document.querySelector('#catalog-list');
const pickerRoot = document.querySelector('#device-picker');
const toast = document.querySelector('#toast');
const announcer = document.querySelector('#status-announcer');
const errorAnnouncer = document.querySelector('#error-announcer');
const loadingState = document.querySelector('#loading-state');

let data;
let serviceFilter = '';
let searchTerm = '';
let toastTimer;
let state = readUrlState();
serviceFilter = state.service || '';
searchTerm = state.q || '';

const LOCAL_APP_ICONS = {
  nuvio_tv: './assets/app-icons/nuvio.png', nuvio_mobile: './assets/app-icons/nuvio.png',
  nuvio_desktop: './assets/app-icons/nuvio.png', nuvio_smart: './assets/app-icons/nuvio.png',
  stremio: './assets/app-icons/stremio.png', kdtivi: './assets/app-icons/kdtivi.png',
  fjordplayer: './assets/app-icons/fjordplayer.svg', nyxplayer: './assets/app-icons/nyxplayer.png',
};
const APP_ACCENTS = ['#183c36', '#263d62', '#452b58', '#543527', '#314b39', '#222d40'];

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function el(tag, className = '', text = '') {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function readUrlState() {
  const query = new URLSearchParams(window.location.search);
  const tab = query.get('tab') || 'overview';
  return {
    device: query.get('device') || '',
    app: query.get('app') || '',
    tab: VALID_TABS.has(tab) ? tab : 'overview',
    method: query.get('method') || '',
    config: query.get('config') || '',
    step: Math.max(0, Number.parseInt(query.get('step') || '0', 10) || 0),
    completed: query.get('done') === '1',
    service: query.get('service') || '',
    q: query.get('q') || '',
  };
}

function syncUrl(push = true) {
  const query = new URLSearchParams();
  if (state.device) query.set('device', state.device);
  if (state.app) query.set('app', state.app);
  if (state.app && state.tab !== 'overview') query.set('tab', state.tab);
  if (state.method && state.tab === 'install') query.set('method', state.method);
  if (state.config && state.tab === 'configure') query.set('config', state.config);
  if (state.step > 0 && (state.tab === 'install' || state.tab === 'configure')) query.set('step', String(state.step));
  if (state.completed && (state.tab === 'install' || state.tab === 'configure')) query.set('done', '1');
  if (state.service) query.set('service', state.service);
  if (state.q) query.set('q', state.q);
  const next = `${window.location.pathname}${query.size ? `?${query}` : ''}`;
  if (next === `${window.location.pathname}${window.location.search}`) return;
  if (push) window.history.pushState({}, '', next);
  else window.history.replaceState({}, '', next);
}

function setState(changes, { push = true, scroll = false } = {}) {
  state = { ...state, ...changes };
  if (Object.prototype.hasOwnProperty.call(changes, 'service')) serviceFilter = changes.service || '';
  if (Object.prototype.hasOwnProperty.call(changes, 'q')) searchTerm = changes.q || '';
  if (data) normalizeState();
  saveLastGuide();
  syncUrl(push);
  render();
  if (scroll) {
    window.setTimeout(() => {
      const target = state.app ? appRoot : document.querySelector('#applications');
      target?.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
      if (state.app) $('#detail-title')?.focus({ preventScroll: true });
    }, 0);
  }
}

function normalizeState() {
  if (state.device && !data.devices[state.device]) state.device = '';
  if (state.app) {
    const app = data.apps[state.app];
    if (!app || !app.devices.includes(state.device)) state.app = '';
  }
  if (!VALID_TABS.has(state.tab)) state.tab = 'overview';
  if (!state.app) {
    state.tab = 'overview';
    state.method = '';
    state.config = '';
    state.step = 0;
    state.completed = false;
    return;
  }
  const app = data.apps[state.app];
  const methods = app.install[state.device] || [];
  if (!methods.some((m) => m.id === state.method)) state.method = methods[0]?.id || '';
  const configs = app.configure[state.device] || [];
  if (!configs.some((c) => c.id === state.config)) state.config = configs[0]?.id || '';
  const current = state.tab === 'configure'
    ? configs.find((c) => c.id === state.config)
    : methods.find((m) => m.id === state.method);
  const max = current?.steps?.length ? current.steps.length - 1 : 0;
  state.step = Math.min(Math.max(0, state.step), max);
  if (state.completed && state.step !== max) state.completed = false;
}

function reducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || false;
}

function safeHttps(raw) {
  if (!raw || typeof raw !== 'string') return null;
  try {
    const url = new URL(raw, window.location.href);
    return url.protocol === 'https:' ? url.href : null;
  } catch {
    return null;
  }
}

function classifyLink(raw, app = null) {
  let host = '';
  try { host = new URL(raw).hostname.toLowerCase(); } catch { /* no-op */ }
  if (host.includes('dropbox.com') || host.endsWith('dropboxusercontent.com')) return { label: 'Miroir Dropbox de l’administrateur', css: 'mirror' };
  if (host.includes('aftv.news') || host.includes('aftvnews.com')) return { label: 'Raccourci AFTV', css: 'aftv' };
  if (host === 'play.google.com' || host === 'apps.apple.com' || host.endsWith('microsoft.com')) return { label: 'Boutique officielle', css: 'official' };
  if (host === 'github.com' || host.endsWith('.github.io')) {
    return ['third_party', 'independent'].includes(app?.publisher_type)
      ? { label: 'Projet tiers / releases', css: 'third' }
      : { label: 'Dépôt / releases éditeur', css: 'official' };
  }
  if (['third_party', 'independent'].includes(app?.publisher_type)) return { label: 'Projet indépendant', css: 'third' };
  return { label: 'Site de l’éditeur', css: 'official' };
}

function addExternalLink(parent, label, raw, app = null, { compact = false } = {}) {
  const href = safeHttps(raw);
  if (!href) return;
  const type = classifyLink(href, app);
  const link = el('a', `${compact ? 'outbound-link' : 'action-link'} source-${type.css}`);
  link.href = href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.referrerPolicy = 'no-referrer';
  link.append(document.createTextNode(label || type.label));
  if (compact) {
    const badge = el('small', '', type.label);
    link.append(badge);
  }
  parent.append(link);
}

function addBadge(parent, label, extraClass = '') {
  if (!label) return;
  const badge = el('span', `badge ${extraClass}`.trim(), label);
  parent.append(badge);
}

function groupInfo(groupId) {
  const groups = {
    tv: { title: 'Télévisions & boîtiers', icon: '▣' },
    computer: { title: 'Ordinateurs', icon: '⌘' },
    mobile: { title: 'Téléphones & tablettes', icon: '▤' },
  };
  const fallback = data.device_groups[groupId] || groupId;
  return groups[groupId] || { title: fallback.replace(/^[^A-Za-zÀ-ÿ]+\s*/, ''), icon: '•' };
}

function renderDevicePicker() {
  pickerRoot.replaceChildren();
  const groups = new Map();
  for (const [deviceId, device] of Object.entries(data.devices)) {
    const groupId = device.group || 'other';
    if (!groups.has(groupId)) groups.set(groupId, []);
    groups.get(groupId).push([deviceId, device]);
  }
  for (const [groupId, devices] of groups) {
    const section = el('div', 'device-group');
    const info = groupInfo(groupId);
    const title = el('h3', 'device-group-title');
    title.append(el('span', '', info.icon), document.createTextNode(info.title));
    section.append(title);
    const options = el('div', 'device-options');
    for (const [deviceId, device] of devices) {
      const button = el('button', 'device-option', device.name);
      button.type = 'button';
      button.dataset.action = 'select-device';
      button.dataset.device = deviceId;
      button.setAttribute('aria-pressed', String(state.device === deviceId));
      options.append(button);
    }
    section.append(options);
    pickerRoot.append(section);
  }

  const help = el('button', 'device-help-button');
  help.type = 'button';
  help.dataset.action = 'device-help';
  help.append(el('span', 'device-help-icon', '?'), document.createTextNode('Je ne sais pas quel système utilise mon appareil'));
  pickerRoot.append(help);

  const callout = $('#device-callout');
  callout.replaceChildren();
  if (state.device === 'fire_vega') {
    callout.hidden = false;
    callout.append(el('strong', '', 'Vega OS n’est pas Fire OS / Android.'), document.createTextNode('Le catalogue ne propose pas de méthode de sideload Android pour cet appareil. Consultez l’Amazon Appstore de votre téléviseur et les informations officielles du fabricant; n’installez pas un APK Android.'));
  } else if (state.device) {
    callout.hidden = false;
    const name = data.devices[state.device]?.name || 'Cet appareil';
    callout.append(el('strong', '', name), document.createTextNode('Les menus peuvent varier selon le modèle, la région, la version du système et de l’application. Une compatibilité indiquée ne constitue pas un test sur chaque modèle.'));
  } else {
    callout.hidden = true;
  }
}

function normalizeText(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function renderCatalogControls() {
  const controls = $('#catalog-controls');
  controls.replaceChildren();
  controls.hidden = !state.device;
  if (!state.device) return;

  const filters = el('div', 'filter-row');
  const all = el('button', 'filter-button', 'Toutes les catégories');
  all.type = 'button';
  all.dataset.action = 'filter-service';
  all.dataset.service = 'all';
  all.setAttribute('aria-pressed', String(!serviceFilter));
  filters.append(all);
  for (const [serviceId, label] of Object.entries(data.services)) {
    const button = el('button', 'filter-button', label.replace(/^[^A-Za-zÀ-ÿ]+\s*/, ''));
    button.type = 'button';
    button.dataset.action = 'filter-service';
    button.dataset.service = serviceId;
    button.setAttribute('aria-pressed', String(serviceFilter === serviceId));
    filters.append(button);
  }
  const searchWrap = el('label', 'search-wrap');
  searchWrap.append(el('span', '', '⌕'));
  const input = el('input', 'search-input');
  input.type = 'search';
  input.id = 'app-search';
  input.placeholder = 'Rechercher une application';
  input.setAttribute('aria-label', 'Rechercher une application compatible');
  input.value = searchTerm;
  searchWrap.append(input);
  controls.append(filters, searchWrap);
  input.addEventListener('input', () => {
    searchTerm = input.value;
    state.q = searchTerm;
    syncUrl(false);
    drawAppCards();
  });
}

function mediaFor(appId, deviceId) {
  return data.media?.[appId]?.[deviceId] || [];
}

function appVisual(appId, app, { large = false } = {}) {
  const media = mediaFor(appId, state.device);
  const poster = media.find((item) => item.kind !== 'logo' && item.url)?.url;
  const visual = el('div', `app-visual${large ? ' app-visual-large' : ''}`);
  visual.style.setProperty('--app-accent', APP_ACCENTS[Object.keys(data.apps).indexOf(appId) % APP_ACCENTS.length]);
  if (poster) visual.style.setProperty('--app-poster', `url("${poster.replaceAll('"', '%22')}")`);
  const icon = el('div', 'app-icon-large');
  const iconPath = LOCAL_APP_ICONS[appId];
  if (iconPath) {
    const img = el('img'); img.src = iconPath; img.alt = `Icône officielle de ${app.name}`; img.loading = large ? 'eager' : 'lazy';
    img.addEventListener('error', () => { icon.textContent = app.name.replace(/^[^A-Za-zÀ-ÿ]+/,'').slice(0, 2).toUpperCase(); }, { once: true });
    icon.append(img);
  } else {
    icon.append(el('span', 'icon-monogram', app.name.replace(/^[^A-Za-zÀ-ÿ]+/,'').slice(0, 2).toUpperCase()));
  }
  visual.append(icon);
  if (!iconPath) visual.append(el('span', 'icon-source-label', app.publisher_type === 'official' ? 'Éditeur' : 'Projet indépendant'));
  return visual;
}

function readLastGuide() {
  try { return JSON.parse(localStorage.getItem('assistant-installation:last-guide') || 'null'); } catch { return null; }
}

function saveLastGuide() {
  if (!state.app) return;
  try { localStorage.setItem('assistant-installation:last-guide', JSON.stringify({ app: state.app, device: state.device, tab: state.tab, step: state.step, completed: state.completed })); } catch { /* storage unavailable */ }
}

function renderSmartPanel() {
  const root = $('#smart-panel');
  if (!root || !data) return;
  root.replaceChildren();
  const inner = el('div', 'smart-panel-inner');
  const last = readLastGuide();
  if (!state.device) {
    inner.append(el('p', 'eyebrow', 'COCKPIT DE PARCOURS'));
    inner.append(el('h2', '', 'Commencez par une décision simple.'));
    inner.append(el('p', 'smart-panel-copy', 'L’interface se réorganise selon votre écran. Pas de compte, pas de chatbot à installer, pas de choix inutiles avant la première étape.'));
    const actions = el('div', 'smart-actions');
    const start = el('button', 'smart-action primary', 'Choisir mon appareil'); start.type='button'; start.dataset.action='scroll-to'; start.dataset.target='parcours';
    const explain = el('button', 'smart-action', 'Comprendre les sources'); explain.type='button'; explain.dataset.action='scroll-to'; explain.dataset.target='sources';
    actions.append(start, explain); inner.append(actions);
  } else if (!state.app) {
    const apps = Object.entries(data.apps).filter(([, app]) => app.devices.includes(state.device));
    const recommended = apps.find(([, app]) => app.publisher_type === 'official') || apps[0];
    inner.append(el('p', 'eyebrow', 'VOTRE ESPACE EST PRÊT'));
    inner.append(el('h2', '', `${apps.length} parcours pour ${data.devices[state.device]?.name || 'votre appareil'}`));
    inner.append(el('p', 'smart-panel-copy', 'Les cartes ci-dessous sont triées pour vous laisser voir rapidement les applications les plus crédibles et les méthodes les plus documentées.'));
    const actions = el('div', 'smart-actions');
    if (recommended) {
      const [id, app] = recommended;
      const open = el('button', 'smart-action primary', `Ouvrir la recommandation · ${app.name}`); open.type='button'; open.dataset.action='open-app'; open.dataset.app=id;
      actions.append(open);
    }
    const reset = el('button', 'smart-action', 'Changer d’appareil'); reset.type='button'; reset.dataset.action='scroll-to'; reset.dataset.target='parcours';
    actions.append(reset); inner.append(actions);
  } else {
    const app = data.apps[state.app];
    inner.append(el('p', 'eyebrow', 'VOTRE PARCOURS EN COURS'));
    inner.append(el('h2', '', app.name));
    inner.append(el('p', 'smart-panel-copy', state.completed ? 'Ce parcours est marqué comme terminé. Vous pouvez maintenant configurer l’application ou ouvrir le dépannage.' : `Étape ${state.step + 1} · ${state.tab === 'overview' ? 'présentation' : state.tab === 'install' ? 'installation' : state.tab === 'configure' ? 'configuration' : 'dépannage'}.`));
    const actions = el('div', 'smart-actions');
    const resume = el('button', 'smart-action primary', state.completed ? 'Revenir à ma fiche' : 'Reprendre le parcours'); resume.type='button'; resume.dataset.action='set-tab'; resume.dataset.tab=state.completed ? 'overview' : (state.tab === 'overview' ? 'install' : state.tab);
    const share = el('button', 'smart-action', 'Partager cette étape'); share.type='button'; share.dataset.action='copy-guide';
    actions.append(resume, share); inner.append(actions);
  }
  if (!state.app && last?.app && data.apps[last.app] && data.devices[last.device]) {
    const resume = el('button', 'resume-strip'); resume.type='button'; resume.dataset.action='resume-last'; resume.dataset.app=last.app; resume.dataset.device=last.device;
    resume.append(el('span', 'resume-kicker', 'REPRENDRE'), el('strong', '', data.apps[last.app].name), el('small', '', `Dernière étape consultée · ${data.devices[last.device].name}`), el('span', 'resume-arrow', '↗'));
    inner.append(resume);
  }
  root.append(inner);
}

function compatibilityBadge(app) {
  const evidence = app.platform_support?.[state.device];
  if (evidence?.status === 'publisher_claim_unverified') return ['Support déclaré, non testé ici', 'badge-caution'];
  if (evidence?.status === 'not_confirmed') return ['Compatibilité non confirmée', 'badge-caution'];
  if (app.publisher_type === 'third_party') return ['Application tierce', 'badge-third'];
  return ['Appareil présent au catalogue', ''];
}

function drawAppCards() {
  catalogRoot.replaceChildren();
  const summary = $('#catalog-summary');
  if (!state.device) {
    summary.textContent = 'Choisissez un appareil pour afficher les applications qui lui sont attribuées.';
    const empty = el('div', 'empty-state');
    empty.append(el('strong', '', 'Le filtre commence par l’appareil.'), document.createTextNode('Choisissez votre TV, téléphone ou ordinateur : seules les applications compatibles selon le catalogue s’afficheront.'));
    catalogRoot.append(empty);
    return;
  }
  if (state.device === 'fire_vega') {
    summary.textContent = 'Vega OS : aucun APK Android n’est proposé pour ce parcours.';
    const empty = el('div', 'empty-state');
    empty.append(el('strong', '', 'Aucune application du catalogue à installer en APK.'), document.createTextNode('Vega OS est différent de Fire OS. Vérifiez uniquement les applications disponibles dans l’Amazon Appstore de votre téléviseur.'));
    catalogRoot.append(empty);
    return;
  }

  const matches = Object.entries(data.apps).filter(([appId, app]) => {
    if (!app.devices.includes(state.device)) return false;
    if (serviceFilter && !(app.services || []).includes(serviceFilter)) return false;
    const q = normalizeText(searchTerm);
    return !q || normalizeText(`${app.name} ${app.note || ''} ${app.prerequisites || ''}`).includes(q);
  });
  const deviceName = data.devices[state.device]?.name || 'cet appareil';
  summary.textContent = `${matches.length} application${matches.length === 1 ? '' : 's'} attribuée${matches.length === 1 ? '' : 's'} à ${deviceName.replace(/^[^A-Za-zÀ-ÿ]+\s*/, '')}.`;
  if (!matches.length) {
    const empty = el('div', 'empty-state');
    empty.append(el('strong', '', searchTerm ? 'Aucun résultat.' : 'Rien dans cette catégorie pour cet appareil.'), document.createTextNode(searchTerm ? 'Essayez un autre nom ou effacez la recherche.' : 'Changez de catégorie ou sélectionnez un autre appareil.'));
    catalogRoot.append(empty);
    return;
  }

  for (const [appId, app] of matches) {
    const card = el('article', 'app-card');
    if (app.publisher_type === 'official' && (app.install[state.device] || []).length) {
      card.classList.add('is-recommended');
      card.append(el('span', 'recommendation-ribbon', 'Recommandée'));
    }
    card.dataset.action = 'open-app';
    card.dataset.app = appId;
    card.tabIndex = 0;
    card.setAttribute('role', 'link');
    card.setAttribute('aria-label', `Ouvrir la fiche ${app.name}`);
    card.append(appVisual(appId, app));
    const top = el('div', 'app-card-top');
    const copy = el('div');
    copy.append(el('h3', '', app.name));
    copy.append(el('p', '', app.note || app.access || 'Consultez la fiche avant installation.'));
    top.append(copy);
    const badges = el('div', 'badge-row');
    const [compatibility, compatibilityClass] = compatibilityBadge(app);
    addBadge(badges, compatibility, compatibilityClass);
    if (app.publisher_type === 'third_party') addBadge(badges, 'Projet indépendant', 'badge-third');
    if (/alpha/i.test(app.name) || /alpha/i.test(app.note || '')) addBadge(badges, 'Version alpha', 'badge-alpha');
    for (const service of app.services || []) addBadge(badges, data.services[service]?.replace(/^[^A-Za-zÀ-ÿ]+\s*/, '') || service);
    const foot = el('div', 'app-card-foot');
    foot.append(el('small', '', `${(app.install[state.device] || []).length} méthode${(app.install[state.device] || []).length === 1 ? '' : 's'} recensée${(app.install[state.device] || []).length === 1 ? '' : 's'}`));
    const open = el('button', 'text-button');
    open.type = 'button'; open.dataset.action = 'open-app'; open.dataset.app = appId;
    open.append(document.createTextNode('Ouvrir la fiche '), el('span', '', '→'));
    foot.append(open);
    card.append(top, badges, foot);
    catalogRoot.append(card);
  }
}

function renderCatalog() {
  renderCatalogControls();
  drawAppCards();
}

function makeBreadcrumb(app) {
  const row = el('div', 'detail-breadcrumb');
  const back = el('button', 'breadcrumb-button', 'Applications');
  back.type = 'button';
  back.dataset.action = 'close-app';
  row.append(back, document.createTextNode(' / '), document.createTextNode(data.devices[state.device]?.name || ''), document.createTextNode(' / '), document.createTextNode(app.name));
  return row;
}

function renderSourceLinks(parent, app) {
  const links = [];
  const add = (label, url) => {
    const href = safeHttps(url);
    if (!href || links.some((item) => item.href === href)) return;
    links.push({ label, href });
  };
  add('Site de l’application', app.site);
  add('Dépôt / source', app.source);
  const deviceLink = app.links?.[state.device];
  if (Array.isArray(deviceLink)) deviceLink.forEach((item) => add(item[0], item[1]));
  else add('Page pour cet appareil', deviceLink);
  add('Fiche Google Play', app.play_store);
  for (const [label, url] of app.distribution_links?.[state.device] || []) add(label, url);

  for (const item of links) {
    const line = el('div', 'action-line');
    const kind = classifyLink(item.href, app);
    line.append(el('span', 'link-label', kind.label));
    addExternalLink(line, item.label, item.href, app);
    parent.append(line);
  }
}

function renderDetail() {
  appRoot.replaceChildren();
  if (!state.app) {
    appRoot.hidden = true;
    return;
  }
  const app = data.apps[state.app];
  if (!app) { appRoot.hidden = true; return; }
  appRoot.hidden = false;
  const shell = el('div', 'detail-shell');
  const top = el('div', 'detail-top');
  top.append(appVisual(state.app, app, { large: true }));
  const copy = el('div');
  copy.append(makeBreadcrumb(app));
  const title = el('h2', 'detail-title', app.name);
  title.id = 'detail-title';
  title.tabIndex = -1;
  copy.append(title);
  copy.append(el('p', 'detail-summary', app.access || app.note || 'Consultez la source éditeur avant de continuer.'));
  const badges = el('div', 'detail-meta');
  const [compatibility, compatibilityClass] = compatibilityBadge(app);
  addBadge(badges, compatibility, compatibilityClass);
  addBadge(badges, app.publisher_type === 'third_party' ? 'Projet tiers — non affilié' : 'Application / source éditeur', app.publisher_type === 'third_party' ? 'badge-third' : '');
  for (const service of app.services || []) addBadge(badges, data.services[service]?.replace(/^[^A-Za-zÀ-ÿ]+\s*/, '') || service);
  copy.append(badges);
  const actions = el('div', 'detail-actions');
  renderSourceLinks(actions, app);
  top.append(copy, actions);
  shell.append(top);

  const evidence = app.platform_support?.[state.device];
  if (evidence?.note) {
    const caution = el('aside', 'caution-box');
    caution.setAttribute('role', 'note');
    const heading = evidence.status === 'publisher_claim_unverified' ? 'Réserve de compatibilité' : 'Compatibilité non confirmée';
    caution.append(el('strong', '', heading), document.createTextNode(evidence.note));
    if (evidence.evidence_url) addExternalLink(caution, 'Consulter la source citée', evidence.evidence_url, app, { compact: true });
    shell.append(caution);
  } else if (app.publisher_type === 'third_party') {
    const caution = el('aside', 'caution-box');
    caution.append(el('strong', '', 'Projet tiers.'), document.createTextNode('Ce logiciel n’est pas affilié à l’éditeur des services éventuellement associés. Vérifiez la provenance, la version, les permissions et les prérequis avant de l’installer.'));
    shell.append(caution);
  }
  if (app.downloader_code && (app.install[state.device] || []).some((m) => /downloader/i.test(m.id))) {
    const code = el('aside', 'caution-box');
    code.append(el('strong', '', `Code Downloader indiqué dans le catalogue : ${app.downloader_code}`), document.createTextNode(`${app.code_source_status || 'Statut de vérification non précisé.'} Un code peut rediriger vers un fichier dont la version évolue. Relisez la source et le nom du paquet avant de confirmer l’installation.`));
    shell.append(code);
  }
  if (app.prerequisites) {
    const prereq = el('p', 'detail-prereq');
    prereq.append(el('strong', '', 'Prérequis : '), document.createTextNode(app.prerequisites));
    shell.append(prereq);
  }

  const body = el('div', 'detail-body');
  const tabs = el('div', 'detail-tabs');
  tabs.setAttribute('role', 'tablist');
  tabs.setAttribute('aria-label', `Rubriques du guide ${app.name}`);
  tabs.setAttribute('aria-orientation', 'horizontal');
  const tabLabels = [
    ['overview', 'Présentation'], ['install', 'Installer'], ['configure', 'Configurer'], ['help', 'Dépannage'],
  ];
  for (const [tabId, label] of tabLabels) {
    const button = el('button', 'tab-button', label);
    button.type = 'button';
    button.id = `tab-${tabId}`;
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', String(state.tab === tabId));
    button.setAttribute('aria-controls', 'guide-pane');
    button.tabIndex = state.tab === tabId ? 0 : -1;
    button.dataset.action = 'set-tab';
    button.dataset.tab = tabId;
    tabs.append(button);
  }
  body.append(tabs);
  const pane = el('div', 'detail-pane');
  pane.id = 'guide-pane';
  pane.setAttribute('role', 'tabpanel');
  pane.setAttribute('aria-labelledby', `tab-${state.tab}`);
  if (state.tab === 'install') renderInstallPane(pane, app);
  else if (state.tab === 'configure') renderConfigurePane(pane, app);
  else if (state.tab === 'help') renderHelpPane(pane, app);
  else renderOverviewPane(pane, app);
  body.append(pane);
  shell.append(body);
  appRoot.append(shell);
}

function renderOverviewPane(pane, app) {
  const heading = el('div', 'pane-heading');
  heading.append(el('h3', '', 'Avant de commencer'));
  heading.append(el('p', '', 'Vérifiez que votre appareil, la source et le compte attendu correspondent à cette fiche.'));
  pane.append(heading);
  const details = el('div', 'overview-copy');
  details.append(el('p', '', app.note || 'Consultez la source de l’éditeur pour les informations récentes.'));
  if (app.prerequisites) details.append(el('p', '', `À préparer : ${app.prerequisites}`));
  details.append(el('p', '', 'Cette application ne fournit pas automatiquement de chaînes, d’abonnement ni de sources. N’ajoutez que des contenus et services auxquels vous êtes autorisé à accéder.'));
  pane.append(details);
  const methods = app.install[state.device] || [];
  if (methods.length) {
    const recommendation = el('aside', 'recommendation-card');
    recommendation.append(el('p', 'eyebrow', 'PARCOURS RECOMMANDÉ'));
    recommendation.append(el('h3', '', methods[0].label));
    recommendation.append(el('p', '', `${methods[0].steps?.length || 0} étapes guidées pour ${data.devices[state.device]?.name || 'cet appareil'}. Les autres méthodes restent accessibles depuis l’onglet Installer.`));
    const start = el('button', 'round-button primary', 'Commencer ce parcours →');
    start.type = 'button'; start.dataset.action = 'set-tab'; start.dataset.tab = 'install';
    recommendation.append(start);
    pane.append(recommendation);
  }
  appendMedia(pane, app);
  const shareRow = el('div', 'share-row');
  const share = el('button', 'round-button');
  share.type = 'button'; share.dataset.action = 'copy-guide'; share.textContent = 'Copier le lien de cette fiche';
  shareRow.append(share);
  pane.append(shareRow);
}

function renderInstallPane(pane, app) {
  const options = app.install[state.device] || [];
  const heading = el('div', 'pane-heading');
  heading.append(el('h3', '', 'Installation, pas à pas'));
  heading.append(el('p', '', 'Choisissez une méthode disponible dans le catalogue pour cet appareil. Les menus peuvent varier selon le modèle et la version de l’application.'));
  pane.append(heading);
  if (!options.length) {
    pane.append(el('div', 'empty-state', 'Aucune méthode d’installation n’est renseignée pour ce couple appareil–application.'));
    return;
  }
  if (options.length > 1) {
    const list = el('div', 'choice-list');
    for (const option of options) {
      const button = el('button', 'choice-button', option.label);
      button.type = 'button'; button.dataset.action = 'set-method'; button.dataset.method = option.id;
      button.setAttribute('aria-pressed', String(state.method === option.id));
      list.append(button);
    }
    pane.append(list);
  }
  const selected = options.find((option) => option.id === state.method) || options[0];
  renderGuidedSteps(pane, selected.steps, 'install');
  appendMedia(pane, app);
}

function renderConfigurePane(pane, app) {
  const options = app.configure[state.device] || [];
  const heading = el('div', 'pane-heading');
  heading.append(el('h3', '', 'Configuration pas à pas'));
  heading.append(el('p', '', 'Ajoutez uniquement vos propres accès. Les mots de passe, URL privées, adresses MAC et codes d’association ne doivent pas être partagés dans un chatbot.'));
  pane.append(heading);
  if (!options.length) {
    pane.append(el('div', 'empty-state', 'Aucun guide de configuration spécifique n’est renseigné pour ce couple appareil–application.'));
    return;
  }
  const label = el('label', 'config-select-label', 'Que souhaitez-vous configurer ?');
  const select = el('select', 'config-select');
  select.id = 'config-choice';
  for (const option of options) {
    const item = el('option', '', option.label);
    item.value = option.id;
    item.selected = state.config === option.id;
    select.append(item);
  }
  select.addEventListener('change', () => setState({ config: select.value, step: 0 }));
  label.append(select);
  pane.append(label);
  const selected = options.find((option) => option.id === state.config) || options[0];
  renderGuidedSteps(pane, selected.steps, 'configure');
  appendMedia(pane, app);
}

function renderGuidedSteps(parent, steps, kind) {
  if (!steps?.length) {
    parent.append(el('div', 'empty-state', 'Aucune étape de ce type n’est actuellement disponible.'));
    return;
  }
  const index = Math.min(state.step, steps.length - 1);
  const step = steps[index];
  if (state.completed) {
    const complete = el('section', 'completion-card');
    complete.append(el('div', 'completion-mark', '✓'));
    const copy = el('div', 'completion-copy');
    copy.append(el('p', 'eyebrow', kind === 'configure' ? 'CONFIGURATION TERMINÉE' : 'INSTALLATION TERMINÉE'));
    copy.append(el('h3', '', kind === 'configure' ? 'Vos réglages sont en place.' : 'L’application est installée et prête à être ouverte.'));
    copy.append(el('p', '', 'Si l’écran ne correspond pas à ce qui est indiqué, revenez à l’étape précédente plutôt que de forcer une installation ou de partager un accès privé.'));
    complete.append(copy);
    const actions = el('div', 'completion-actions');
    if (kind === 'install') {
      const configure = el('button', 'round-button primary', 'Configurer maintenant →');
      configure.type = 'button'; configure.dataset.action = 'continue-config';
      actions.append(configure);
    }
    const help = el('button', 'round-button', 'J’ai un problème');
    help.type = 'button'; help.dataset.action = 'open-help';
    const restart = el('button', 'text-button', 'Revoir depuis le début');
    restart.type = 'button'; restart.dataset.action = 'restart-guide';
    actions.append(help, restart);
    complete.append(actions);
    parent.append(complete);
    return;
  }
  const card = el('article', 'guide-card');
  card.setAttribute('aria-live', 'polite');
  const num = el('div', 'guide-number', String(index + 1).padStart(2, '0'));
  num.setAttribute('aria-hidden', 'true');
  const content = el('div', 'guide-content');
  content.append(el('h4', '', step.title || `Étape ${index + 1}`));
  content.append(el('p', '', step.body || 'Suivez les instructions affichées par l’application.'));
  if (step.image) {
    const figure = el('figure', 'step-visual');
    const image = el('img');
    image.src = step.image.startsWith('assets/') ? `./${step.image}` : step.image;
    image.alt = 'Illustration pédagogique de cette étape — pas une capture d’écran';
    image.loading = 'lazy';
    image.decoding = 'async';
    image.addEventListener('error', () => figure.replaceChildren(el('figcaption', 'media-fallback', 'Illustration temporairement indisponible')), { once: true });
    figure.append(image, el('figcaption', '', 'Illustration pédagogique — pas une capture d’écran'));
    content.append(figure);
  }
  card.append(num, content);
  parent.append(card);

  const progress = el('div', 'step-progress');
  progress.setAttribute('role', 'progressbar');
  progress.setAttribute('aria-label', `Progression du guide : étape ${index + 1} sur ${steps.length}`);
  progress.setAttribute('aria-valuemin', '1');
  progress.setAttribute('aria-valuemax', String(steps.length));
  progress.setAttribute('aria-valuenow', String(index + 1));
  for (let i = 0; i < steps.length; i += 1) {
    const segment = el('span', `progress-segment${i <= index ? ' active' : ''}`);
    segment.setAttribute('aria-hidden', 'true');
    progress.append(segment);
  }
  parent.append(progress);

  const actionLinks = el('div', 'step-links');
  const sourceApp = data.apps[state.app];
  if (step.url) addExternalLink(actionLinks, 'Ouvrir la page liée à cette étape', step.url, sourceApp, { compact: true });
  for (const [label, url] of step.links || []) addExternalLink(actionLinks, label, url, sourceApp, { compact: true });
  if (actionLinks.childNodes.length) parent.append(actionLinks);

  const nav = el('div', 'step-nav');
  nav.append(el('span', 'step-count', `Étape ${index + 1} sur ${steps.length}`));
  const buttons = el('div', 'nav-buttons');
  const prev = el('button', 'round-button', '← Précédente');
  prev.type = 'button'; prev.dataset.action = 'prev-step'; prev.disabled = index === 0;
  const next = el('button', 'round-button primary', index === steps.length - 1 ? 'Marquer comme terminé' : 'Suivante →');
  next.type = 'button'; next.dataset.action = 'next-step'; next.dataset.kind = kind;
  if (index === steps.length - 1) next.setAttribute('aria-label', 'Marquer le guide comme terminé');
  buttons.append(prev, next);
  nav.append(buttons);
  parent.append(nav);
}

function renderHelpPane(pane, app) {
  const heading = el('div', 'pane-heading');
  heading.append(el('h3', '', 'Que se passe-t-il ?'));
  heading.append(el('p', '', 'Conseils repris du parcours du bot. Commencez par choisir le problème qui ressemble le plus au vôtre.'));
  pane.append(heading);
  const issues = app.troubleshooting[state.device] || [];
  if (issues.length) {
    const list = el('div', 'troubleshoot-list');
    for (const issue of issues) {
      const details = el('details', 'issue-item');
      const summary = el('summary', '', issue.label);
      details.append(summary);
      details.append(el('div', 'issue-text', issue.text));
      if (issue.links?.length) {
        const links = el('div', 'issue-links');
        for (const [label, url] of issue.links) addExternalLink(links, label, url, app, { compact: true });
        details.append(links);
      }
      list.append(details);
    }
    pane.append(list);
  } else {
    const fallback = el('div', 'empty-state');
    fallback.append(el('strong', '', 'Aucun cas spécifique exporté pour cette combinaison.'), document.createTextNode('Vérifiez les prérequis, la compatibilité de votre modèle et la source du fichier téléchargé. Si une étape ne correspond pas à votre écran, arrêtez-vous et consultez la page de l’éditeur.'));
    pane.append(fallback);
  }
  const safety = el('aside', 'caution-box');
  safety.append(el('strong', '', 'Évitez les corrections risquées.'), document.createTextNode('Ne désactivez pas durablement les protections du système, ne partagez pas de mot de passe ou de code privé et n’installez pas un paquet prévu pour un autre appareil.'));
  pane.append(safety);
  appendMedia(pane, app);
}

function appendMedia(parent, app) {
  const items = mediaFor(state.app, state.device).filter((item) => item.kind !== 'logo');
  if (items.length) {
    const section = el('section', 'media-section');
    section.append(el('h3', '', 'Captures publiées par l’éditeur'));
    section.append(el('p', 'media-intro', 'Ces visuels illustrent l’interface communiquée par l’éditeur; ils ne prouvent ni la disponibilité actuelle de l’application, ni le fonctionnement sur votre modèle.'));
    const gallery = el('div', 'media-gallery');
    for (const item of items.slice(0, 8)) {
      const figure = el('figure', 'media-card');
      const preview = el('button', 'media-preview');
      preview.type = 'button'; preview.dataset.action = 'open-lightbox'; preview.dataset.image = item.url; preview.dataset.title = item.title || `Capture de ${app.name}`;
      preview.setAttribute('aria-label', `Agrandir ${item.title || `la capture de ${app.name}`}`);
      const image = el('img');
      image.src = item.url;
      image.alt = item.alt || item.title || `Capture éditeur de ${app.name}`;
      image.loading = 'lazy';
      image.referrerPolicy = 'no-referrer';
      image.addEventListener('error', () => {
        figure.replaceChildren(el('div', 'media-fallback', 'Visuel temporairement indisponible'));
      }, { once: true });
      preview.append(image, el('span', 'zoom-indicator', '↗'));
      const caption = el('figcaption');
      caption.append(el('strong', '', item.title || 'Capture éditeur'));
      const source = safeHttps(item.source || item.url);
      if (source) {
        const link = el('a', '', 'Source ↗');
        link.href = source; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.referrerPolicy = 'no-referrer';
        caption.append(link);
      }
      figure.append(preview, caption);
      gallery.append(figure);
    }
    section.append(gallery);
    parent.append(section);
  }

  const videos = (data.videos || []).filter((video) => (video.apps || []).includes(state.app) && (video.devices || []).includes(state.device));
  if (videos.length) {
    const section = el('section', 'media-section');
    section.append(el('h3', '', 'Vidéos associées'));
    section.append(el('p', 'media-intro', 'Les liens et métadonnées ont été contrôlés; le contenu complet des vidéos n’a pas été visionné. Les vidéos de créateurs tiers ne remplacent pas les instructions de l’éditeur.'));
    const list = el('div', 'video-list');
    for (const video of videos) list.append(makeVideoCard(video));
    section.append(list);
    if (data.video_verification_method) section.append(el('p', 'video-disclaimer', data.video_verification_method));
    parent.append(section);
  }
}

function makeVideoCard(video) {
  const card = el('article', 'video-card');
  const button = el('button', 'video-preview');
  button.type = 'button';
  button.dataset.action = 'load-video';
  button.dataset.video = video.id;
  button.setAttribute('aria-label', `Charger la vidéo : ${video.title}`);
  const videoId = youtubeId(video.url);
  if (videoId) {
    const image = el('img');
    image.src = `https://i.ytimg.com/vi/${encodeURIComponent(videoId)}/hqdefault.jpg`;
    image.alt = '';
    image.loading = 'lazy';
    image.referrerPolicy = 'no-referrer';
    image.addEventListener('error', () => { image.remove(); }, { once: true });
    button.append(image);
  }
  button.append(el('span', 'play-indicator', '▶'));
  const caption = el('div', 'video-caption');
  caption.append(el('h4', '', video.title));
  caption.append(el('p', '', `${video.creator || 'Source vidéo'}${video.published ? ` · ${video.published}` : ''}${video.lang ? ` · ${video.lang.toUpperCase()}` : ''}`));
  if (video.disclaimer) caption.append(el('p', '', video.disclaimer));
  addExternalLink(caption, 'Ouvrir sur YouTube', video.url, null);
  card.append(button, caption);
  return card;
}

function youtubeId(raw) {
  try {
    const url = new URL(raw);
    if (url.hostname.endsWith('youtu.be')) return url.pathname.slice(1).split('/')[0];
    if (url.searchParams.get('v')) return url.searchParams.get('v');
    const match = url.pathname.match(/\/(?:embed|shorts)\/([\w-]+)/);
    return match?.[1] || '';
  } catch { return ''; }
}

function loadVideo(videoId) {
  const video = (data.videos || []).find((item) => item.id === videoId);
  const id = video ? youtubeId(video.url) : '';
  if (!id) return;
  const button = $(`[data-action="load-video"][data-video="${CSS.escape(videoId)}"]`);
  if (!button) return;
  const iframe = el('iframe', 'video-frame');
  iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1`;
  iframe.title = video.title;
  iframe.loading = 'lazy';
  iframe.referrerPolicy = 'strict-origin-when-cross-origin';
  iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
  iframe.allowFullscreen = true;
  button.replaceWith(iframe);
}

function render() {
  if (!data) return;
  normalizeState();
  renderDevicePicker();
  renderSmartPanel();
  renderCatalog();
  renderDetail();
  requestAnimationFrame(() => observeRevealables());
  const footer = $('.site-footer p');
  const stamp = data.generated_at ? new Date(data.generated_at) : null;
  if (footer && stamp && !$('.data-stamp', footer)) {
    footer.append(document.createTextNode(' '));
    const small = el('small', 'data-stamp', `Données exportées le ${new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeZone: 'Europe/Paris' }).format(stamp)}.`);
    footer.append(small);
  }
}

let revealObserver;
function observeRevealables() {
  const nodes = $$('.device-group, .app-card, .detail-shell, .smart-panel-inner, .source-section, .media-card, .guide-card');
  if (!('IntersectionObserver' in window)) { nodes.forEach((node) => node.classList.add('is-visible')); return; }
  revealObserver?.disconnect();
  revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: .08, rootMargin: '0px 0px -30px' });
  nodes.forEach((node, index) => { node.style.setProperty('--reveal-delay', `${Math.min(index * 35, 240)}ms`); revealObserver.observe(node); });
}

function updateScrollProgress() {
  const bar = $('#scroll-progress');
  if (!bar) return;
  const max = document.documentElement.scrollHeight - window.innerHeight;
  bar.style.transform = `scaleX(${max > 0 ? Math.min(1, window.scrollY / max) : 0})`;
}

function enableMotionDesign() {
  if (reducedMotion() || !window.matchMedia?.('(hover: hover) and (pointer: fine)').matches) return;
  document.addEventListener('pointermove', (event) => {
    const card = event.target.closest?.('.app-card');
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - .5;
    const y = (event.clientY - rect.top) / rect.height - .5;
    card.style.setProperty('--tilt-x', `${(-y * 2.8).toFixed(2)}deg`);
    card.style.setProperty('--tilt-y', `${(x * 3.2).toFixed(2)}deg`);
    card.style.setProperty('--spot-x', `${(x * 100 + 50).toFixed(1)}%`);
    card.style.setProperty('--spot-y', `${(y * 100 + 50).toFixed(1)}%`);
  });
  document.addEventListener('pointerout', (event) => {
    const card = event.target.closest?.('.app-card');
    if (!card || card.contains(event.relatedTarget)) return;
    card.style.setProperty('--tilt-x', '0deg'); card.style.setProperty('--tilt-y', '0deg');
  });
  document.addEventListener('click', (event) => {
    const target = event.target.closest?.('.round-button, .smart-action, .filter-button, .device-option, .tab-button');
    if (!target || reducedMotion()) return;
    const ripple = el('span', 'motion-ripple');
    const rect = target.getBoundingClientRect();
    ripple.style.left = `${event.clientX - rect.left}px`;
    ripple.style.top = `${event.clientY - rect.top}px`;
    target.append(ripple);
    window.setTimeout(() => ripple.remove(), 520);
  });
}

enableMotionDesign();

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('show'), 2600);
}

function announce(message, { error = false } = {}) {
  const target = error ? errorAnnouncer : announcer;
  if (!target) return;
  target.textContent = '';
  window.setTimeout(() => { target.textContent = message; }, 20);
}

async function copyGuideLink() {
  syncUrl(false);
  try {
    await navigator.clipboard.writeText(window.location.href);
    showToast('Lien copié. Il s’ouvrira sur cette fiche et cette étape.');
  } catch {
    showToast('Le navigateur ne permet pas la copie automatique. Copiez le lien depuis la barre d’adresse.');
  }
}

function onClick(event) {
  const control = event.target.closest('[data-action]');
  if (!control) return;
  const action = control.dataset.action;
  if (action === 'select-device') {
    serviceFilter = ''; searchTerm = '';
    setState({ device: control.dataset.device, app: '', tab: 'overview', method: '', config: '', step: 0, completed: false, service: '', q: '' }, { scroll: true });
  } else if (action === 'device-help') {
    const callout = $('#device-callout');
    callout.hidden = false;
    callout.replaceChildren(
      el('strong', '', 'Comment reconnaître votre appareil ?'),
      document.createTextNode(' TV : ouvrez Paramètres → À propos. Samsung utilise généralement Tizen, LG webOS, Apple TV tvOS et Google TV/Chromecast Android TV. Sur mobile, consultez Réglages/Paramètres → À propos. Sur ordinateur, ouvrez Informations système.'),
      el('br'),
      document.createTextNode(' Si vous hésitez encore, choisissez le système indiqué sur l’écran d’accueil plutôt que l’appareil utilisé pour lire cette page.'),
    );
    callout.focus?.();
    announce('Aide pour identifier le système de votre appareil affichée.');
  } else if (action === 'scroll-to') {
    document.getElementById(control.dataset.target)?.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
  } else if (action === 'resume-last') {
    const last = readLastGuide();
    const app = data.apps[control.dataset.app];
    if (app) setState({ device: control.dataset.device, app: control.dataset.app, tab: last?.tab || 'install', method: app.install?.[control.dataset.device]?.[0]?.id || '', config: app.configure?.[control.dataset.device]?.[0]?.id || '', step: last?.step || 0, completed: Boolean(last?.completed) }, { scroll: true });
  } else if (action === 'open-app') {
    const appId = control.dataset.app;
    const app = data.apps[appId];
    setState({ app: appId, tab: 'overview', method: app?.install[state.device]?.[0]?.id || '', config: app?.configure[state.device]?.[0]?.id || '', step: 0, completed: false }, { scroll: true });
  } else if (action === 'close-app') {
    setState({ app: '', tab: 'overview', method: '', config: '', step: 0 }, { scroll: true });
  } else if (action === 'filter-service') {
    serviceFilter = control.dataset.service === 'all' ? '' : control.dataset.service;
    setState({ service: serviceFilter }, { push: true });
    renderCatalogControls(); drawAppCards();
  } else if (action === 'set-tab') {
    setState({ tab: control.dataset.tab, step: 0 });
  } else if (action === 'set-method') {
    setState({ method: control.dataset.method, step: 0 });
  } else if (action === 'prev-step') {
    setState({ step: Math.max(0, state.step - 1) });
  } else if (action === 'next-step') {
    const current = state.tab === 'configure'
      ? data.apps[state.app]?.configure[state.device]?.find((item) => item.id === state.config)
      : data.apps[state.app]?.install[state.device]?.find((item) => item.id === state.method);
    const max = Math.max(0, (current?.steps?.length || 1) - 1);
    if (state.step < max) setState({ step: state.step + 1, completed: false });
    else setState({ completed: true });
  } else if (action === 'restart-guide') {
    setState({ step: 0, completed: false });
  } else if (action === 'continue-config') {
    const app = data.apps[state.app];
    if (app?.configure?.[state.device]?.length) setState({ tab: 'configure', step: 0, completed: false });
    else setState({ tab: 'help', step: 0, completed: false });
  } else if (action === 'open-help') {
    setState({ tab: 'help', step: 0, completed: false }, { scroll: true });
  } else if (action === 'copy-guide') {
    copyGuideLink();
  } else if (action === 'load-video') {
    loadVideo(control.dataset.video);
  } else if (action === 'open-lightbox') {
    const dialog = $('#media-lightbox');
    const image = $('#lightbox-image');
    image.src = control.dataset.image;
    image.alt = control.dataset.title || 'Aperçu agrandi';
    $('#lightbox-title').textContent = control.dataset.title || 'Aperçu agrandi';
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
    $('.lightbox-close')?.focus();
  } else if (action === 'close-lightbox') {
    $('#media-lightbox')?.close?.();
  }
}

document.addEventListener('click', onClick);
window.addEventListener('scroll', updateScrollProgress, { passive: true });
window.addEventListener('resize', updateScrollProgress, { passive: true });
updateScrollProgress();
document.addEventListener('keydown', (event) => {
  const card = event.target.closest?.('.app-card[data-action="open-app"]');
  if (card && (event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault(); card.click();
  }
  const tab = event.target.closest?.('[role="tab"]');
  if (tab) {
    const tabs = $$('.detail-tabs [role="tab"]');
    const index = tabs.indexOf(tab);
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft' || event.key === 'Home' || event.key === 'End') {
      event.preventDefault();
      const delta = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
      const targetIndex = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + delta + tabs.length) % tabs.length;
      tabs[targetIndex]?.click();
      window.requestAnimationFrame(() => document.querySelector('[role="tab"][aria-selected="true"]')?.focus());
    }
  }
  if (event.key === 'Escape' && state.app) setState({ app: '', tab: 'overview', completed: false }, { scroll: true });
  if (event.key.toLowerCase() === 'r' && state.app && (state.tab === 'install' || state.tab === 'configure') && !['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName)) setState({ step: 0, completed: false });
});
$('#media-lightbox')?.addEventListener('click', (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
window.addEventListener('popstate', () => {
  state = readUrlState();
  if (data) { normalizeState(); render(); }
});

fetch(DATA_URL, { cache: 'no-cache' })
  .then((response) => {
    if (!response.ok) throw new Error(`Erreur HTTP ${response.status}`);
    return response.json();
  })
  .then((json) => {
    if (!json.apps || !json.devices || json.schema_version !== 1) throw new Error('Format de données inattendu');
    data = json;
    if (loadingState) loadingState.hidden = true;
    normalizeState();
    syncUrl(false);
    render();
    announce('Catalogue chargé.');
  })
  .catch((error) => {
    if (loadingState) loadingState.hidden = true;
    const empty = el('div', 'empty-state');
    empty.append(el('strong', '', 'Le catalogue ne s’est pas chargé.'), document.createTextNode('Vérifiez votre connexion ou la présence du fichier data/site-data.json, puis réessayez.'));
    const retry = el('button', 'round-button primary', 'Réessayer');
    retry.type = 'button'; retry.addEventListener('click', () => window.location.reload());
    empty.append(el('br'), retry);
    catalogRoot.replaceChildren(empty);
    announce('Le catalogue ne s’est pas chargé. Un bouton Réessayer est disponible.', { error: true });
    console.error('Assistant Installation: impossible de charger les données publiques.', error);
  });
