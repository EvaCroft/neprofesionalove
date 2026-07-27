# Neprofesionálové

Agregovaná mediální/komunitní platforma + sociální síť. MVP fáze — základ (uživatelé, profily, messenger, chat místnosti, logování), na kterém se dál staví zbytek konceptu (agregace feedů/messengerů z externích platforem, monetizace/zlaťáky, aukce, hry, marketplace, streamování, simulátor vývoje...).

Plná koncepční specifikace: viz `koncept-prehled.md` (dodáno uživatelem, mimo repo projektu).

## Stack
- Backend: Python FastAPI + SQLite
- Frontend: jednosouborové HTML/JS (styl OmniCore)

## Role a oprávnění (MVP)
| Role | Oprávnění |
|---|---|
| Guest | prohlížení veřejných místností bez interakce, registrace/login |
| User | psaní do chatu, messenger, vlastní profil, join do místností |
| Creator | + zakládání místností, správa vlastní místnosti (kick/mute ve své místnosti) |
| Moderator | dohled nad přidělenými místnostmi, mazání zpráv, mute/ban, user-report fronta |
| Admin | plný přístup — správa uživatelů/rolí, čtení všech logů, globální nastavení |

## Rozsah MVP
1. Uživatelé + role
2. User-profile (základní info)
3. Messenger (přímé zprávy)
4. Chat místnosti (veřejné/privátní)
5. Založení místnosti
6. Logovací systém (11 typů logů — viz DEVLOG.md sekce 2)

## Post-MVP: Systém příspěvků (v20)
Model `Post` (vlastní i systémem generované příspěvky) + `WallSettings` (co se propisuje na zeď) — `app/models/post.py`, `app/models/wall_settings.py`, `app/services/post_service.py`, `app/routers/posts.py`. Napojeno na `MediaSource.WALL` upload. Viditelnost "friends" zatím = "private" (chybí systém přátel).

## Mimo scope MVP
Agregace externích feedů/messengerů, monetizace, tokeny/zlaťáky, aukce, hry, marketplace, streamování, simulátor vývoje s coding mapami.

Detailní stav a build plán: viz `DEVLOG.md` a `BUILDPLAN.md`.
