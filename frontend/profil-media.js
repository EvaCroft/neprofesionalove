/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

const PLAY_ICON_SVG = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
const TRASH_ICON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m2 0v14a2 2 0 01-2 2H8a2 2 0 01-2-2V6h12z"/></svg>';

let _myMedia = [];

function _mediaTileHTML(asset, opts){
  opts = opts || {};
  const inner = window.MediaShared ? window.MediaShared.thumbHTML(asset) : '';
  const delBtn = opts.deletable === false ? '' : `<button class="media-del" title="Smazat" onclick="event.stopPropagation(); deleteMyMedia(${asset.id})">${TRASH_ICON_SVG}</button>`;
  return `<div class="media-tile" onclick="openMediaLightbox(${asset.id})">${inner}${delBtn}</div>`;
}

function _renderMediaEmptyOrGrid(gridEl, emptyEl, items, opts){
  if(!items.length){
    gridEl.innerHTML = '';
    if(emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if(emptyEl) emptyEl.style.display = 'none';
  gridEl.innerHTML = items.map(a => _mediaTileHTML(a, opts)).join('');
}

async function loadMyMedia(){
  const grid = document.getElementById('media-grid');
  const empty = document.getElementById('media-empty');
  const previewGrid = document.getElementById('media-preview-grid');
  try{
    const res = await fetch('/media?direction=uploaded&sort=newest&limit=48', { headers: authHeaders() });
    if(!res.ok) return;
    _myMedia = await res.json();
    _renderMediaEmptyOrGrid(grid, empty, _myMedia);
    if(previewGrid){
      if(_myMedia.length){
        previewGrid.innerHTML = _myMedia.slice(0, 4).map(a => _mediaTileHTML(a, { deletable:false })).join('');
      } else {
        previewGrid.innerHTML = '<div class="photo-tile"></div><div class="photo-tile"></div><div class="photo-tile"></div><div class="photo-tile"></div>';
      }
    }
  }catch(e){ /* necháme prázdný stav, pokud API neodpoví */ }
}

async function uploadMyMedia(fileList){
  const files = Array.from(fileList || []);
  if(!files.length) return;
  for(const file of files){
    if(!file.type.startsWith('image/') && !file.type.startsWith('video/')){
      alert(`Přeskočeno "${file.name}" — podporujeme jen obrázky a videa.`);
      continue;
    }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', 'direct_upload');
    try{
      const res = await fetch('/media/upload', { method:'POST', headers: authHeaders(), body: formData });
      const data = await res.json();
      if(!res.ok){
        alert(data.detail || `Nahrání "${file.name}" se nezdařilo.`);
        continue;
      }
      _myMedia.unshift(data);
    }catch(e){
      alert(`Nepodařilo se nahrát "${file.name}". Zkus to znovu.`);
    }
  }
  _renderMediaEmptyOrGrid(document.getElementById('media-grid'), document.getElementById('media-empty'), _myMedia);
  const previewGrid = document.getElementById('media-preview-grid');
  if(previewGrid) previewGrid.innerHTML = _myMedia.slice(0, 4).map(a => _mediaTileHTML(a, { deletable:false })).join('');
}

async function deleteMyMedia(mediaId){
  if(!confirm('Smazat toto médium? Tuto akci nejde vzít zpět.')) return;
  try{
    const res = await fetch(`/media/${mediaId}`, { method:'DELETE', headers: authHeaders() });
    if(!res.ok && res.status !== 204){
      alert('Smazání se nezdařilo.');
      return;
    }
    _myMedia = _myMedia.filter(a => a.id !== mediaId);
    _renderMediaEmptyOrGrid(document.getElementById('media-grid'), document.getElementById('media-empty'), _myMedia);
    const previewGrid = document.getElementById('media-preview-grid');
    if(previewGrid){
      previewGrid.innerHTML = _myMedia.length
        ? _myMedia.slice(0, 4).map(a => _mediaTileHTML(a, { deletable:false })).join('')
        : '<div class="photo-tile"></div><div class="photo-tile"></div><div class="photo-tile"></div><div class="photo-tile"></div>';
    }
    closeMediaLightbox();
  }catch(e){
    alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
  }
}

/* Otevírání/procházení/mazání médií teď řeší sdílený prohlížeč MediaShared.openViewer()
   (frontend/media-shared.js) — stejná logika jako v Galerii médií a u příspěvků na Zdi,
   viz DEVLOG #042. Seznam pro šipky = zdejší "Moje média" (_myMedia). */
function openMediaLightbox(mediaId){
  MediaShared.primeCache(_myMedia);
  MediaShared.openViewer(_myMedia.map(a => a.id), mediaId, {
    authHeaders: authHeaders(),
    onDelete: (deletedId) => {
      _myMedia = _myMedia.filter(a => a.id !== deletedId);
      _renderMediaEmptyOrGrid(document.getElementById('media-grid'), document.getElementById('media-empty'), _myMedia);
      const previewGrid = document.getElementById('media-preview-grid');
      if(previewGrid){
        previewGrid.innerHTML = _myMedia.length
          ? _myMedia.slice(0, 4).map(a => _mediaTileHTML(a, { deletable:false })).join('')
          : '<div class="photo-tile"></div><div class="photo-tile"></div><div class="photo-tile"></div><div class="photo-tile"></div>';
      }
    },
  });
}
function closeMediaLightbox(){
  MediaShared.closeViewer();
}
