# BUILDPLAN_admin (Active) – Neprofesionálové

**Stav:** 🔄 ROZPRACOVÁNO — samostatná doména, nezávislá na `BUILDPLAN_core.md`.

> **Konvence pro tento blok:** Frontend se staví napřed i tam, kde backend
> chybí nebo je neúplný. Místo blokace se použije mock/placeholder data
> a záznam do tabulky "Čeká na backend napojení" na konci tohoto souboru —
> až se bude psát backend, tahle tabulka řekne přesně, co který frontend
> očekává za tvar dat a endpointy.
>
> Nová session pro vAx potřebuje: `PROJECT.md`, tento soubor a soubory
> vypsané u sub-položky (viz i `CONTEXT-MAP.md` sekce "Admin rozhraní"
> a "Admin & logy") — case-by-case, ne celý backend admin domény naráz.

---

## Backend (hotovo — vA5)

Původní `app/routers/admin.py` byl rozdělen podle skutečného obsahu na
5 souborů, všechny pod stejným prefixem `/admin` (API cesty se nemění):

- [x] ✅ `app/routers/admin_users.py` — `/admin/users`, `/admin/users/{id}/role`
- [x] ✅ `app/routers/admin_moderation.py` — `/admin/moderators` (assign/unassign)
- [x] ✅ `app/routers/admin_logs.py` — `/admin/logs`
- [x] ✅ `app/routers/admin_settings.py` — `/admin/settings`
- [x] ✅ `app/routers/admin_wallet.py` — `/admin/wallet/*`, `/admin/withdraw-requests*`
- [x] ✅ `app/main.py` — přeregistrace na 5 routerů místo jednoho

## Frontend (plán)

- [ ] **vA1 — Kostra admin frontendu**
  - Cíl: nový statický `layout-admin.html` (layout/menu sekcí: Uživatelé, Moderace, Logy, Nastavení, Wallet, Místnosti, Obsah, Hry, Odznaky, Události).
  - Soubory: `frontend/layout-admin.html`, `frontend/admin.css` (jen pokud chybí třídy).
  - Bez zásahu do backendu.
- [ ] **vA2 — Správa uživatelů (UI + napojení)**
  - Cíl: výpis/filtr uživatelů, změna role, ban/unban.
  - Soubory: `frontend/admin-users.js`, `app/routers/admin_users.py`.
- [ ] **vA3 — Prohlížení logů (UI + napojení)**
  - Cíl: filtrovatelný výpis logů (11 typů dle PROJECT.md).
  - Soubory: `frontend/admin-logs.js`, `app/routers/admin_logs.py`, `app/logging_service.py` (jen čtení).
- [ ] **vA4 — Globální nastavení (UI + napojení)**
  - Cíl: editace globálních nastavení appky.
  - Soubory: `frontend/admin-settings.js`, `app/routers/admin_settings.py`, `app/models/settings.py`.
- [ ] **vA5b — Moderace (přiřazení room moderátorů)**
  - Cíl: UI pro assign/unassign moderátorů místností.
  - Soubory: `frontend/admin-moderation.js`, `app/routers/admin_moderation.py`.
- [ ] **vA6 — Správa chat místností**
  - Cíl: přehled místností, force-close/smazání místnosti, náhled provozu.
  - Soubory: `frontend/admin-rooms.js`, `app/routers/rooms.py` (jen nové read/admin-akce endpointy, pokud chybí).
- [ ] **vA7 — Správa profilového a mediálního obsahu uživatelů**
  - Cíl: moderace/mazání příspěvků na zdi a médií v galerii (např. na základě nahlášení).
  - Soubory: `frontend/admin-content.js`, `app/routers/posts.py`, `app/routers/media.py`, `app/models/moderation.py` (návaznost na existující report frontu).
- [ ] **vA8 — Správa her**
  - Cíl: přehled aktivních her, force-end, statistiky.
  - Soubory: `frontend/admin-games.js`, `app/routers/games.py`.
- [ ] **vA9 — Správa systému odznaků**
  - Cíl: CRUD katalogu odznaků (v25 má zatím jen 15 výchozích, pevně daných).
  - Soubory: `frontend/admin-badges.js`, `app/routers/badges.py`, `app/models/badge.py`.
- [ ] **vA10 — Správa událostí (Events)**
  - Cíl: přehled/editace/mazání událostí adminem.
  - Soubory: `frontend/admin-events.js`, `app/routers/events.py`.
- [ ] **vA11 — Správa systému lajků a komentářů (frontend napřed)**
  - Cíl: UI pro moderaci lajků/komentářů u médií — na mock datech, dokud backend neexistuje.
  - Soubory: `frontend/admin-content.js` (rozšíření vA7).
  - Zápis do tabulky níže: `media_like.py`, `media_comment.py` a odpovídající endpointy.

---

## 📋 Čeká na backend napojení (Admin frontend)

| Frontend soubor | Co používá mock data | Očekávaný endpoint / model | Poznámka |
|---|---|---|---|
| `admin-badges.js` | CRUD katalogu odznaků | `POST/PUT/DELETE /admin/badges` | zatím jen 15 pevných odznaků, žádný CRUD na backendu |
| `admin-content.js` | Lajky u médií | `GET/DELETE /admin/media/{id}/likes` | model `media_like.py` zatím neexistuje |
| `admin-content.js` | Komentáře u médií | `GET/DELETE /admin/media/{id}/comments` | model `media_comment.py` zatím neexistuje |
| `admin-rooms.js` | Force-close místnosti | `PUT /admin/rooms/{id}/close` | ověřit před psaním, jestli náhodou už není v `rooms.py` |

## Kandidáti na další rozdělení (než začnou růst)

Sledovat velikost `admin_wallet.py` a `admin_users.py` po přidání vA2/vA6/vA7 —
pokud některý přeroste ~250–300 řádků, rozdělit dál (stejný princip jako u
`app/routers/games.py` v hlavním `CONTEXT-MAP.md`).
