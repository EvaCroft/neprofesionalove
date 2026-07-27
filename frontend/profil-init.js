/* Rozděleno z profil.js (v30) — viz profil.js pro historii. */

/* Bootstrap volání — MUSÍ se načíst až po všech ostatních profil-*.js souborech,
   protože zde volané funkce jsou definované v nich (žádný modulový systém, jen
   sdílený global scope přes obyčejné <script> tagy v pořadí v HTML). */

loadProfileData().then(loadActivityPreview);
loadMyMedia();
loadMyEvents();
loadFriendRequests();
loadFriendCounts();
loadFriendsPreview();
loadPresence();
loadBadges();
