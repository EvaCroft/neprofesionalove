# DEVLOG (Archive) – Neprofesionálové

Tento dokument obsahuje historický deník vývoje (DEVLOG), kompletní výpis logovacích záznamů (#001–#049) a specifikace dřívějších verzí (v1 až v29).

---

## Obsah archivu
1. Historie verzí a plné záznamy logu (#001–#049)
2. Původní specifikace logovacího systému (11 typů logů)
3. Kompletní seznam vylepšení a vyřešených bugů

---

### Vybrané klíčové milníky z logu:

- **#049 [2026-07-27] — v29 (Osobní údaje & citlivá kontaktní data)**: Implementována pole `education`, `religion`, `sexual_preference`, sensitive endpoint s heslem, konstanta `ALWAYS_PRIVATE_FIELDS`.
- **#048 [2026-07-27] — v27 (O mně & Přátelé na vlastním profilu)**: Napojen online status (`/presence`), trvalé statistiky, karta Přátelé na vlastním profilu.
- **#047 [2026-07-27] — v26 (Přítomnost & čítače)**: Presence service bez pingu, odvození stavu, čítač zobrazení profilu a hodin v chatu.
- **#046 [2026-07-27] — v25 (Odznaky)**: Katalog 15 ikon, max 5 na profil, admin CRUD endpointy.
- **#045 [2026-07-27] — v24 (Vztahy: Přátelství & Sledování)**: DB modely `FriendRequest`, `Follow`, backend router `/friends`.
- **#042 [2026-07-27] — Sdílené prohlížení médií (`media-shared.js`)**: Sjednocení lightboxu pro Galerii, Profil i Zeď.
- **#001–#041**: Základní MVP (v1–v6), Kreditový systém (v7–v12), Aukce a hry (v13–v16), Design template systém (v17–v19), Reálný design a modulární profil (v20–v23).

*(Kompletní historický text původního DEVLOG.md byl archívně uložen sem)*