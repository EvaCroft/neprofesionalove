/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

/* ---- Události ---- */
let _myEvents = [];
let _editingEventId = null;

function formatEventWhen(isoString){
  const d = new Date(isoString);
  const day = d.getDate();
  const time = d.toTimeString().slice(0,5);
  return `${day}. ${MONTHS_GEN[d.getMonth()]} ${d.getFullYear()}, ${time}`;
}

function openCreateEvent(){
  _editingEventId = null;
  document.getElementById('event-title').value = '';
  document.getElementById('event-starts-at').value = '';
  document.getElementById('event-location').value = '';
  document.getElementById('event-description').value = '';
  document.getElementById('event-cover-file').value = '';
  document.getElementById('event-form-msg').className = 'form-msg';
  document.querySelector('#event-form-overlay h3').textContent = 'Vytvořit událost';
  document.getElementById('save-event-btn').textContent = 'Vytvořit';
  document.getElementById('event-form-overlay').classList.add('open');
}
function closeCreateEvent(){
  document.getElementById('event-form-overlay').classList.remove('open');
}

async function saveEvent(){
  const msgEl = document.getElementById('event-form-msg');
  const btn = document.getElementById('save-event-btn');
  const title = document.getElementById('event-title').value.trim();
  const startsAtRaw = document.getElementById('event-starts-at').value;
  if(!title || !startsAtRaw){
    msgEl.textContent = 'Název a datum/čas jsou povinné.';
    msgEl.className = 'form-msg error';
    return;
  }
  const payload = {
    title,
    starts_at: new Date(startsAtRaw).toISOString(),
    location: document.getElementById('event-location').value.trim() || null,
    description: document.getElementById('event-description').value.trim() || null,
  };
  btn.disabled = true; btn.textContent = 'Ukládám…';
  try{
    const res = await fetch('/events', {
      method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if(!res.ok){
      msgEl.textContent = data.detail || 'Vytvoření se nezdařilo.';
      msgEl.className = 'form-msg error';
      btn.disabled = false; btn.textContent = 'Vytvořit';
      return;
    }
    const coverFile = document.getElementById('event-cover-file').files[0];
    if(coverFile){
      const formData = new FormData();
      formData.append('file', coverFile);
      formData.append('source', 'event_cover');
      formData.append('event_id', data.id);
      try{
        const coverRes = await fetch('/media/upload', { method:'POST', headers: authHeaders(), body: formData });
        const coverData = await coverRes.json();
        if(coverRes.ok) data.cover_url = coverData.url;
      }catch(e){ /* událost je založená i bez coveru - nepřerušovat */ }
    }
    _myEvents.unshift(data);
    renderEvents();
    btn.disabled = false; btn.textContent = 'Vytvořit';
    closeCreateEvent();
  }catch(e){
    msgEl.textContent = 'Nepodařilo se spojit se serverem. Zkus to znovu.';
    msgEl.className = 'form-msg error';
    btn.disabled = false; btn.textContent = 'Vytvořit';
  }
}

async function loadMyEvents(){
  try{
    const res = await fetch('/events?mine=true&participating=true&upcoming_only=false&limit=100', { headers: authHeaders() });
    if(!res.ok) return;
    _myEvents = await res.json();
    renderEvents();
  }catch(e){ /* necháme prázdný stav, pokud API neodpoví */ }
}

function renderEvents(){
  const listEl = document.getElementById('events-list');
  const emptyEl = document.getElementById('events-empty');
  if(!_myEvents.length){
    listEl.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }
  emptyEl.style.display = 'none';
  const myId = (_currentProfile && _currentProfile.user_id) || null;
  listEl.innerHTML = _myEvents.map(ev => {
    const isOwner = myId !== null && ev.owner_id === myId;
    const cover = ev.cover_url ? `style="background-image:url('${ev.cover_url}')"` : '';
    const statuses = [
      { key:'going', label:'Jdu' },
      { key:'interested', label:'Mám zájem' },
      { key:'went', label:'Byla jsem' },
    ];
    const chips = statuses.map(s =>
      `<button class="status-chip ${ev.my_status===s.key ? 'active '+s.key : ''}" onclick="setParticipation(${ev.id}, '${s.key}')">${s.label}</button>`
    ).join('');
    const delBtn = isOwner
      ? `<button class="event-del" title="Smazat" onclick="deleteEventRow(${ev.id})"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m2 0v14a2 2 0 01-2 2H8a2 2 0 01-2-2V6h12z"/></svg></button>`
      : '';
    return `<div class="event-row">
      <div class="event-cover" ${cover}></div>
      <div class="event-info">
        <b>${ev.title}${isOwner ? ' <span class="owner-tag">· pořádáš</span>' : ''}</b>
        <div class="event-meta"><span>${formatEventWhen(ev.starts_at)}</span>${ev.location ? `<span>· ${ev.location}</span>` : ''}<span>· ${ev.going_count} jde · ${ev.interested_count} má zájem</span></div>
      </div>
      <div class="event-actions">${chips}${delBtn}</div>
    </div>`;
  }).join('');
}

async function setParticipation(eventId, statusKey){
  try{
    const res = await fetch(`/events/${eventId}/participate`, {
      method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
      body: JSON.stringify({ status: statusKey }),
    });
    if(!res.ok){ alert('Nepodařilo se uložit účast.'); return; }
    const ev = _myEvents.find(e => e.id === eventId);
    if(ev){
      const wasNew = ev.my_status === null;
      if(ev.my_status === 'going') ev.going_count--;
      if(ev.my_status === 'interested') ev.interested_count--;
      ev.my_status = statusKey;
      if(statusKey === 'going') ev.going_count++;
      if(statusKey === 'interested') ev.interested_count++;
    }
    renderEvents();
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}

async function deleteEventRow(eventId){
  if(!confirm('Smazat tuto událost? Tuto akci nejde vzít zpět.')) return;
  try{
    const res = await fetch(`/events/${eventId}`, { method:'DELETE', headers: authHeaders() });
    if(!res.ok && res.status !== 204){ alert('Smazání se nezdařilo.'); return; }
    _myEvents = _myEvents.filter(e => e.id !== eventId);
    renderEvents();
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}
