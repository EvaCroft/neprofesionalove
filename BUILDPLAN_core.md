# BUILDPLAN_core (Active) – Neprofesionálové

**Aktuální verze:** v28a ✅ HOTOVO
**Aktivní blok:** v28b — Komunitní widgety na Přehledu

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
- [x] ✅ **v27 — "O mně" & Veřejný profil:**
  - [x] Vlastní profil (online status, trvalé statistiky, přátelé) — HOTOVO (#048).
  - [x] **v27a — Kostra veřejného profilu** — HOTOVO.
    - `frontend/layout-profil-verejny.html` vytvořen podle rozložení `layout-user-profil.html`.
  - [x] **v27b — Napojení na data + skrytí citlivých polí** — HOTOVO.
    - `frontend/profil-verejny.js` napojen na `GET /profile/{id}` + `GET /profile/{id}/presence` + `GET /friends/counts/{id}`. `ALWAYS_PRIVATE_FIELDS` ověřeny — filtrují se už v `app/routers/profile.py:read_public_profile`, frontend s nimi vůbec nepracuje.
  - [x] **v27c — Akční tlačítka Přidat do přátel / Sledovat** — HOTOVO.
    - Tlačítka v `profil-verejny.js` volají existující v24 endpointy (`/friends/request`, `/accept`, `/cancel`, `/decline`, `/{id}`, `/follow/{id}`) a čtou stav z `GET /friends/status/{id}` — endpoint už existoval, žádná backend úprava nebyla potřeba.
- [ ] 🔄 **v28 — Moje statistiky & Komunitní widgety:**
  - [x] **v28a — Přejmenování a rozšíření vlastních statistik** — HOTOVO.
    - "Statistiky" → "Moje statistiky" na `layout-user-profil.html`.
    - `GET /profile/me` nově vrací `games_count` (dokončené hry, 1v1 i týmové), `events_count` (distinct účasti), `media_count` (vše nahrané uživatelem) — transientní hodnoty dopočítané v `app/routers/profile.py`, žádná DB migrace, jen čtení `games.py`/`events.py`/`media.py` modelů.
    - Veřejný profil (`read_public_profile`) tato čísla nepočítá, zůstávají na výchozí 0 (schéma je sdílené, ale pole má smysl jen na vlastním profilu).
  - [ ] **v28b — Komunitní widgety na Přehledu**
    - Cíl: widgety (přátelé, přátelé přátel, klubovny, události, hry) na `layout-dashboard.html`.
    - Soubory: `frontend/layout-dashboard.html`, nový `frontend/dashboard-widgets.js` (nedávat inline — dashboard má už 51 řádků inline JS, nerozšiřovat je), `app/routers/friends.py`, `app/routers/rooms.py`, `app/routers/events.py`, `app/routers/games.py` (jen nové read-only endpointy pro souhrnná čísla, pokud chybí).

### Zbývá / Další krok (mimo v27/v28)
- Frontend pro Chat místnosti + Messenger (`layout-chat-mistnost.html`, `layout-messenger.html`).

> Detailní mapa feature → soubory pro celý projekt: viz `CONTEXT-MAP.md`.
