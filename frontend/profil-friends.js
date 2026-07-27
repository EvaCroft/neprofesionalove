/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

/* ===== VZTAHY (v24) - žádosti o přátelství na vlastním profilu + reálný
   počet přátel do karty "Statistiky". Tlačítka na CIZÍM profilu (přidat do
   přátel/sledovat) odloženo do v27 (na žádost uživatele, viz DEVLOG #044) -
   stránka zatím vůbec neumí zobrazit cizí user_id v ostatních záložkách. */

function _friendUserLabel(u){
  return (u && u.display_name) ? u.display_name : `Uživatel #${u ? u.user_id : '?'}`;
}

async function loadFriendRequests(){
  try{
    const res = await fetch('/friends/requests/incoming', { headers: authHeaders() });
    if(!res.ok) return;
    const requests = await res.json();
    const card = document.getElementById('card-friend-requests');
    const list = document.getElementById('friend-requests-list');
    if(!requests.length){
      card.style.display = 'none';
      return;
    }
    card.style.display = '';
    list.innerHTML = requests.map(r => `
      <div class="room-row" id="friend-request-${r.from_user_id}">
        <div class="avatar-sm"></div>
        <div class="rinfo"><b>${_friendUserLabel(r.user)}</b><span>chce být tvým přítelem/tvojí přítelkyní</span></div>
        <div class="pill-btn-row">
          <button class="pill-btn" onclick="acceptFriendRequest(${r.from_user_id})">Přijmout</button>
          <button class="pill-btn ghost" onclick="declineFriendRequest(${r.from_user_id})">Odmítnout</button>
        </div>
      </div>
    `).join('');
  }catch(e){ /* necháme kartu skrytou, pokud API neodpoví */ }
}

async function acceptFriendRequest(fromUserId){
  try{
    const res = await fetch(`/friends/accept/${fromUserId}`, { method:'POST', headers: authHeaders() });
    if(!res.ok){
      const data = await res.json().catch(()=>({}));
      alert(data.detail || 'Přijetí žádosti se nezdařilo.');
      return;
    }
    const row = document.getElementById(`friend-request-${fromUserId}`);
    if(row) row.remove();
    if(!document.getElementById('friend-requests-list').children.length){
      document.getElementById('card-friend-requests').style.display = 'none';
    }
    loadFriendCounts();
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}

async function declineFriendRequest(fromUserId){
  try{
    const res = await fetch(`/friends/decline/${fromUserId}`, { method:'DELETE', headers: authHeaders() });
    if(!res.ok && res.status !== 204){
      const data = await res.json().catch(()=>({}));
      alert(data.detail || 'Odmítnutí žádosti se nezdařilo.');
      return;
    }
    const row = document.getElementById(`friend-request-${fromUserId}`);
    if(row) row.remove();
    if(!document.getElementById('friend-requests-list').children.length){
      document.getElementById('card-friend-requests').style.display = 'none';
    }
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}

async function loadFriendCounts(){
  try{
    const meRes = await fetch('/auth/me', { headers: authHeaders() });
    if(!meRes.ok) return;
    const me = await meRes.json();
    const res = await fetch(`/friends/counts/${me.id}`);
    if(!res.ok) return;
    const counts = await res.json();
    const el = document.getElementById('stat-friends-count');
    if(el) el.textContent = counts.friends_count.toLocaleString('cs-CZ');
    document.getElementById('stat-followers').textContent = counts.followers_count.toLocaleString('cs-CZ');
    document.getElementById('stat-following').textContent = counts.following_count.toLocaleString('cs-CZ');
  }catch(e){ /* necháme placeholder '—', pokud API neodpoví */ }
}

/* ===== PŘÍTOMNOST (v27) - online status v kartě "O mně", odvozeno z v26
   presence endpointu. Na vlastním profilu se zobrazuje vždy (viditelnost
   pole "online_status" dle field_visibility se řeší až u cizího profilu -
   samostatný veřejný layout, mimo tento krok). */
async function loadPresence(){
  const dot = document.getElementById('presence-dot');
  const label = document.getElementById('info-presence');
  try{
    const meRes = await fetch('/auth/me', { headers: authHeaders() });
    if(!meRes.ok) return;
    const me = await meRes.json();
    const res = await fetch(`/profile/${me.id}/presence`);
    if(!res.ok) return;
    const p = await res.json();
    if(p.is_online){
      dot.style.background = '';
      dot.classList.add('dot-green');
      let text = 'Online';
      if(p.activity === 'chatting') text += p.activity_detail ? ` · chatuje v „${p.activity_detail}“` : ' · chatuje';
      if(p.activity === 'playing') text += ' · hraje';
      label.textContent = text;
    }else{
      dot.style.background = 'var(--text-3)';
      dot.classList.remove('dot-green');
      label.textContent = p.last_active_at ? 'Naposledy aktivní ' + formatTimeAgo(p.last_active_at) : 'Offline';
    }
  }catch(e){ label.textContent = 'Stav nedostupný'; }
}

/* ===== PŘÁTELÉ - náhled seznamu pod "O mně" (v27). Plný seznam/správa
   zůstává na Přehledu (žádosti); tady jde jen o rychlý přehled, kolik a
   koho mám. Guest-friendly endpoint /friends/list, ale tady vždy pro sebe. */
async function loadFriendsPreview(){
  const list = document.getElementById('friends-preview-list');
  const totalLabel = document.getElementById('friends-total-label');
  try{
    const meRes = await fetch('/auth/me', { headers: authHeaders() });
    if(!meRes.ok) return;
    const me = await meRes.json();
    const res = await fetch(`/friends/list/${me.id}?limit=8`);
    if(!res.ok) return;
    const friends = await res.json();
    if(!friends.length){
      list.innerHTML = '<span style="color:var(--text-3); font-size:.8rem;">Zatím žádní přátelé.</span>';
      totalLabel.textContent = '';
      return;
    }
    list.innerHTML = friends.map(f => `
      <div style="display:flex; flex-direction:column; align-items:center; gap:4px; width:60px;" title="${_friendUserLabel(f)}">
        <div class="avatar-sm"></div>
        <span style="font-size:.66rem; color:var(--text-2); text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; width:100%;">${_friendUserLabel(f)}</span>
      </div>
    `).join('');
    const countsRes = await fetch(`/friends/counts/${me.id}`);
    if(countsRes.ok){
      const counts = await countsRes.json();
      totalLabel.textContent = counts.friends_count > friends.length ? `${counts.friends_count} celkem` : '';
    }
  }catch(e){ /* necháme placeholder, pokud API neodpoví */ }
}
