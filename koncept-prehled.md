# Koncept: Agregovaná mediální/komunitní platforma + sociální síť

## 1. Agregace obsahu (feed)
- Feed z různých platforem/sítí — import uživatelů, galerií, videí atd.
- Agregovaný feed ze **všech messengerů**: iMessage/iCloud, Google, WhatsApp, FB/Messenger, Instagram, Signal, Telegram, další platformy
- Vlastní wall/feed agregující uživatelovy zdroje a propojené appky/soc. sítě

## 2. Tvorba a správa obsahu
- Formáty: audio, video, foto, text, 3D, odkazy, soubory, galerie, animace, AI generovaný obsah
- Funkce: uložení, zálohování, archivace, sdílení, hodnocení, komentování, organizace, propagace
- **Monetizace** uměleckého/autorsky exkluzivního a event/raw obsahu
- Import z PC, jiných soc. sítí, cloudových služeb
- Plánování obsahu + automatická publikace na napojené sítě/platformy
- Global user base

## 3. Komunitní vrstva
- Fórum, user-wall
- Ankety, soutěže
- Povídky, srázy (meetupy), komentáře, kluby, blogy
- Seznamka / inzeráty
- Trendy, statistiky, TOP žebříčky
- Marketplace
- HelpDesk

## 4. Chat / messenger systém
- Veřejné stálé místnosti (dle kategorie, lokality, trendu)
- Hlavní chat-wall v místnosti: text, emoji, obrázek/gif — max 2 řádky
- Soukromé zprávy, šeptání mezi uživateli
- Hodnocení a ankety v místnosti
- Zakládání nových místností
- Streamování videa v místnosti

### 4a. R&D nápad (výzkum)
- Vizualizace chat místnosti jako "domu" — velikost dle počtu lidí
- Avataři přicházejí, gestikulují, animace, spolupráce více avatarů
- Vizualizace sledovanosti streamu (počet diváků)

## 5. Tokenová ekonomika
- Jednotka: **zlaťáky**
- Převody mezi členy, platby za sdílení, odměny

## 6. Platformy
- Web, iOS, Android

## 7. BackOffice / administrace
Administrace celého systému napříč agendami a odděleními, prostředí:
- DEV 1, DEV 2, DEV-BACKUP
- PRODUCTION-RUNNING, PRODUCTION-BACKUP
- EMERGENCY_PRODUCTION_PROTOKOL
- LANGUAGE_MUTATION
- COUNTRY_ACCESS_RESTRICTED
- Cíl: stabilní, robustní, škálovatelný, "soon peopleless" provoz

## 8. Architektonické principy
- Škálovatelnost, verzovatelnost, nasaditelnost, spravovatelnost
- Snadná integrace do jiných struktur / integrace dalších celků do appky
- Otypování, parametrizace, kategorizace, definice vztahů, seskupování
- **Paralelní vývoj**: víc větví/sekcí/modulů současně
- **Lokální kontext**: pro malou změnu nenačítat půl systému / celý devlog
- Build plan a groupování práce dle konkrétních souborů/tříd/funkcí a kontextu

## 9. Vývojový proces (skilly)
- `spec-first-development` — spec → potvrzení → build plan → potvrzení → implementace
- `dev-logger-alice` — DEVLOG.md (stav, spec, build plan, log, zamítnuté nápady, backlog, bugfix iterace, rozhodnutí, blokátory)
- `token-saver-jane` — token-efektivní chování napříč konverzací
- `done-before-zzzokenight-donald` — odhad náročnosti před startem, rozdělení velkých úkolů
- BUILDPLAN.md vždy min. 3–6 verzí dopředu, verze seskupené podle souborů/tříd/funkcí; při vysoké náročnosti verzi dál dělit

---

## Otevřené otázky k doplnění (než uděláme spec)
1. **Priorita MVP** — co jede v první verzi: agregace feedů, chat, marketplace, monetizace? Vše najednou = obří scope.
2. **Messenger agregace** — přes oficiální API (limitované, mnohé zakazují cross-posting jako Meta/WhatsApp) nebo scraping (riziko banů/legality)?
3. **Trendy prvky, co chybí**: live shopping, short-form video (reels-style), AI co-creation nástroje, creator analytics dashboard, tipping/superchat při streamu, NFT/ownership certifikace obsahu, moderace obsahu + AI trust&safety, verifikace uživatelů/tvůrců, mobile push/notifikační engine, SEO/discovery algoritmus, GDPR/data export nástroj.
4. **Regulatorní riziko** — tokenová ekonomika (zlaťáky) může spadat pod finanční regulace, pokud jsou směnitelné za reálné peníze.

Chceš, ať z tohohle sestavíme první spec (MVP scope) podle `spec-first-development`?
