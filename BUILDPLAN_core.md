# BUILDPLAN_core (Active) – Neprofesionálové

**Aktuální verze:** v29 ✅ HOTOVO
**Aktivní blok:** Reálný design appky & Rozšířený profil / Vztahy / Sdílené komponenty

> Tento soubor pokrývá hlavní appku (ne admin — viz `BUILDPLAN_admin.md`,
> ne backlog nápadů — viz `BUILDPLAN_backlog.md`). Nová session pro
> core featury potřebuje jen: `PROJECT.md`, tento soubor a soubory
> vypsané u konkrétní sub-položky v `CONTEXT-MAP.md`.

---

## Přehled aktivního plánu

### 🔄 Blok: Profil, Vztahy & Komunita (v24–v28)
- [x] ✅ **v24 — Vztahy:** Backend pro žádosti o přátelství + follow systém (#045).
- [x] ✅ **v25 — Odznaky:** Katalog 15 výchozích odznaků, možnost výběru až 5 na profilu (#046).
- [x] ✅ **v26 — Přítomnost + čítače:** Online/chatuje/hraje status, čítače zobrazení profilu a času v chatu (#047).
- [ ] 🔄 **v27 — "O mně" & Veřejný profil:**
  - [x] Vlastní profil (online status, trvalé statistiky, přátelé) — HOTOVO (#048).
  - [ ] **v27a — Kostra veřejného profilu**
    - Cíl: nový statický `layout-profil-verejny.html` (jen HTML/CSS layout, bez logiky), vycházející z rozložení `layout-user-profil.html`.
    - Soubory: nový `frontend/layout-profil-verejny.html`, `frontend/profil.css` (jen pokud chybí třídy).
    - Bez zásahu do backendu.
  - [ ] **v27b — Napojení na data + skrytí citlivých polí**
    - Cíl: `GET /profile/{id}` vrací veřejná data, `ALWAYS_PRIVATE_FIELDS` zůstávají skryté i pro přihlášeného cizího uživatele.
    - Soubory: `frontend/layout-profil-verejny.html`, nový `frontend/profil-verejny.js` (nezasahovat do `profil-core.js` — vlastní modul dle vzoru profilu), `app/routers/profile.py`.
  - [ ] **v27c — Akční tlačítka Přidat do přátel / Sledovat**
    - Cíl: tlačítka volají existující v24 endpointy, mění stav podle `GET /friends/status/{id}`.
    - Soubory: `frontend/profil-verejny.js`, `app/routers/friends.py` (jen pokud chybí `GET /friends/status/{id}` — ověřit před úpravou).
- [ ] 🔄 **v28 — Moje statistiky & Komunitní widgety:**
  - [ ] **v28a — Přejmenování a rozšíření vlastních statistik**
    - Cíl: "Statistiky" → "Moje statistiky" na vlastním profilu + herní/event/media čísla.
    - Soubory: `frontend/layout-user-profil.html`, `frontend/profil-ui.js`, `app/routers/profile.py` (rozšíření response o počty her/eventů/médií — zdroje dat: `app/routers/games.py`, `app/routers/events.py`, `app/routers/media.py` jen ke čtení modelů, ne k úpravě).
  - [ ] **v28b — Komunitní widgety na Přehledu**
    - Cíl: widgety (přátelé, přátelé přátel, klubovny, události, hry) na `layout-dashboard.html`.
    - Soubory: `frontend/layout-dashboard.html`, nový `frontend/dashboard-widgets.js` (nedávat inline — dashboard má už 51 řádků inline JS, nerozšiřovat je), `app/routers/friends.py`, `app/routers/rooms.py`, `app/routers/events.py`, `app/routers/games.py` (jen nové read-only endpointy pro souhrnná čísla, pokud chybí).

### Zbývá / Další krok (mimo v27/v28)
- Frontend pro Chat místnosti + Messenger (`layout-chat-mistnost.html`, `layout-messenger.html`).

> Detailní mapa feature → soubory pro celý projekt: viz `CONTEXT-MAP.md`.
