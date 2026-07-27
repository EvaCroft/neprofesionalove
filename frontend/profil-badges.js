/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

/* ===== ODZNAKY (v25) - výběr max. 5 z pevného katalogu, zobrazení nad
   "O mně". Katalog je editovatelný adminem v DB (/badges), ne hardcoded -
   proto se vždy natáhne živě z API, ne z konstanty ve frontendu. */

const MAX_BADGES = 5;
let _badgeCatalog = [];
let _myBadgeKeys = [];

function renderBadgeRow(badges){
  const row = document.getElementById('badge-row');
  if(!badges.length){
    row.innerHTML = '<span style="color:var(--text-3); font-size:.8rem;">Zatím žádné odznaky.</span>';
    return;
  }
  row.innerHTML = badges.map(b => `<div class="badge-chip" title="${b.name}">${b.emoji}</div>`).join('');
}

async function loadBadges(){
  try{
    const meRes = await fetch('/auth/me', { headers: authHeaders() });
    if(!meRes.ok) return;
    const me = await meRes.json();
    const res = await fetch(`/badges/${me.id}`);
    if(!res.ok) return;
    const badges = await res.json();
    _myBadgeKeys = badges.map(b => b.key);
    renderBadgeRow(badges);
  }catch(e){ /* necháme placeholder, pokud API neodpoví */ }
}

function _renderBadgePicker(){
  const picker = document.getElementById('badge-picker');
  picker.innerHTML = _badgeCatalog.map(b => `
    <div class="badge-pick-item ${_myBadgeKeys.includes(b.key) ? 'selected' : ''}" data-key="${b.key}" onclick="toggleBadgePick('${b.key}')">
      <div class="badge-chip">${b.emoji}</div>
      <span>${b.name}</span>
    </div>
  `).join('');
}

function toggleBadgePick(key){
  if(_myBadgeKeys.includes(key)){
    _myBadgeKeys = _myBadgeKeys.filter(k => k !== key);
  }else{
    if(_myBadgeKeys.length >= MAX_BADGES){
      alert(`Max. ${MAX_BADGES} odznaků najednou. Nejdřív nějaký odeber.`);
      return;
    }
    _myBadgeKeys.push(key);
  }
  _renderBadgePicker();
}

async function openEditBadges(){
  document.getElementById('edit-badges-overlay').classList.add('open');
  try{
    const res = await fetch('/badges');
    if(res.ok) _badgeCatalog = await res.json();
  }catch(e){ /* necháme případný předchozí katalog */ }
  _renderBadgePicker();
}

function closeEditBadges(){
  document.getElementById('edit-badges-overlay').classList.remove('open');
}

async function saveBadges(){
  try{
    const res = await fetch('/badges/me', {
      method: 'PUT',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ badge_keys: _myBadgeKeys }),
    });
    const data = await res.json();
    if(!res.ok){
      alert(data.detail || 'Uložení odznaků se nezdařilo.');
      return;
    }
    renderBadgeRow(data);
    closeEditBadges();
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}
