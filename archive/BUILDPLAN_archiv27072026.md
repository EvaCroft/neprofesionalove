# BUILDPLAN (Archive) – Neprofesionálové

Tento soubor obsahuje kompletní historii a specifikaci již dokončených verzí z plánu vývoje.

---

## 1. Blok: MVP (v1–v6) ✅ KOMPLETNÍ
- **v1 — Kostra projektu + auth + logging:** FastAPI skeleton, SQLite, model `User`, JWT auth, 11 logovacích tabulek.
- **v2 — Role & oprávnění + User-profile:** Oprávnění (Guest/User/Creator/Moderator/Admin), model `Profile` a REST CRUD.
- **v3 — Messenger:** Model `DirectMessage`, posílání přímých zpráv, historie, logování.
- **v4 — Chat místnosti (základ):** Model `Room`, `RoomMessage`, veřejné a soukromé místnosti, join/leave.
- **v5 — Založení místnosti + Creator práva:** Zakládání místností (Creator+), práva vlastníků (kick/mute).
- **v6 — Moderator/Admin nástroje + audit logování:** Moderování, bannery, admin nástroje, finální audit 11 logovacích typů.

---

## 2. Blok: Kreditový systém / zlaťáky (v7–v12) ✅ KOMPLETNÍ
- **v7 — Credit ledger core:** Modely `Wallet`, `Transaction`, `credit_service` (deposit/withdraw/transfer).
- **v8 — Dobíjení kreditu (top-up):** Admin topup placeholder.
- **v9 — Výplata kreditu:** Request flow výplat (WithdrawalRequest).
- **v10 — Placené místnosti + odměny:** Vstupné do místností, odměny pro creatory.
- **v11 — Invite/referral systém:** Pozvánky a odměny za doporučené uživatele.
- **v12 — Regulatorní pojistky + credit audit:** Auditní nástroje a bezpečné limity.

---

## 3. Blok: Aukce a hry (v13–v16) ✅ KOMPLETNÍ
- **v13 — Herní infrastruktura:** Piškvorky 1v1.
- **v14 — Spectator mode:** Živé sledování her.
- **v15 — Živé aukce:** Dražby v místnostech.
- **v16 — 2v2 týmové hry:** Týmové zápasy a volitelný vklad/pot.

---

## 4. Archív design systému (v17–v19) 📦 ARCHIVOVÁNO
- **v17–v19:** Původní dynamické HSL theming šablony byly nahrazeny stálým Apple/glass designem a přesunuty do `frontend/_archive_v17-v19/`.