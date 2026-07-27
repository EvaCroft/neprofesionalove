# DEVLOG (Active) – Neprofesionálové

**Projekt:** Neprofesionálové  
**Aktuální verze:** v29 ✅ HOTOVO (staticky ověřeno) — Osobní údaje & zabezpečené kontakty (zařazeno mimo pořadí).  
**Stav bloku Profil/Vztahy:**
- **v27 🔄 AKTIVNÍ / ROZPRACOVÁNO:** "O mně" + Přátelé na VLASTNÍM profilu hotovo (#048). **Zbývá:** samostatný veřejný profil (`layout-profil-verejny.html`) + akční tlačítka Přidat do přátel / Sledovat.
- **v28 🔄 NEZAHÁJENO:** "Moje statistiky" + komunitní widgety na Přehledu.
- **v29 ✅ HOTOVO:** Osobní údaje (vzdělání, náboženství, sexuální preference) + kontakty přes `PUT /profile/me/sensitive` chráněné heslem (#049).

**Stav bloku Frontend / Design:**
- Hotové reálné stránky: `layout-dashboard.html`, `layout-auth.html`, `layout-user-profil.html`, `layout-wall.html`, `layout-media-galerie.html`.
- **Zbývá / Další krok:** 1. Dokončení v27 – vytvoření `layout-profil-verejny.html`.
  2. Dokončení v28 – Moje statistiky & widgety.
  3. Frontend pro Chat místnosti + Messenger (`layout-chat-mistnost.html`, `layout-messenger.html`).

---

## 1. Aktuální rozpracované úkoly (Context pro další session)

### Rozpracováno: v27 – Veřejný profil (`layout-profil-verejny.html`)
- **Stav:** Na vlastním profilu jsou sekce "O mně", presence i přátelé zapojené (#048).
- **Cíl:** Vytvořit samostatný soubor `layout-profil-verejny.html` pro prohlížení cizího profilu.
- **Požadavky:**
  - Napojení na `GET /profile/{id}` a `GET /friends/status/{id}`.
  - Tlačítka **Přidat do přátel** / **Sledovat** (využívající již hotové backend endpointy z v24).
  - Skrytí citlivých polí (`ALWAYS_PRIVATE_FIELDS`: e-maily, telefony, adresa, datum narození).

### Zabezpečení a citlivá data (v29 Summary)
- `PUT /profile/me/sensitive` vyžaduje `current_password`. Mění: `email_secondary`, `phone_secondary`, `birth_date`, `address`.
- Konstanta `ALWAYS_PRIVATE_FIELDS` na backendu striktně blokuje veřejné čtení těchto 4 polí.

---

## 2. Přehled otevřeného backlogu (Aktivní)
- **Chat místnosti & Messenger (Frontend UI):** Backend v3 (Messenger) a v4–v6 (Rooms) je hotový, chybí HTML/JS stránky.
- **Sdílený prohlížeč médií (`media-shared.js`):** Základní UI a akce hotové (#042). Chybí backend pro komentáře/lajky u médií, alba a tagování uživatelů.
- **Vlastní layouty uživatele (v20–v22 backlog):** Presety, export/import JSON (zatím nezahájeno).
- **Produkční tvrzení:** Zabezpečení JWT klíče do env, automatizované testy.

---

*Starší historie verzí (v1–v26) a log záznamy (#001–#049) byly přesunuty do `DEVLOG_archive_v25-v31.md`.*