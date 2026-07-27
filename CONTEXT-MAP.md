# CONTEXT-MAP – Neprofesionálové

Mapa **feature → soubory**. Účel: nová session si najde svou featuru a otevře
jen soubory uvedené u ní — nemusí procházet celý repo ani zbytek buildplanu.

**BUILDPLAN je rozdělen na 3 soubory podle domény/stavu, ne podle vrstvy
frontend/backend** (feature se vyvíjí vertikálně napříč vrstvami v jedné
session, proto nedává smysl řezat podle vrstvy — jen admin je natolik
izolovaná doména, že má vlastní soubor):
- `BUILDPLAN_core.md` — aktivní práce na hlavní appce (profil, vztahy, komunita...).
- `BUILDPLAN_admin.md` — celá admin doména (frontend i backend pohromadě).
- `BUILDPLAN_backlog.md` — nezahájené nápady čekající na zařazení.

Sdílené/core soubory (`app/db.py`, `app/auth.py`, `app/permissions.py`,
`app/logging_service.py`, `app/main.py`) jsou vypsané zvlášť dole — dotýkají
se jich jen úkoly, které mění autentizaci, práva nebo routing napříč appkou.

---

## Backend — podle domény

### Uživatelé & Auth
- `app/models/user.py`
- `app/schemas/auth.py`
- `app/routers/auth.py`
- `app/auth.py` (jen pokud se mění hashování/JWT logika)

### Profil (vlastní i veřejný, vč. citlivých údajů a lokalit)
- `app/models/profile.py`
- `app/models/profile_location.py`
- `app/schemas/profile.py`
- `app/routers/profile.py`
- `app/services/presence_service.py` (online status na profilu)

### Vztahy — přátelství & sledování
- `app/models/friendship.py`
- `app/models/follow.py`
- `app/schemas/friendship.py`
- `app/routers/friends.py`

### Odznaky (Badges)
- `app/models/badge.py`
- `app/schemas/badge.py`
- `app/routers/badges.py`

### Přítomnost & aktivita (online/chatuje/hraje, čítače)
- `app/models/activity_settings.py`
- `app/schemas/presence.py`
- `app/services/activity_service.py`
- `app/routers/activity.py`

### Messenger (přímé zprávy)
- `app/models/message.py`
- `app/schemas/messenger.py`
- `app/routers/messenger.py`

### Chat místnosti (Rooms)
- `app/models/room.py`
- `app/models/room_message.py`
- `app/schemas/rooms.py`
- `app/routers/rooms.py`

### Moderace (nahlášení, room moderátoři)
- `app/models/moderation.py`
- `app/schemas/moderation.py`
- `app/routers/moderation.py`

### Příspěvky & zeď (Posts / Wall)
- `app/models/post.py`
- `app/models/wall_settings.py`
- `app/schemas/posts.py`
- `app/services/post_service.py`
- `app/routers/posts.py`

### Média (upload, galerie, statistiky)
- `app/models/media.py`
- `app/schemas/media.py`
- `app/services/media_service.py`
- `app/routers/media.py`
- (napojuje se i na `post_service.py` kvůli "propsat na zeď")

### Peněženka & kredity (Wallet)
- `app/models/wallet.py`
- `app/models/withdrawal.py`
- `app/schemas/wallet.py`
- `app/services/credit_service.py`
- `app/routers/wallet.py`

### Aukce
- `app/models/auction.py`
- `app/schemas/auctions.py`
- `app/routers/auctions.py`
- (závisí na `rooms.py` — `_get_room_or_404`, `_is_member`)

### Hry
- `app/models/game.py`
- `app/schemas/games.py`
- `app/services/game_service.py`
- `app/routers/games.py`
- (závisí na `rooms.py`, `credit_service.py`)

### Události (Events)
- `app/models/event.py`
- `app/schemas/events.py`
- `app/routers/events.py`

### Referral systém
- `app/models/referral.py`
- `app/schemas/referral.py`
- `app/routers/referral.py`

### Admin & logy
- `app/models/log.py`
- `app/models/settings.py`
- `app/logging_service.py`
- Backend admin domény (rozděleno z původního `admin.py`, 406 řádků, vA5):
  - `app/routers/admin_users.py` — správa uživatelů a rolí
  - `app/routers/admin_moderation.py` — přiřazování room moderátorů
  - `app/routers/admin_logs.py` — čtení logů
  - `app/routers/admin_settings.py` — globální nastavení
  - `app/routers/admin_wallet.py` — admin topup/reward + schvalování výběrů
- Detailní plán admin frontendu i dalšího backend napojení: viz `BUILDPLAN_admin.md`.

---

## Frontend — podle stránky/featury

> ⚠️ **Duplikace design tokenů:** `:root` proměnné (`--accent`, `--bg`,
> `--radius`...) jsou teď zkopírované v každém page-specific CSS souboru
> (`profil.css`, `media-galerie.css`, do budoucna `wall.css`, `auth.css`...).
> Funguje to, ale škáluje to špatně — např. pro plánovaný live editor
> vzhledu (změna barvy by musela editovat N souborů místo jednoho).
> Konsolidace do sdíleného `frontend/design-system.css` je zapsaná jako
> předpoklad live editoru v `BUILDPLAN_backlog.md` (bod 6).


### Auth (login/register)
- `frontend/layout-auth.html` (má 112 řádků inline JS — kandidát na
  vytažení do `auth.js`)

### Dashboard / Přehled
- `frontend/layout-dashboard.html` (51 řádků inline JS)

### Vlastní profil
- `frontend/layout-user-profil.html` (jen kostra)
- `frontend/profil-core.js`
- `frontend/profil-ui.js`
- `frontend/profil-init.js`
- `frontend/profil-friends.js`
- `frontend/profil-badges.js`
- `frontend/profil-events.js`
- `frontend/profil-media.js`
- `frontend/profil-contact.js`
- `frontend/profil-wall-activity.js`
- `frontend/profil.css`
- → **vzorový modulární rozpad, používat i jinde**

### Veřejný profil (TBD — v27)
- `frontend/layout-profil-verejny.html` (zatím neexistuje)
- nový `frontend/profil-verejny.js` (doporučeno založit rovnou zvlášť,
  ne dopisovat do `profil-core.js`)

### Zeď (Wall)
- `frontend/layout-wall.html` (97 řádků inline JS)
- `frontend/posts-shared.js`

### Galerie médií
- `frontend/layout-media-galerie.html` (jen kostra — rozděleno)
- `frontend/media-galerie.css`
- `frontend/media-galerie.js`
- `frontend/media-shared.js`

### Chat místnosti / Messenger (frontend zatím neexistuje)
- `frontend/layout-chat-mistnost.html` (TBD)
- `frontend/layout-messenger.html` (TBD)

### Admin rozhraní (TBD — samostatná doména, viz BUILDPLAN_admin.md)
- `frontend/layout-admin.html` (zatím neexistuje)
- `frontend/admin-users.js`
- `frontend/admin-moderation.js`
- `frontend/admin-logs.js`
- `frontend/admin-settings.js`
- `frontend/admin-wallet.js`
- `frontend/admin-rooms.js`
- `frontend/admin-content.js` (moderace obsahu; později rozšířeno o lajky/komentáře — vA11)
- `frontend/admin-games.js`
- `frontend/admin-badges.js`
- `frontend/admin-events.js`
- `frontend/admin.css` (jen pokud chybí třídy z jiných layoutů)

---

## Kandidáti na další rozdělení (než začnou růst)

| Soubor | Řádků | Doporučení |
|---|---|---|
| `app/routers/games.py` | 406 | rozdělit po jednotlivých hrách, až přibude 2. typ hry |
| `frontend/layout-auth.html` | 112 řádků inline JS | vytáhnout do `auth.js` |
| `frontend/layout-wall.html` | 97 řádků inline JS | zvážit vytažení do `wall.js` (částečně už sdílí `posts-shared.js`) |

---

## Jak mapu používat

1. Nová session dostane: `PROJECT.md` + relevantní blok z `BUILDPLAN_core.md`
   / `BUILDPLAN_admin.md` / `BUILDPLAN_backlog.md` (podle domény) + soubory
   uvedené u dané featury zde. Nic víc na začátek nepotřebuje.
2. Pokud úkol prokazatelně sahá i mimo vypsané soubory (např. nová featura
   volá `credit_service.py`), přidej řádek do příslušné sekce zde, ať to
   příští session už najde rovnou.
3. Po dokončení featury zkontroluj, jestli nenarostl některý soubor přes
   ~250–300 řádků — pokud ano, přidej ho do tabulky "Kandidáti na další
   rozdělení" výše.
