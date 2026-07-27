# BUILDPLAN (Active) – Neprofesionálové

**Aktuální verze:** v29 ✅ HOTOVO  
**Aktivní blok:** Reálný design appky & Rozšířený profil / Vztahy / Sdílené komponenty

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

> Detailní mapa feature → soubory pro celý projekt: viz `CONTEXT-MAP.md`.
> Nová session pro v27x/v28x potřebuje jen: `PROJECT.md`, tento blok a
> soubory vypsané u konkrétní sub-položky — ne celý BUILDPLAN ani zbytek repa.

---

## 🆕 Rozpracované & plánované úkoly k zařazení do vývoje

### 1. 🔔 Systém notifikací (Notification System)
*Cíl: Komplexní notifikační centrum pro upozorňování uživatelů na události napříč aplikací.*
- [ ] **Backend infrastructure:**
  - Datový model `Notification` (typ, adresát, příznak přečtení, navázaný objekt ID, čas vytvoření).
  - API endpointy (`GET /notifications`, `PUT /notifications/{id}/read`, `PUT /notifications/read-all`).
  - Triggery pro události:
    - Označení v příspěvku / médiu / komentáři (@zmínky, tagy).
    - Žádosti o přátelství / nové sledování.
    - Zprávy v Messengeru a zmínky v chatovacích místnostech.
    - Systémové notifikace a upozornění k událostem/aukcím.
- [ ] **Frontend UI:**
  - Globální indikátor notifikací v hlavičce (zvoneček s čítačem nepřečtených).
  - Rozbalovací panel / Centrum notifikací s filtrem (Vše / Nepřečtené / Zmínky / Vztahy).

### 2. 🏷️ Označování osob a míst (Mentions & Tagging System)
*Cíl: Univerzální systém označování uživatelů a lokalit napříč obsahy (příspěvky, média, komentáře).*
- [ ] **Označování lidí (People Tagging & @Mentions):**
  - Našeptávač uživatelů/přátel při psaní `@` nebo v políčku "Označit lidi" (v modalu nahrávání / editoru příspěvku).
  - Generování notifikace pro označené uživatele.
  - Zobrazení vazby v detailu média / příspěvku s proklikem na profil označené osoby.
- [ ] **Označování lokalit/míst (Location Tagging):**
  - Autocomplete / vyhlašovací pole pro volbu či zadání místa (např. v modalu nahrávání či příspěvku na zeď).
  - Zobrazení lokality u příspěvku / média.
  - Možnost filtrace médií a příspěvků podle konkrétního místa.

### 3. 🖼️ Sdílená funkce / Modal pro nahrávání médií (`media-upload-modal`)
*Cíl: Univerzální modalové okno pro nahrávání médií použitelné napříč aplikací (Profil, Galerie, Zeď).*
- [ ] **UI Modalu (Trigger na tlačítko "Nahrát"):**
  - **Soubory:** Výběr/přetažení jednoho nebo více médií (obrázky/videa).
  - **Základní údaje:** Název média, Popisek.
  - **Metadata & Označení:**
    - Označení lidí (tagování uživatelů).
    - Označení místa (lokalita/místo vzniku).
    - Datum (volba vlastního data pro zpětné zařazení na časovou osu / timeline).
    - Nastavení viditelnosti (Veřejný / Přátelé / Soukromý).
  - **Propojení se zdí:** Volba/checkbox "Propsat na zeď".
- [ ] **Backend & Logic:**
  - Automatické vytvoření příspěvku (Post) na zdi s navázanými nahrávanými médii a tagy uživatelů/místa + vyvolání notifikací pro označené osoby.

### 4. 📍 Dokončení správy lokalit na profilu (`Profile Locations`)
*Cíl: Rozšíření jednoplátkového pole adresy na plnohodnotnou správu až 3 lokalit uživatele.*
- [ ] **UI & Formátování na profilu:**
  - Nahradit jedno pole pro adresu formulářem/rozhraním pro **až 3 lokality** (Lokalita 1, Lokalita 2, Lokalita 3).
  - Každá lokalita bude obsahovat:
    - **Název lokality** (např. *Domov*, *Práce*, *Chata na horách*).
    - **Adresu / Místo**.
    - **Popis lokality** (doplňující text/poznámka).
- [ ] **Backend napojení:**
  - Úprava datového modelu profilu / citlivých údajů pro uložení strukturovaného pole lokalit.