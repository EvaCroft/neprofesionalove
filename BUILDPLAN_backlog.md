# BUILDPLAN_backlog – Neprofesionálové

**Stav:** 🆕 Rozpracované & plánované úkoly k zařazení do vývoje.

> Věci odsud se přesouvají do `BUILDPLAN_core.md` nebo `BUILDPLAN_admin.md`
> ve chvíli, kdy se na nich reálně začne pracovat — tenhle soubor drží jen
> to, co ještě čeká na zařazení.

---

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

### 4. ✅ Dokončení správy lokalit na profilu (`Profile Locations`)
*Hotovo — přesunuto z backlogu, viz DEVLOG #051. Backend (`ProfileLocation`
model, `GET/POST/PUT/DELETE /profile/me/locations`) existoval už z v27,
chybělo jen UI na vlastním profilu.*
- [x] **UI & Formátování na profilu:**
  - `frontend/layout-user-profil.html` — sekce "Lokality" v kartě "O mně" (nahradila placeholder "Lokace a zájmy — brzy"), nový modal pro přidání/úpravu.
  - Nový `frontend/profil-locations.js` — CRUD napojený na `/profile/me/locations`, limit **3 lokalit** vynucen frontendem (backend limit nemá).
  - Každá lokalita: **Název** (label), **Město** (povinné), **Země** (nepovinné), **Popis** (nepovinné).
- [x] **Backend napojení:** Nebylo potřeba — `ProfileLocation` + CRUD endpointy už existovaly z v27 (kvůli zobrazení na veřejném profilu).

### 5. 💬 Systém lajků a komentářů u médií
*Cíl: Chybějící backend pro interakce s médii (viz DEVLOG backlog).*
- [ ] Nové modely `app/models/media_like.py`, `app/models/media_comment.py`.
- [ ] Endpointy v `app/routers/media.py` (přidat/odebrat lajk, přidat/smazat komentář, výpis).
- [ ] Alba a tagování uživatelů u médií (souvisí s bodem 2 výše).
- [ ] Admin moderace nad touto featurou už je zapsaná v `BUILDPLAN_admin.md` (vA11).

### 6. 🎨 Konsolidace design tokenů (`design-system.css`) — předpoklad Live editoru vzhledu
*Cíl: Sjednotit `:root` proměnné (`--bg`, `--accent`, `--radius`, fonty...),
teď zkopírované v každém page-specific CSS (`profil.css`,
`media-galerie.css`, do budoucna `wall.css`, `auth.css`...), do jednoho
sdíleného `frontend/design-system.css`, na který se ostatní CSS napojí.*
- [ ] Vytvořit `frontend/design-system.css` s `:root` + `[data-mode="dark"]`
      proměnnými a společnými base pravidly (`*`, `html`, `body`, `.orb`,
      `.panel-*`, `.app-header`, `.card`...), která se dnes opakují v každém
      page CSS.
- [ ] Každý layout přidá `<link rel="stylesheet" href="design-system.css">`
      **před** svůj page-specific CSS link (pořadí kvůli přepisování
      pravidel).
- [ ] Odstranit zkopírované base bloky z `profil.css`, `media-galerie.css`
      (a dalších, jak vzniknou) — zůstane v nich jen to, co je pro danou
      stránku specifické.
- [ ] **Blokátor pro:** plánovaný live editor vzhledu — bez konsolidace by
      editor musel zapisovat do N souborů najednou při každé změně barvy/
      radiusu/fontu, což je křehké a chybové. Tenhle bod je proto potřeba
      dokončit před zahájením práce na editoru, ne souběžně s ním.


- Zabezpečení JWT klíče do env.
- Automatizované testy.
