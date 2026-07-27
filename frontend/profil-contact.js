/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

/* ===== KONTAKTNÍ ÚDAJE (v29) - sekundární e-mail/telefon, datum narození,
   adresa. Odděleno od "Upravit profil", ukládání vyžaduje heslo (PUT
   /profile/me/sensitive). Primární e-mail/telefon jsou tu jen ke čtení -
   needitovatelné natrvalo, viz DEVLOG #049. */
function openEditSensitive(){
  document.getElementById('sensitive-email').value = (_currentUser && _currentUser.email) || '';
  document.getElementById('sensitive-phone').value = _currentProfile.phone || '';
  document.getElementById('sensitive-email-secondary').value = _currentProfile.email_secondary || '';
  document.getElementById('sensitive-phone-secondary').value = _currentProfile.phone_secondary || '';
  document.getElementById('sensitive-birth-date').value = _currentProfile.birth_date || '';
  document.getElementById('sensitive-address').value = _currentProfile.address || '';
  document.getElementById('sensitive-password').value = '';
  document.getElementById('edit-sensitive-msg').className = 'form-msg';
  document.getElementById('edit-sensitive-overlay').classList.add('open');
}
function closeEditSensitive(){
  document.getElementById('edit-sensitive-overlay').classList.remove('open');
}
async function saveSensitiveInfo(){
  const msgEl = document.getElementById('edit-sensitive-msg');
  const btn = document.getElementById('save-sensitive-btn');
  const password = document.getElementById('sensitive-password').value;
  if(!password){
    msgEl.textContent = 'Pro uložení zadej heslo.';
    msgEl.className = 'form-msg error';
    return;
  }
  const payload = {
    current_password: password,
    email_secondary: document.getElementById('sensitive-email-secondary').value.trim() || null,
    phone_secondary: document.getElementById('sensitive-phone-secondary').value.trim() || null,
    birth_date: document.getElementById('sensitive-birth-date').value || null,
    address: document.getElementById('sensitive-address').value.trim() || null,
  };
  btn.disabled = true; btn.textContent = 'Ukládám…';
  try{
    const res = await fetch('/profile/me/sensitive', {
      method: 'PUT',
      headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(!res.ok){
      msgEl.textContent = res.status === 401 ? 'Nesprávné heslo.' : (data.detail || 'Uložení se nezdařilo.');
      msgEl.className = 'form-msg error';
      btn.disabled = false; btn.textContent = 'Uložit';
      return;
    }
    _currentProfile = data;
    btn.disabled = false; btn.textContent = 'Uložit';
    closeEditSensitive();
  }catch(e){
    msgEl.textContent = 'Nepodařilo se spojit se serverem. Zkus to znovu.';
    msgEl.className = 'form-msg error';
    btn.disabled = false; btn.textContent = 'Uložit';
  }
}

function openEditProfile(){
  document.getElementById('edit-display-name').value = _currentProfile.display_name || '';
  document.getElementById('edit-first-name').value = _currentProfile.first_name || '';
  document.getElementById('edit-last-name').value = _currentProfile.last_name || '';
  document.getElementById('edit-nickname').value = _currentProfile.nickname || '';
  document.getElementById('edit-bio').value = _currentProfile.bio || '';
  document.getElementById('edit-education').value = _currentProfile.education || '';
  document.getElementById('edit-religion').value = _currentProfile.religion || '';
  document.getElementById('edit-sexual-preference').value = _currentProfile.sexual_preference || '';
  document.getElementById('edit-profile-msg').className = 'form-msg';
  document.getElementById('edit-profile-overlay').classList.add('open');
}
function closeEditProfile(){
  document.getElementById('edit-profile-overlay').classList.remove('open');
}
async function saveProfile(){
  const msgEl = document.getElementById('edit-profile-msg');
  const btn = document.getElementById('save-profile-btn');
  const payload = {
    display_name: document.getElementById('edit-display-name').value.trim() || null,
    first_name: document.getElementById('edit-first-name').value.trim() || null,
    last_name: document.getElementById('edit-last-name').value.trim() || null,
    nickname: document.getElementById('edit-nickname').value.trim() || null,
    bio: document.getElementById('edit-bio').value.trim() || null,
    education: document.getElementById('edit-education').value || null,
    religion: document.getElementById('edit-religion').value || null,
    sexual_preference: document.getElementById('edit-sexual-preference').value.trim() || null,
  };
  btn.disabled = true; btn.textContent = 'Ukládám…';
  try{
    const res = await fetch('/profile/me', {
      method: 'PUT',
      headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(!res.ok){
      msgEl.textContent = data.detail || 'Uložení se nezdařilo.';
      msgEl.className = 'form-msg error';
      btn.disabled = false; btn.textContent = 'Uložit';
      return;
    }
    _currentProfile = data;
    document.getElementById('profile-name').textContent = data.display_name || 'Bez jména';
    document.getElementById('profile-handle').textContent = '@' + (data.display_name ? data.display_name.toLowerCase().replace(/\s+/g,'') : 'uzivatel');
    document.getElementById('profile-bio').textContent = data.bio || 'Zatím žádné bio.';
    if(data.avatar_url) applyAvatar(data.avatar_url);
    document.getElementById('info-education').textContent = 'Vzdělání: ' + (data.education || 'nechci uvádět');
    document.getElementById('info-religion').textContent = 'Náboženství: ' + (data.religion || 'nechci uvádět');
    if(data.sexual_preference){
      document.getElementById('info-sexual-preference').textContent = data.sexual_preference;
      document.getElementById('info-sexual-preference-row').style.display = '';
    }else{
      document.getElementById('info-sexual-preference-row').style.display = 'none';
    }
    btn.disabled = false; btn.textContent = 'Uložit';
    closeEditProfile();
  }catch(e){
    msgEl.textContent = 'Nepodařilo se spojit se serverem. Zkus to znovu.';
    msgEl.className = 'form-msg error';
    btn.disabled = false; btn.textContent = 'Uložit';
  }
}
