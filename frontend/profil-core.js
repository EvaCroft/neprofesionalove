/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

function authHeaders(){ return { 'Authorization': 'Bearer ' + localStorage.getItem('np_token') }; }
function logout(){ localStorage.removeItem('np_token'); window.location.replace('layout-auth.html'); }
(async function verifySession(){
  const token = localStorage.getItem('np_token');
  if(!token) return;
  try{
    const res = await fetch('/auth/me', { headers:{ 'Authorization':'Bearer '+token } });
    if(!res.ok){ localStorage.removeItem('np_token'); window.location.replace('layout-auth.html'); }

  }catch(e){ /* výpadek sítě - neodhlašovat, jen zkusit dál */ }
})();

const ROLE_LABELS = {
  user: '● Člen', creator: '✦ Creator', moderator: '🛡 Moderátor', admin: '⚙ Admin'
};
const MONTHS_GEN = ['ledna','února','března','dubna','května','června','července','srpna','září','října','listopadu','prosince'];

let _currentProfile = { display_name: null, avatar_url: null, bio: null };
let _currentUser = null; // /auth/me (v29 - primární e-mail pro kartu "Kontaktní údaje", needitovatelný)

// v29 - stejné seznamy jako EDUCATION_CHOICES/RELIGION_CHOICES v app/schemas.py.
// Při změně na backendu je NUTNÉ upravit i tady (žádné sdílené API pro seznamy).
const EDUCATION_CHOICES = ['základní', 'vyučen/a', 'středoškolské', 'vyšší odborné', 'vysokoškolské', 'nechci uvádět'];
const RELIGION_CHOICES = ['křesťanství', 'islám', 'judaismus', 'buddhismus', 'hinduismus', 'bez vyznání', 'nechci uvádět'];

function _fillChoiceSelect(selectEl, choices){
  selectEl.innerHTML = '<option value="">— nevybráno —</option>' +
    choices.map(c => `<option value="${c}">${c}</option>`).join('');
}
_fillChoiceSelect(document.getElementById('edit-education'), EDUCATION_CHOICES);
_fillChoiceSelect(document.getElementById('edit-religion'), RELIGION_CHOICES);

function formatMemberSince(isoString){
  const d = new Date(isoString);
  return `Členka/člen od ${MONTHS_GEN[d.getMonth()]} ${d.getFullYear()}`;
}

function formatTimeAgo(isoString){
  const diffMin = Math.max(0, Math.round((Date.now() - new Date(isoString).getTime()) / 60000));
  if(diffMin < 1) return 'právě teď';
  if(diffMin < 60) return `před ${diffMin} min`;
  const diffHod = Math.round(diffMin / 60);
  if(diffHod < 24) return `před ${diffHod} h`;
  const diffDny = Math.round(diffHod / 24);
  return `před ${diffDny} dny`;
}

function applyAvatar(url){
  const el = document.getElementById('profile-avatar');
  if(url){
    el.style.backgroundImage = `url('${url}')`;
    el.style.backgroundSize = 'cover';
    el.style.backgroundPosition = 'center';
  }
}

function applyCover(url){
  const el = document.getElementById('profile-cover');
  if(url){
    el.style.backgroundImage = `url('${url}')`;
    el.style.backgroundSize = 'cover';
    el.style.backgroundPosition = 'center';
  }
}

async function _uploadProfileImage(file, source, applyFn, buttonLabelEl){
  if(!file) return;
  if(!file.type.startsWith('image/')){
    alert('Profilovka a cover musí být obrázek.');
    return;
  }
  const originalLabel = buttonLabelEl ? buttonLabelEl.textContent : null;
  if(buttonLabelEl) buttonLabelEl.textContent = 'Nahrávám…';

  const formData = new FormData();
  formData.append('file', file);
  formData.append('source', source);

  try{
    const res = await fetch('/media/upload', {
      method: 'POST',
      headers: authHeaders(), // bez Content-Type - browser si sám doplní multipart boundary
      body: formData,
    });
    const data = await res.json();
    if(!res.ok){
      alert(data.detail || 'Nahrání se nezdařilo.');
      return;
    }
    applyFn(data.url);
    if(source === 'profile_avatar') _currentProfile.avatar_url = data.url;
    if(source === 'profile_cover') _currentProfile.cover_url = data.url;
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }finally{
    if(buttonLabelEl) buttonLabelEl.textContent = originalLabel;
  }
}

function uploadAvatar(file){
  _uploadProfileImage(file, 'profile_avatar', applyAvatar, null);
}
function uploadCover(file){
  _uploadProfileImage(file, 'profile_cover', applyCover, document.getElementById('cover-edit-label'));
}

async function loadProfileData(){
  try{
    const [meRes, profileRes, walletRes, referralRes] = await Promise.all([
      fetch('/auth/me', { headers: authHeaders() }),
      fetch('/profile/me', { headers: authHeaders() }),
      fetch('/wallet/me', { headers: authHeaders() }),
      fetch('/referral/my-code', { headers: authHeaders() }),
    ]);

    if(meRes.ok){
      const me = await meRes.json();
      _currentUser = me;
      document.getElementById('profile-role-tag').textContent = ROLE_LABELS[me.role] || me.role;
      document.getElementById('info-member-since').textContent = formatMemberSince(me.created_at);
      document.getElementById('info-email').textContent = me.email;
    }

    if(profileRes.ok){
      const p = await profileRes.json();
      _currentProfile = p;
      document.getElementById('profile-name').textContent = p.display_name || 'Bez jména';
      document.getElementById('profile-handle').textContent = '@' + (p.display_name ? p.display_name.toLowerCase().replace(/\s+/g,'') : 'uzivatel');
      document.getElementById('profile-bio').textContent = p.bio || 'Zatím žádné bio.';
      if(p.avatar_url) applyAvatar(p.avatar_url);
      if(p.cover_url) applyCover(p.cover_url);
      if(_myEvents.length) renderEvents(); // profil se může načíst až po událostech - dopočítat owner tag/mazání

      // trvalé statistiky (v27) - přímo z Profile, žádný extra request
      document.getElementById('stat-profile-views').textContent = (p.profile_views_count || 0).toLocaleString('cs-CZ');
      const hours = Math.round((p.chat_minutes || 0) / 60 * 10) / 10;
      document.getElementById('stat-chat-hours').textContent = hours.toLocaleString('cs-CZ');

      // v29 - vzdělání/náboženství/sexuální preference (O mně) + telefon (Kontaktní údaje)
      document.getElementById('info-education').textContent = 'Vzdělání: ' + (p.education || 'nechci uvádět');
      document.getElementById('info-religion').textContent = 'Náboženství: ' + (p.religion || 'nechci uvádět');
      if(p.sexual_preference){
        document.getElementById('info-sexual-preference').textContent = p.sexual_preference;
        document.getElementById('info-sexual-preference-row').style.display = '';
      }
      document.getElementById('info-phone').textContent = p.phone ? p.phone : 'Telefon zatím nevyplněn';

      // v27 backend (lokality) + backlog bod 4 (UI) - viz profil-locations.js
      renderLocationsList(p.locations || []);
    }

    if(walletRes.ok){
      const w = await walletRes.json();
      const balance = Math.round(parseFloat(w.balance));
      document.getElementById('stat-credits').textContent = balance.toLocaleString('cs-CZ');
    }

    if(referralRes.ok){
      const r = await referralRes.json();
      document.getElementById('info-referral').textContent = 'Referral kód: ' + r.code;
    }
  }catch(e){ /* necháme placeholder hodnoty, pokud API neodpoví */ }
}
