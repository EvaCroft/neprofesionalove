/* frontend/profil-locations.js — Správa lokalit na vlastním profilu
   (BUILDPLAN_backlog.md bod 4: "Dokončení správy lokalit na profilu").
 *
 * Backend (`app/routers/profile.py`, `app/models/profile_location.py`)
 * i schémata (`ProfileLocationOut/Create/Update`) už existovala z v27
 * (kvůli zobrazení lokalit na veřejném profilu, viz profil-verejny.js) -
 * tenhle soubor doplňuje jediný chybějící kus: UI pro SPRÁVU (přidat/
 * upravit/smazat) až MAX_LOCATIONS lokalit na vlastním profilu.
 *
 * Vzor podle profil-badges.js (vlastní modul, global scope, žádné
 * zásahy do profil-core.js mimo jednoho volání renderLocationsList()
 * z loadProfileData(), stejně jako tam přímo nastavuje education/religion).
 *
 * Limit 3 lokalit (label "Domov"/"Práce"/"Chalupa" apod. + město + země +
 * popis) NENÍ vynucený na backendu (žádný check v add_my_location) - je to
 * čistě frontendová/produktová volba z backlogu, tlačítko "+ Přidat" se
 * po dosažení limitu skryje.
 */

const MAX_LOCATIONS = 3;
let _myLocations = [];
let _editingLocationId = null;

function escapeHtmlLoc(str) {
  var div = document.createElement('div');
  div.textContent = str == null ? '' : String(str);
  return div.innerHTML;
}

function renderLocationsList(locations) {
  _myLocations = locations || [];
  var list = document.getElementById('locations-list');
  var addBtn = document.getElementById('btn-add-location');
  if (!list) return;

  if (!_myLocations.length) {
    list.innerHTML = '<span style="color:var(--text-3); font-size:.8rem;">Zatím žádné lokality.</span>';
  } else {
    list.innerHTML = _myLocations.map(function (loc) {
      var label = loc.label ? '<b>' + escapeHtmlLoc(loc.label) + ':</b> ' : '';
      var place = escapeHtmlLoc(loc.city) + (loc.country ? ', ' + escapeHtmlLoc(loc.country) : '');
      var desc = loc.description ? '<div style="font-size:.76rem;color:var(--text-3);margin:2px 0 0 26px;">' + escapeHtmlLoc(loc.description) + '</div>' : '';
      return '<div class="info-row" style="justify-content:space-between; align-items:flex-start;">' +
        '<div style="display:flex; gap:10px;">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-top:2px;"><path d="M12 21s-7-6.1-7-11a7 7 0 0114 0c0 4.9-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>' +
        '<div>' + label + place + desc + '</div>' +
        '</div>' +
        '<div style="display:flex; gap:4px; flex-shrink:0;">' +
        '<button class="profile-btn ghost icon-only" style="padding:4px; width:26px; height:26px;" title="Upravit" onclick="openEditLocation(' + loc.id + ')">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg>' +
        '</button>' +
        '<button class="profile-btn ghost icon-only" style="padding:4px; width:26px; height:26px;" title="Smazat" onclick="deleteLocation(' + loc.id + ')">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/></svg>' +
        '</button>' +
        '</div></div>';
    }).join('');
  }

  if (addBtn) addBtn.style.display = _myLocations.length >= MAX_LOCATIONS ? 'none' : '';
}

function openAddLocation() {
  if (_myLocations.length >= MAX_LOCATIONS) return;
  _editingLocationId = null;
  document.getElementById('location-form-title').textContent = 'Přidat lokalitu';
  document.getElementById('location-label').value = '';
  document.getElementById('location-city').value = '';
  document.getElementById('location-country').value = '';
  document.getElementById('location-description').value = '';
  document.getElementById('location-form-msg').className = 'form-msg';
  document.getElementById('location-form-overlay').classList.add('open');
}

function openEditLocation(id) {
  var loc = _myLocations.find(function (l) { return l.id === id; });
  if (!loc) return;
  _editingLocationId = id;
  document.getElementById('location-form-title').textContent = 'Upravit lokalitu';
  document.getElementById('location-label').value = loc.label || '';
  document.getElementById('location-city').value = loc.city || '';
  document.getElementById('location-country').value = loc.country || '';
  document.getElementById('location-description').value = loc.description || '';
  document.getElementById('location-form-msg').className = 'form-msg';
  document.getElementById('location-form-overlay').classList.add('open');
}

function closeLocationForm() {
  document.getElementById('location-form-overlay').classList.remove('open');
}

async function saveLocationForm() {
  const msgEl = document.getElementById('location-form-msg');
  const btn = document.getElementById('save-location-btn');
  const city = document.getElementById('location-city').value.trim();

  if (!city) {
    msgEl.textContent = 'Vyplň prosím alespoň město.';
    msgEl.className = 'form-msg error';
    return;
  }

  const payload = {
    label: document.getElementById('location-label').value.trim() || null,
    city: city,
    country: document.getElementById('location-country').value.trim() || null,
    description: document.getElementById('location-description').value.trim() || null,
  };

  const isEdit = _editingLocationId !== null;
  const url = isEdit ? '/profile/me/locations/' + _editingLocationId : '/profile/me/locations';
  const method = isEdit ? 'PUT' : 'POST';

  btn.disabled = true; btn.textContent = 'Ukládám…';
  try {
    const res = await fetch(url, {
      method: method,
      headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      msgEl.textContent = data.detail || 'Uložení se nezdařilo.';
      msgEl.className = 'form-msg error';
      btn.disabled = false; btn.textContent = 'Uložit';
      return;
    }

    if (isEdit) {
      _myLocations = _myLocations.map(function (l) { return l.id === data.id ? data : l; });
    } else {
      _myLocations = _myLocations.concat([data]);
    }
    renderLocationsList(_myLocations);
    btn.disabled = false; btn.textContent = 'Uložit';
    closeLocationForm();
  } catch (e) {
    msgEl.textContent = 'Nepodařilo se spojit se serverem. Zkus to znovu.';
    msgEl.className = 'form-msg error';
    btn.disabled = false; btn.textContent = 'Uložit';
  }
}

async function deleteLocation(id) {
  if (!window.confirm('Opravdu smazat tuhle lokalitu?')) return;
  try {
    const res = await fetch('/profile/me/locations/' + id, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    if (!res.ok && res.status !== 204) {
      window.alert('Smazání se nezdařilo, zkus to prosím znovu.');
      return;
    }
    _myLocations = _myLocations.filter(function (l) { return l.id !== id; });
    renderLocationsList(_myLocations);
  } catch (e) {
    window.alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}
