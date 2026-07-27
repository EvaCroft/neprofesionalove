/* ============================================================
   posts-shared.js — sdílená logika pro příspěvky na Zdi.
   Používá frontend/layout-wall.html i tab "Zeď" v layout-user-profil.html.

   Cíl: jedno místo pro renderování/načítání/odesílání příspěvků, aby
   budoucí rozšíření (foto/video/gif u příspěvku) stačilo udělat jen tady.

   Tento soubor sám neřeší autentizaci - volající stránka mu v cfg
   předá vlastní auth hlavičky (authHeaders) a případně vlastní user_id (meId).
============================================================ */
(function (global) {
  const VIS_LABEL = { public: 'Veřejné', friends: 'Jen přátelé', private: 'Soukromé' };
  const ACTION_LABEL = { media_upload: 'Nahrání fotky/videa na zeď', event_created: 'Založení události' };

  const _nameCache = {};
  async function authorName(userId, authHeaders) {
    if (_nameCache[userId]) return _nameCache[userId];
    try {
      const res = await fetch(`/profile/${userId}`, { headers: authHeaders });
      if (res.ok) {
        const p = await res.json();
        _nameCache[userId] = p.display_name || `Uživatel #${userId}`;
        return _nameCache[userId];
      }
    } catch {}
    return `Uživatel #${userId}`;
  }

  function fmtTime(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString('cs-CZ', { day: 'numeric', month: 'short' }) + ' · ' + d.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * Vyrenderuje jeden příspěvek.
   * cfg: { authHeaders, meId, onDelete, variant }
   *   variant 'card' (výchozí) - vlastní plovoucí .card, viz layout-wall.html
   *   variant 'row'  - řádek do seznamu uvnitř už existující .card, viz tab Zeď v profilu
   */
  function renderPostCard(post, cfg) {
    cfg = cfg || {};
    const variant = cfg.variant || 'card';
    const el = document.createElement('div');

    if (variant === 'row') {
      el.className = 'post';
      el.innerHTML = `
        <div class="post-head"><div class="avatar-sm"></div><div><b class="post-author"></b><span>${fmtTime(post.created_at)}</span></div></div>
        ${post.text ? '<div class="post-text"></div>' : ''}
        ${post.media_id ? '<div class="post-media"></div>' : ''}
      `;
    } else {
      el.className = 'card post-card';
      const originLabel = post.origin === 'system_generated' ? (ACTION_LABEL[post.source_action] || 'Automatický záznam') : null;
      el.innerHTML = `
        <div class="post-head">
          <div class="post-avatar"></div>
          <div class="post-meta">
            <b class="post-author">Uživatel #${post.author_id}</b>
            <span>${fmtTime(post.created_at)}<span class="vis-chip">${VIS_LABEL[post.visibility] || post.visibility}</span>${originLabel ? `<span class="origin-chip">· ${originLabel}</span>` : ''}</span>
          </div>
        </div>
        ${post.text ? `<div class="post-text"></div>` : ''}
        ${post.media_id ? `<div class="post-media"></div>` : ''}
        <div class="post-actions"></div>
      `;
    }

    authorName(post.author_id, cfg.authHeaders).then(name => { el.querySelector('.post-author').textContent = name; });
    if (post.text) el.querySelector('.post-text').textContent = post.text; // textContent kvůli XSS
    if (post.media_id) {
      const mediaEl = el.querySelector('.post-media');
      if (mediaEl && global.MediaShared) {
        // clickable:false - klik neotevírá surový soubor v novém panelu, ale sdílený
        // prohlížeč (MediaShared.openViewer), se šipkami mezi VŠEMI médii aktuálně
        // načteného feedu (cfg.wallMediaIds, naplněné v loadWall níže), ne jen tímhle
        // jedním - viz DEVLOG #042.
        global.MediaShared.renderInto(mediaEl, post.media_id, cfg.authHeaders, { clickable: false });
        mediaEl.style.cursor = 'pointer';
        mediaEl.onclick = () => {
          const ids = (cfg.wallMediaIds && cfg.wallMediaIds.length) ? cfg.wallMediaIds : [post.media_id];
          global.MediaShared.openViewer(ids, post.media_id, {
            authHeaders: cfg.authHeaders,
            onDelete: () => { if (cfg.onMediaDeleted) cfg.onMediaDeleted(); },
          });
        };
      }
    }

    if (variant !== 'row' && cfg.meId != null && (cfg.meId === post.author_id || cfg.meId === post.target_user_id) && cfg.onDelete) {
      const del = document.createElement('button');
      del.textContent = 'Smazat';
      del.onclick = () => cfg.onDelete(post.id);
      el.querySelector('.post-actions').appendChild(del);
    }
    return el;
  }

  /**
   * Načte a vykreslí zeď uživatele do feedEl.
   * cfg: { targetUserId, feedEl, emptyEl, authHeaders, meId, onDelete, onMediaDeleted, variant }
   */
  async function loadWall(cfg) {
    const res = await fetch(`/posts/wall/${cfg.targetUserId}`, { headers: cfg.authHeaders });
    if (!res.ok) return;
    const posts = await res.json();
    cfg.feedEl.innerHTML = '';
    cfg.feedEl.style.display = posts.length ? '' : 'none';
    if (cfg.emptyEl) cfg.emptyEl.style.display = posts.length ? 'none' : '';
    // Pořadí médií pro šipky v MediaShared.openViewer - všechna média aktuálně
    // načtené zdi, v pořadí, v jakém jsou vykreslené (nejnovější nahoře).
    const wallMediaIds = posts.filter(p => p.media_id).map(p => p.media_id);
    posts.forEach(p => cfg.feedEl.appendChild(renderPostCard(p, Object.assign({}, cfg, { wallMediaIds }))));
  }

  /**
   * Odešle nový příspěvek z composeru.
   * cfg: { textEl, visibilityEl, submitBtn, authHeaders, targetUserId, onSuccess }
   */
  async function submitPost(cfg) {
    const text = cfg.textEl.value.trim();
    if (!text) return;
    const visibility = cfg.visibilityEl.value;
    cfg.submitBtn.disabled = true;
    try {
      const res = await fetch('/posts', {
        method: 'POST',
        headers: Object.assign({ 'Content-Type': 'application/json' }, cfg.authHeaders),
        body: JSON.stringify({ text, visibility, target_user_id: cfg.targetUserId || null }),
      });
      if (res.ok) {
        cfg.textEl.value = '';
        if (cfg.onSuccess) cfg.onSuccess();
      }
    } finally {
      cfg.submitBtn.disabled = false;
    }
  }

  /** cfg: { authHeaders, onSuccess } */
  async function deletePost(id, cfg) {
    if (!confirm('Smazat tento příspěvek?')) return;
    const res = await fetch(`/posts/${id}`, { method: 'DELETE', headers: cfg.authHeaders });
    if (res.ok && cfg.onSuccess) cfg.onSuccess();
  }

  global.PostsShared = { VIS_LABEL, ACTION_LABEL, fmtTime, authorName, renderPostCard, loadWall, submitPost, deletePost };
})(window);
