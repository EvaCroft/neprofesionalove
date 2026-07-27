# DEVLOG (Active) – Neprofesionálové

**Projekt:** Neprofesionálové  
**Aktuální verze:** v27 ✅ HOTOVO — "O mně" & Veřejný profil (vlastní i cizí).  
**Stav bloku Profil/Vztahy:**
- **v27 ✅ HOTOVO:** "O mně" + Přátelé na VLASTNÍM profilu (#048). Veřejný profil `layout-profil-verejny.html` + `profil-verejny.js` (kostra, napojení na data, skrytí `ALWAYS_PRIVATE_FIELDS`, tlačítka Přidat do přátel / Sledovat) — v27a/b/c dokončeny v jednom kroku, backend endpointy (`friends.py`, `profile.py`) už existovaly, žádná backend úprava nebyla potřeba (#050).
- **v28 🔄 NEZAHÁJENO:** "Moje statistiky" + komunitní widgety na Přehledu.
- **v29 ✅ HOTOVO:** Osobní údaje (vzdělání, náboženství, sexuální preference) + kontakty přes `PUT /profile/me/sensitive` chráněné heslem (#049).

**Stav bloku Frontend / Design:**
- Hotové reálné stránky: `layout-dashboard.html`, `layout-auth.html`, `layout-user-profil.html`, `layout-wall.html`, `layout-media-galerie.html`, `layout-profil-verejny.html`.
- **Zbývá / Další krok:** 1. v28 – Moje statistiky & widgety.
  2. Frontend pro Chat místnosti + Messenger (`layout-chat-mistnost.html`, `layout-messenger.html`).

---

## 1. Aktuální rozpracované úkoly (Context pro další session)

### ✅ Dokončeno: v27 – Veřejný profil (`layout-profil-verejny.html`) (#050)
- **Stav:** Hotovo, v27a/b/c dokončeny naráz.
- Nový `frontend/layout-profil-verejny.html` (kostra podle `layout-user-profil.html`) + nový `frontend/profil-verejny.js` (vlastní modul, nezasahuje do `profil-core.js`).
- Napojení na `GET /profile/{id}`, `GET /profile/{id}/presence`, `GET /friends/counts/{id}` (guest-friendly) a `GET /friends/status/{id}` (jen přihlášení).
- Tlačítka **Přidat do přátel** / **Sledovat** volají existující v24 endpointy (`/friends/request`, `/accept`, `/cancel`, `/decline`, `/{id}`, `/follow/{id}`).
- `ALWAYS_PRIVATE_FIELDS` (e-maily, telefony, adresa, datum narození) ověřeny — filtrují se už v `app/routers/profile.py:read_public_profile`, frontend s nimi vůbec nepočítá.
- Žádná backend úprava nebyla potřeba — všechny použité endpointy už existovaly z v24/v26.

### Zabezpečení a citlivá data (v29 Summary)
- `PUT /profile/me/sensitive` vyžaduje `current_password`. Mění: `email_secondary`, `phone_secondary`, `birth_date`, `address`.
- Konstanta `ALWAYS_PRIVATE_FIELDS` na backendu striktně blokuje veřejné čtení těchto 4 polí.

### ✅ Dokončeno: Správa lokalit na vlastním profilu (backlog bod 4, #051)
- Backend (`app/models/profile_location.py`, `GET/POST/PUT/DELETE /profile/me/locations`) existoval už z v27 kvůli zobrazení lokalit na veřejném profilu — chybělo jen UI pro správu na vlastním profilu.
- Nové: sekce "Lokality" v kartě "O mně" na `layout-user-profil.html` (nahradila placeholder), modal pro přidání/úpravu, nový `frontend/profil-locations.js`.
- Limit **3 lokalit** (label + město + země + popis) vynucen frontendem — backend limit nemá.

---

## 2. Přehled otevřeného backlogu (Aktivní)
- **Chat místnosti & Messenger (Frontend UI):** Backend v3 (Messenger) a v4–v6 (Rooms) je hotový, chybí HTML/JS stránky.
- **Sdílený prohlížeč médií (`media-shared.js`):** Základní UI a akce hotové (#042). Chybí backend pro komentáře/lajky u médií, alba a tagování uživatelů.
- **Vlastní layouty uživatele (v20–v22 backlog):** Presety, export/import JSON (zatím nezahájeno).
- **Produkční tvrzení:** Zabezpečení JWT klíče do env, automatizované testy.

---

*Starší historie verzí (v1–v26) a log záznamy (#001–#049) byly přesunuty do `DEVLOG_archive_v25-v31.md`.*