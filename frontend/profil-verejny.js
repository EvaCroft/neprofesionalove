/**
 * frontend/profil-verejny.js — v27b + v27c
 *
 * Napojení layout-profil-verejny.html na:
 *  - GET /profile/{id}            (v27b - data profilu)
 *  - GET /profile/{id}/presence   (v27b - online/aktivita)
 *  - GET /friends/counts/{id}     (v27c - guest-friendly čítače)
 *  - GET /friends/status/{id}     (v27c - jen přihlášení, pohání tlačítka)
 *  - POST/DELETE /friends/request,accept,cancel,decline,{id},follow/{id}
 *    (v27c - akce tlačítek Přidat do přátel / Sledovat)
 *
 * Vlastní modul podle vzoru profil-core.js / profil-ui.js atd.
 * (viz CONTEXT-MAP.md) — vědomě NEZASAHUJE do profil-core.js, ten patří
 * vlastnímu profilu.
 *
 * Bezpečnost citlivých údajů: birth_date / address / email_secondary /
 * phone_secondary (ALWAYS_PRIVATE_FIELDS, app/models/profile.py) se
 * odstraňují už na backendu v read_public_profile() - tento soubor s nimi
 * vůbec nepočítá a nikde je z `profile` objektu nečte. I kdyby se objevily
 * v odpovědi, tady se prostě nezobrazí, protože pro ně není žádný #pv-*
 * element.
 *
 * Ověřeno proti layout-auth.html:
 *   - JWT token je v localStorage pod klíčem 'np_token' (ne 'access_token',
 *     jak jsem původně hádal - opraveno).
 *   - Nepřihlášený návštěvník se posílá na 'layout-auth.html' (potvrzeno,
 *     tenhle odhad sedněl).
 *   - Backend běží na stejné origin jako frontend (relativní '/profile/...',
 *     '/friends/...') - podle fetch('/auth/login') v layout-auth.html.
 *
 * Jediné, co pořád jen předpokládám (auth.py jsem neviděl):
 *   - Chráněné endpointy čekají token v hlavičce 'Authorization: Bearer
 *     <token>' - běžná FastAPI konvence, stojí za ověření, až bude auth.py
 *     po ruce.
 *   - ID zobrazovaného profilu se čte z URL query parametru '?id=123' -
 *     nikde jsem zatím neviděl, jak appka na tuhle stránku vlastně
 *     odkazuje/naviguje (žádný odkaz na layout-profil-verejny.html jinde).
 *
 * PresenceOut (app/schemas/presence.py) je teď navázaný přesně:
 * { is_online: bool, last_active_at: datetime|null,
 *   activity: "playing"|"chatting"|null, activity_detail: string|null }.
 */
(function () {
  'use strict';

  function getViewedUserId() {
    var params = new URLSearchParams(window.location.search);
    var id = params.get('id');
    return id ? parseInt(id, 10) : null;
  }

  function authHeaders() {
    var token = null;
    try { token = localStorage.getItem('np_token'); } catch (e) { /* noop */ }
    return token ? { Authorization: 'Bearer ' + token } : {};
  }

  function fetchJson(url) {
    return fetch(url, { headers: authHeaders() }).then(function (res) {
      if (!res.ok) {
        var err = new Error('Request failed: ' + res.status);
        err.status = res.status;
        throw err;
      }
      return res.json();
    });
  }

  // POST/DELETE na akční endpointy (/friends/request, /accept, /follow...) -
  // žádné z nich nečekají tělo požadavku, jen path param.
  function apiRequest(method, url) {
    return fetch(url, { method: method, headers: authHeaders() }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (body) {
          var err = new Error(body.detail || ('Request failed: ' + res.status));
          err.status = res.status;
          throw err;
        });
      }
      if (res.status === 204) return null;
      return res.json();
    });
  }

  function isLoggedIn() {
    try { return !!localStorage.getItem('np_token'); } catch (e) { return false; }
  }

  function goToLogin() {
    // POZN.: layout-auth.html podle CONTEXT-MAP - uprav, pokud appka login
    // řeší jinak (modal, jiná cesta...).
    window.location.href = 'layout-auth.html';
  }

  // Stav vztahu k zobrazenému profilu - viz FriendRelationOut
  // (app/schemas/friendship.py): friend_status "none"|"pending_sent"|
  // "pending_received"|"friends", is_following, is_followed_by.
  var FRIEND_STATE = { userId: null, friend_status: 'none', is_following: false };

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
  }

  function displayName(profile) {
    if (profile.display_name) return profile.display_name;
    var full = [profile.first_name, profile.last_name].filter(Boolean).join(' ');
    if (full) return full;
    if (profile.nickname) return profile.nickname;
    return 'Uživatel #' + profile.user_id;
  }

  function showRow(rowId, valueId, value, formatter) {
    var row = document.getElementById(rowId);
    var span = document.getElementById(valueId);
    if (!row || !span) return;
    if (!value || (Array.isArray(value) && value.length === 0)) {
      row.style.display = 'none';
      return;
    }
    row.style.display = '';
    span.innerHTML = formatter ? formatter(value) : escapeHtml(value);
  }

  function renderLocations(locations) {
    var wrap = document.getElementById('pv-locations');
    if (!wrap) return;
    if (!locations || !locations.length) {
      wrap.innerHTML = '';
      return;
    }
    wrap.innerHTML = locations.map(function (loc) {
      var label = loc.label ? '<b>' + escapeHtml(loc.label) + ':</b> ' : '';
      var place = escapeHtml(loc.city) + (loc.country ? ', ' + escapeHtml(loc.country) : '');
      var desc = loc.description ? '<div style="font-size:.78rem;color:var(--text-2);margin-left:26px;">' + escapeHtml(loc.description) + '</div>' : '';
      return '<div class="info-row">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.1-7-11a7 7 0 0114 0c0 4.9-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>' +
        label + place + '</div>' + desc;
    }).join('');
  }

  function renderProfile(profile) {
    document.getElementById('pv-name').textContent = displayName(profile);

    showRow('row-handle', 'pv-handle', profile.nickname, function (v) { return '@' + escapeHtml(v); });

    var headerBio = document.getElementById('pv-header-bio');
    headerBio.textContent = profile.bio || '';
    headerBio.style.display = profile.bio ? '' : 'none';

    if (profile.avatar_url) {
      var avatar = document.getElementById('pv-avatar');
      avatar.style.backgroundImage = "url('" + profile.avatar_url + "')";
      avatar.style.backgroundSize = 'cover';
      avatar.style.backgroundPosition = 'center';
    }
    if (profile.cover_url) {
      var cover = document.getElementById('pv-cover');
      cover.style.backgroundImage = "url('" + profile.cover_url + "')";
      cover.style.backgroundSize = 'cover';
      cover.style.backgroundPosition = 'center';
    }

    showRow('row-city', 'pv-city', profile.city);

    var aboutBio = document.getElementById('pv-about-bio');
    aboutBio.textContent = profile.bio || 'Uživatel/ka zatím nic nenapsal/a.';

    showRow('row-orientation', 'pv-orientation', profile.orientation, function (v) { return '<b>Orientace:</b> ' + escapeHtml(v); });
    showRow('row-relationship', 'pv-relationship', profile.relationship_status, function (v) { return '<b>Vztah:</b> ' + escapeHtml(v); });
    showRow('row-seeking', 'pv-seeking', profile.seeking, function (v) { return '<b>Hledá:</b> ' + escapeHtml(v.join(', ')); });
    showRow('row-education', 'pv-education', profile.education, function (v) { return '<b>Vzdělání:</b> ' + escapeHtml(v); });
    showRow('row-religion', 'pv-religion', profile.religion, function (v) { return '<b>Vyznání:</b> ' + escapeHtml(v); });
    showRow('row-hobbies', 'pv-hobbies', profile.hobbies, function (v) { return '<b>Záliby:</b> ' + escapeHtml(v.join(', ')); });

    renderLocations(profile.locations);

    // sexual_preference je taky VISIBILITY_CONTROLLED_FIELDS a schválně tu
    // není zobrazené - nemám zadání, jestli/kde se má na veřejném profilu
    // ukazovat, ať nekreslím UI navíc bez rozhodnutí. Přidat je jednoduché,
    // stačí popsat, kam ve v27c/dalším kroku.
  }

  // Hrubé, jednoduché "před X min/h/dny" - žádná knihovna navíc jen kvůli
  // jednomu řádku textu.
  function formatRelativeTime(isoString) {
    if (!isoString) return null;
    var then = new Date(isoString).getTime();
    if (isNaN(then)) return null;
    var diffMin = Math.round((Date.now() - then) / 60000);
    if (diffMin < 1) return 'právě teď';
    if (diffMin < 60) return 'před ' + diffMin + ' min';
    var diffHod = Math.round(diffMin / 60);
    if (diffHod < 24) return 'před ' + diffHod + ' h';
    return 'před ' + Math.round(diffHod / 24) + ' dny';
  }

  function renderPresence(presence) {
    var row = document.getElementById('row-presence');
    var span = document.getElementById('pv-presence');
    if (!row || !span || !presence) { if (row) row.style.display = 'none'; return; }

    row.style.display = '';

    if (presence.is_online) {
      var label = 'Online';
      if (presence.activity === 'playing') {
        label = 'Hraje hru';
      } else if (presence.activity === 'chatting') {
        label = presence.activity_detail
          ? 'Chatuje v „' + escapeHtml(presence.activity_detail) + '“'
          : 'Chatuje';
      }
      span.innerHTML = '<span class="dotc dot-green" style="display:inline-block;margin-right:5px;"></span>' + label;
    } else {
      var rel = formatRelativeTime(presence.last_active_at);
      span.textContent = rel ? 'Naposledy online ' + rel : 'Offline';
    }
  }

  function setFriendButton(status) {
    var btn = document.getElementById('btn-friend');
    var label = btn.querySelector('.btn-label');
    btn.classList.remove('primary', 'ghost');
    switch (status) {
      case 'friends':
        btn.classList.add('ghost');
        label.textContent = 'Přátelé';
        break;
      case 'pending_sent':
        btn.classList.add('ghost');
        label.textContent = 'Žádost odeslána';
        break;
      case 'pending_received':
        btn.classList.add('primary');
        label.textContent = 'Přijmout žádost';
        break;
      default:
        btn.classList.add('primary');
        label.textContent = 'Přidat do přátel';
    }
  }

  function setFollowButton(isFollowing) {
    var btn = document.getElementById('btn-follow');
    btn.querySelector('.btn-label').textContent = isFollowing ? 'Sledováno' : 'Sledovat';
  }

  function renderRelation(relation) {
    FRIEND_STATE.friend_status = relation.friend_status;
    FRIEND_STATE.is_following = relation.is_following;
    setFriendButton(relation.friend_status);
    setFollowButton(relation.is_following);

    var badge = document.getElementById('pv-followed-by-badge');
    badge.style.display = relation.is_followed_by ? '' : 'none';
  }

  function renderCounts(counts) {
    document.getElementById('pv-friends-count').textContent = counts.friends_count;
    document.getElementById('pv-followers-count').textContent = counts.followers_count;
    document.getElementById('pv-following-count').textContent = counts.following_count;
  }

  function handleFriendClick() {
    if (!isLoggedIn()) { goToLogin(); return; }
    var userId = FRIEND_STATE.userId;
    var status = FRIEND_STATE.friend_status;
    var promise;

    if (status === 'none') {
      promise = apiRequest('POST', '/friends/request/' + userId)
        .then(function () { FRIEND_STATE.friend_status = 'pending_sent'; });
    } else if (status === 'pending_sent') {
      if (!window.confirm('Zrušit odeslanou žádost o přátelství?')) return;
      promise = apiRequest('DELETE', '/friends/cancel/' + userId)
        .then(function () { FRIEND_STATE.friend_status = 'none'; });
    } else if (status === 'pending_received') {
      promise = apiRequest('POST', '/friends/accept/' + userId)
        .then(function () { FRIEND_STATE.friend_status = 'friends'; });
    } else if (status === 'friends') {
      if (!window.confirm('Opravdu chcete zrušit přátelství?')) return;
      promise = apiRequest('DELETE', '/friends/' + userId)
        .then(function () { FRIEND_STATE.friend_status = 'none'; });
    } else {
      return;
    }

    promise
      .then(function () { setFriendButton(FRIEND_STATE.friend_status); })
      .catch(function (err) {
        console.error('friend action selhala', err);
        window.alert('Něco se nepovedlo, zkuste to prosím znovu.');
      });
  }

  function handleFollowClick() {
    if (!isLoggedIn()) { goToLogin(); return; }
    var userId = FRIEND_STATE.userId;
    var method = FRIEND_STATE.is_following ? 'DELETE' : 'POST';

    apiRequest(method, '/friends/follow/' + userId)
      .then(function () {
        FRIEND_STATE.is_following = !FRIEND_STATE.is_following;
        setFollowButton(FRIEND_STATE.is_following);
      })
      .catch(function (err) {
        console.error('follow action selhala', err);
        window.alert('Něco se nepovedlo, zkuste to prosím znovu.');
      });
  }

  function showState(state) {
    document.getElementById('profile-loading').style.display = state === 'loading' ? '' : 'none';
    document.getElementById('profile-content').style.display = state === 'content' ? '' : 'none';
    document.getElementById('profile-error').style.display = state === 'error' ? '' : 'none';
  }

  function init() {
    var userId = getViewedUserId();
    if (!userId) {
      console.error('profil-verejny.js: chybí ?id= v URL, nevím, čí profil zobrazit');
      showState('error');
      return;
    }
    FRIEND_STATE.userId = userId;

    document.getElementById('btn-friend').addEventListener('click', handleFriendClick);
    document.getElementById('btn-follow').addEventListener('click', handleFollowClick);

    showState('loading');

    fetchJson('/profile/' + userId)
      .then(function (profile) {
        renderProfile(profile);
        showState('content');

        // Presence, vztah (jen přihlášení) a čítače (guest-friendly) se
        // natahují samostatně a nesmí shodit zobrazení profilu, kdyby
        // některý endpoint spadl.
        fetchJson('/profile/' + userId + '/presence')
          .then(renderPresence)
          .catch(function (err) { console.warn('presence se nepodařilo načíst', err); });

        fetchJson('/friends/counts/' + userId)
          .then(renderCounts)
          .catch(function (err) { console.warn('friends/counts se nepodařilo načíst', err); });

        if (isLoggedIn()) {
          fetchJson('/friends/status/' + userId)
            .then(renderRelation)
            .catch(function (err) { console.warn('friends/status se nepodařilo načíst', err); });
        }
        // Nepřihlášený návštěvník vidí výchozí tlačítka ("Přidat do přátel"
        // / "Sledovat") a klik ho pošle na login - viz goToLogin().
      })
      .catch(function (err) {
        console.error('profil-verejny.js: profil se nepodařilo načíst', err);
        showState('error');
      });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
