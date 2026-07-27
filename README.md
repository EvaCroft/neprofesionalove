# Neprofesionálové

## Spuštění

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Server poběží na `http://127.0.0.1:8000`.

## Otevření frontendu

Otevři v prohlížeči:

```
http://127.0.0.1:8000/
```

Kořenová URL tě automaticky přesměruje na `/app/` → `frontend/appearance.html`
(design template systém — přepínání layoutů + slidery pro vzhled).

## Přímé odkazy

- Frontend (nastavení vzhledu): `http://127.0.0.1:8000/app/`
- API dokumentace (automaticky generovaná): `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Poznámky

- Databáze je SQLite, soubor se vytvoří automaticky při prvním spuštění (`init_db()` na startup).
- Detailní stav vývoje, log a build plán: viz `DEVLOG.md` a `BUILDPLAN.md`.
