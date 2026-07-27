/* Auth guard - stejný vzor jako layout-user-profil.html */
const NP_TOKEN = localStorage.getItem('np_token');
if (!NP_TOKEN) { window.location.replace('layout-auth.html'); }

const authHeaders = { 'Authorization': 'Bearer ' + NP_TOKEN };

const SOURCE_LABEL = { wall: 'Zeď profilu', direct_upload: 'Nahráno do galerie', messenger: 'Messenger', room: 'Chat místnosti' };
const TYPE_ICON = {
  photo: '<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M3 13l4-4 3 3 5-5 6 6"/><circle cx="8" cy="8" r="1.3"/>',
  video: '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M16 10l6-4v12l-6-4z"/>',
  audio: '<path d="M9 18V6l10-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/>',
  reel:  '<rect x="4" y="2" width="16" height="20" rx="3"/><path d="M9 8l6 4-6 4z"/>',
};
const SOURCE_ICON = {
  wall: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/>',
  direct_upload: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/>',
  messenger: '<path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>',
  room: '<path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.4-4 8-9 8-1.2 0-2.4-.2-3.4-.6L3 21l1.6-4.2A7.9 7.9 0 013 12c0-4.4 4-8 9-8s9 3.6 9 8z"/>',
};
const DIRECTION_ICON = {
  sent: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  received: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
};

let state = { type: '', direction: '', source: '', sort: 'newest', view: 'grid' };
let currentAssets = [];

function svg(inner, extraAttrs){ return `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ${extraAttrs||''}>${inner}</svg>`; }

function fmtDuration(sec){
  if (sec == null) return null;
  const m = Math.floor(sec/60), s = Math.round(sec%60);
  return m + ':' + String(s).padStart(2,'0');
}
function fmtTime(iso){
  const d = new Date(iso);
  return d.toLocaleTimeString('cs-CZ', {hour:'2-digit', minute:'2-digit'});
}
function dayLabel(iso){
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date(); yesterday.setDate(today.getDate()-1);
  const sameDay = (a,b) => a.getFullYear()===b.getFullYear() && a.getMonth()===b.getMonth() && a.getDate()===b.getDate();
  if (sameDay(d, today)) return 'Dnes';
  if (sameDay(d, yesterday)) return 'Včera';
  return d.toLocaleDateString('cs-CZ', {day:'numeric', month:'long'});
}

function captionFor(asset){
  if (asset.direction === 'sent') return 'Odesláno' + (asset.source === 'room' ? '' : ' · uživateli #' + asset.to_user_id);
  if (asset.direction === 'received') return 'Přijato' + (asset.source === 'messenger' ? ' · od uživatele #' + asset.owner_id : ' · sdíleno v místnosti');
  return SOURCE_LABEL[asset.source] || 'Nahráno';
}

function renderTile(asset){
  const tile = document.createElement('div');
  tile.className = 'media-tile' + (asset.media_type === 'audio' ? ' audio' : '');
  tile.title = asset.original_filename;

  // v22-BUG-01/02 + sjednocení (viz frontend/media-shared.js): náhled se teď
  // vykresluje přes sdílenou funkci MediaShared.thumbHTML(), stejnou, jakou
  // používá i "Moje média" na profilu a příloha u příspěvku na Zdi - jedna
  // oprava/úprava se tak promítne všude, ne jen na téhle stránce.
  if (asset.media_type !== 'audio' && window.MediaShared) {
    tile.insertAdjacentHTML('afterbegin', window.MediaShared.thumbHTML(asset));
  }

  let inner = '';
  if (asset.media_type === 'audio') {
    inner += svg(TYPE_ICON.audio);
  } else {
    inner += `<div class="tile-type-badge">${svg(TYPE_ICON[asset.media_type]||'')}</div>`;
  }

  const dur = fmtDuration(asset.duration_seconds);
  if (dur) inner += `<div class="duration-tag">${dur}</div>`;

  if (asset.source !== 'wall' && asset.source !== 'direct_upload') {
    inner += `<div class="tile-source-badge" title="${SOURCE_LABEL[asset.source]}">${svg(SOURCE_ICON[asset.source]||'')}</div>`;
  } else {
    inner += `<div class="tile-source-badge" title="${SOURCE_LABEL[asset.source]}">${svg(SOURCE_ICON[asset.source]||'')}</div>`;
  }

  if (asset.direction === 'sent' || asset.direction === 'received') {
    inner += `<div class="tile-direction ${asset.direction}" title="${asset.direction === 'sent' ? 'Odesláno' : 'Přijato'}">${svg(DIRECTION_ICON[asset.direction], 'stroke-width="2.5"')}</div>`;
  }

  inner += `<div class="tile-overlay"><div class="tile-overlay-text"><b>${captionFor(asset)}</b><span>${fmtTime(asset.created_at)}</span></div></div>`;
  tile.insertAdjacentHTML('beforeend', inner);
  tile.addEventListener('click', () => openLightbox(asset));
  return tile;
}

function renderTimelineRow(asset){
  const row = document.createElement('div');
  row.className = 'timeline-row';

  const thumb = document.createElement('div');
  thumb.className = 'timeline-thumb';
  if (asset.media_type !== 'audio' && window.MediaShared) {
    thumb.insertAdjacentHTML('afterbegin', window.MediaShared.thumbHTML(asset));
  }
  row.appendChild(thumb);

  const info = document.createElement('div');
  info.className = 'timeline-info';
  info.innerHTML = '<b></b><span></span>';
  info.querySelector('b').textContent = asset.original_filename;
  info.querySelector('span').textContent = captionFor(asset);
  row.appendChild(info);

  const meta = document.createElement('div');
  meta.className = 'timeline-meta';
  meta.textContent = fmtTime(asset.created_at);
  row.appendChild(meta);

  row.addEventListener('click', () => openLightbox(asset));
  return row;
}

function groupByDay(assets){
  const groups = new Map();
  for (const a of assets){
    const label = dayLabel(a.created_at);
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(a);
  }
  return groups;
}

function renderGallery(){
  const content = document.getElementById('gallery-content');
  const empty = document.getElementById('empty-state');
  content.innerHTML = '';

  if (currentAssets.length === 0){
    empty.style.display = 'block';
    content.style.display = 'none';
    return;
  }
  empty.style.display = 'none';
  content.style.display = 'block';

  const groups = groupByDay(currentAssets);
  for (const [label, assets] of groups){
    const group = document.createElement('div');
    group.className = 'day-group';
    const groupLabel = document.createElement('div');
    groupLabel.className = 'day-group-label';
    groupLabel.textContent = label;
    group.appendChild(groupLabel);

    const wrap = document.createElement('div');
    wrap.className = state.view === 'grid' ? 'media-grid' : '';
    for (const a of assets){
      wrap.appendChild(state.view === 'grid' ? renderTile(a) : renderTimelineRow(a));
    }
    group.appendChild(wrap);
    content.appendChild(group);
  }
}

async function loadStats(){
  try {
    const res = await fetch('/media/stats', { headers: authHeaders });
    if (!res.ok) return;
    const data = await res.json();
    const byType = Object.fromEntries(data.by_type.map(t => [t.media_type, t.count]));
    document.querySelector('.gstat[data-type="vse"] b').textContent = data.total;
    document.querySelector('.gstat[data-type="foto"] b').textContent = byType.photo || 0;
    document.querySelector('.gstat[data-type="video"] b').textContent = byType.video || 0;
    document.querySelector('.gstat[data-type="audio"] b').textContent = byType.audio || 0;
    document.querySelector('.gstat[data-type="reels"] b').textContent = byType.reel || 0;
  } catch (e) { console.error('Nepodařilo se načíst statistiky galerie', e); }
}

async function loadMedia(){
  document.getElementById('gallery-loading').style.display = 'block';
  document.getElementById('gallery-content').style.display = 'none';
  document.getElementById('empty-state').style.display = 'none';

  const params = new URLSearchParams();
  if (state.type && state.type !== 'vse') params.set('media_type', state.type === 'foto' ? 'photo' : state.type === 'reels' ? 'reel' : state.type);
  if (state.direction) params.set('direction', state.direction);
  if (state.source) params.set('source', state.source);
  params.set('sort', state.sort);

  try {
    const res = await fetch('/media?' + params.toString(), { headers: authHeaders });
    if (res.status === 401) { window.location.replace('layout-auth.html'); return; }
    currentAssets = res.ok ? await res.json() : [];
  } catch (e) {
    console.error('Nepodařilo se načíst galerii médií', e);
    currentAssets = [];
  }

  document.getElementById('gallery-loading').style.display = 'none';
  renderGallery();
}

function filterType(el){
  document.querySelectorAll('.gstat').forEach(x=>x.classList.remove('active'));
  el.classList.add('active');
  state.type = el.dataset.type;
  loadMedia();
}

/* Otevírání/procházení/mazání médií teď řeší sdílený prohlížeč MediaShared.openViewer()
   (frontend/media-shared.js) — stejná logika jako v tabu "Moje média" na profilu a
   u příspěvků na Zdi, viz DEVLOG #042. Seznam pro šipky = aktuálně načtená stránka
   Galerie médií (`currentAssets`), po smazání se karta/dlaždice zase přepočítá zdejším
   `loadStats()`+`loadMedia()`. */
function openLightbox(asset){
  MediaShared.primeCache(currentAssets);
  MediaShared.openViewer(currentAssets.map(a => a.id), asset.id, {
    authHeaders,
    onDelete: () => { loadStats(); loadMedia(); },
  });
}

document.querySelectorAll('.gallery-toolbar .seg')[0].querySelectorAll('button').forEach((btn, i) => {
  const map = ['', 'uploaded', 'sent', 'received'];
  btn.addEventListener('click', () => {
    document.querySelectorAll('.gallery-toolbar .seg button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    state.direction = map[i];
    loadMedia();
  });
});

const selects = document.querySelectorAll('.gallery-select select');
selects[0].addEventListener('change', (e) => {
  const map = { 'Všechny zdroje': '', 'Zeď profilu': 'wall', 'Messenger': 'messenger', 'Chat místnosti': 'room', 'Přímé nahrání': 'direct_upload' };
  state.source = map[e.target.value] || '';
  loadMedia();
});
selects[1].addEventListener('change', (e) => {
  const map = { 'Nejnovější': 'newest', 'Nejstarší': 'oldest', 'Nejoblíbenější': 'newest', 'Podle velikosti': 'size' };
  state.sort = map[e.target.value] || 'newest';
  loadMedia();
});

document.querySelectorAll('.view-toggle button').forEach((btn, i) => {
  btn.addEventListener('click', () => {
    btn.parentElement.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    state.view = i === 0 ? 'grid' : 'timeline';
    renderGallery();
  });
});

document.getElementById('upload-input').addEventListener('change', async (e) => {
  const files = e.target.files;
  if (!files.length) return;
  for (const file of files){
    const form = new FormData();
    form.append('file', file);
    form.append('source', 'wall'); // nahrání z galerie = jako by šlo na zeď profilu
    try {
      const res = await fetch('/media/upload', { method: 'POST', headers: authHeaders, body: form });
      if (!res.ok) { const err = await res.json().catch(()=>({})); alert('Nahrání se nepovedlo: ' + (err.detail || res.status)); }
    } catch (err) { alert('Nahrání se nepovedlo.'); }
  }
  e.target.value = '';
  loadStats();
  loadMedia();
});

loadStats();
loadMedia();
