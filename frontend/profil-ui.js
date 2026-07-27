/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

function toggleMode(){document.body.dataset.mode=document.body.dataset.mode==='light'?'dark':'light';}

function toggleDrop(name){
  const map={notif:'notif-drop',avatar:'avatar-drop',messages:'messages-drop'};
  document.querySelectorAll('.dropdown').forEach(d=>{ if(d.id!==map[name]) d.classList.remove('open'); });
  document.getElementById(map[name]).classList.toggle('open');
}
document.addEventListener('click', function(e){
  if(!e.target.closest('.icon-btn')){ document.querySelectorAll('.dropdown').forEach(d=>d.classList.remove('open')); }
});
function dockMode(mode, btn){
  document.querySelectorAll('.dock-mode-row button').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelector('.dock-quick').classList.toggle('hidden', mode!=='quick');
  document.querySelector('.dock-log').classList.toggle('active', mode==='log');
}
function showProfileTab(name, btn){
  document.querySelectorAll('.profile-tabs a').forEach(a=>a.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  if (name === 'zed') loadZedFeed();
  if (name === 'aktivita') loadActivity();
}
const _statsCycle = [
  {dot:'dot-green', text:'21 830 přihlášených'},
  {dot:'dot-pink', text:'4 698 webcam'},
  {dot:'dot-purple', text:'890 hrají'},
  {dot:'dot-blue', text:'1 903 kouká na videa'},
];
let _statIdx = 0;
function _cycleStat(){
  const el = document.getElementById('stat-item');
  if(!el) return;
  el.classList.add('leaving');
  setTimeout(()=>{
    _statIdx = (_statIdx+1) % _statsCycle.length;
    const s = _statsCycle[_statIdx];
    el.innerHTML = `<span class="dotc ${s.dot}"></span>${s.text}`;
    el.classList.remove('leaving');
    el.classList.add('entering');
    setTimeout(()=>el.classList.remove('entering'), 400);
  }, 400);
}
setInterval(_cycleStat, 3000);
