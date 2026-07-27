/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

/* ===== ZEĎ (tab v profilu) - napojeno na /posts API přes posts-shared.js,
   viz layout-wall.html pro plnou stránku Zdi (stejná sdílená logika). ===== */
function loadZedFeed(){
  const myId = _currentProfile.user_id;
  if (!myId) return;
  return PostsShared.loadWall({
    targetUserId: myId,
    feedEl: document.getElementById('zed-feed'),
    emptyEl: document.getElementById('zed-empty'),
    authHeaders: authHeaders(),
    variant: 'row',
    onMediaDeleted: loadZedFeed,
  });
}

function zedSubmitPost(){
  return PostsShared.submitPost({
    textEl: document.getElementById('zed-post-text'),
    visibilityEl: document.getElementById('zed-post-visibility'),
    submitBtn: document.getElementById('zed-post-submit'),
    authHeaders: authHeaders(),
    onSuccess: loadZedFeed,
  });
}

/* ===== AKTIVITA (tab v profilu) - napojeno na /activity API (v23),
   viz app/services/activity_service.py pro logiku renderování/viditelnosti.
   Aktivita čte z existujícího user-logu, nezavádí žádné nové API pro logování. ===== */
const ACTIVITY_ACTION_LABEL = {
  post_create: 'Nový příspěvek na zeď',
  room_created: 'Založení místnosti',
  room_joined: 'Vstup do místnosti',
  room_left: 'Odchod z místnosti',
  event_created: 'Vytvoření události',
  media_uploaded: 'Nahrání fotky/videa',
  referral_reward_earned: 'Odměna za pozvání přes referral',
  game_move: 'Výhra ve hře',
};

function _renderActivityInto(listEl, emptyEl, entries){
  listEl.innerHTML = '';
  if (!entries.length){
    emptyEl.style.display = '';
    return;
  }
  emptyEl.style.display = 'none';
  entries.forEach(entry => {
    const row = document.createElement('div');
    row.className = 'activity-line';
    const dot = document.createElement('div');
    dot.className = 'dotc2';
    const text = document.createElement('span');
    text.textContent = entry.text; // textContent kvůli XSS (jméno místnosti/události je uživatelský vstup)
    const time = document.createElement('span');
    time.style.cssText = 'margin-left:auto;color:var(--text-3);font-size:.72rem;flex-shrink:0;';
    time.textContent = PostsShared.fmtTime(entry.timestamp);
    row.appendChild(dot); row.appendChild(text); row.appendChild(time);
    listEl.appendChild(row);
  });
}

async function loadActivity(){
  const myId = _currentProfile.user_id;
  if (!myId) return;
  try{
    const res = await fetch(`/activity/${myId}?limit=100`, { headers: authHeaders() });
    if (!res.ok) return;
    const entries = await res.json();
    _renderActivityInto(document.getElementById('activity-list'), document.getElementById('activity-empty'), entries);
  }catch(e){ /* necháme prázdný stav, pokud API neodpoví */ }
}

async function loadActivityPreview(){
  const myId = _currentProfile.user_id;
  if (!myId) return;
  try{
    const res = await fetch(`/activity/${myId}?limit=3`, { headers: authHeaders() });
    if (!res.ok) return;
    const entries = await res.json();
    _renderActivityInto(document.getElementById('prehled-activity-list'), document.getElementById('prehled-activity-empty'), entries);
  }catch(e){ /* necháme prázdný stav, pokud API neodpoví */ }
}

let activitySettingsLoaded = false;
function toggleActivitySettings(){
  const box = document.getElementById('activity-settings');
  box.classList.toggle('open');
  if (box.classList.contains('open') && !activitySettingsLoaded) loadActivitySettings();
}

async function loadActivitySettings(){
  const res = await fetch('/activity/settings/me', { headers: authHeaders() });
  if (!res.ok) return;
  const data = await res.json();
  activitySettingsLoaded = true;
  const box = document.getElementById('activity-settings');
  box.innerHTML = '';
  Object.entries(data.visible_actions).forEach(([key, enabled]) => {
    const row = document.createElement('div');
    row.className = 'activity-settings-row';
    row.innerHTML = `<span>${ACTIVITY_ACTION_LABEL[key] || key}</span>`;
    const sw = document.createElement('button');
    sw.className = 'switch' + (enabled ? ' on' : '');
    sw.onclick = () => toggleActivityAction(key, sw);
    row.appendChild(sw);
    box.appendChild(row);
  });
}

async function toggleActivityAction(key, btn){
  const next = !btn.classList.contains('on');
  btn.classList.toggle('on', next);
  await fetch('/activity/settings/me', {
    method: 'PUT',
    headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
    body: JSON.stringify({ actions: { [key]: next } }),
  });
}
