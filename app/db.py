"""
DB inicializace - SQLite + SQLAlchemy session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./neprofesionalove.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency - jedna DB session na request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Vytvoří všechny tabulky podle registrovaných modelů."""
    # Import modelů, aby se zaregistrovaly do Base.metadata před create_all
    from app.models import user, log, profile, profile_location, message, room, room_message, moderation, settings, wallet, withdrawal, referral, game, auction, media, event, post, wall_settings, activity_settings, friendship, follow, badge  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_existing_tables()
    _seed_default_badges()


def _migrate_existing_tables():
    """Lehká 'migrace' pro SQLite bez Alembic.

    `create_all()` vytvoří jen tabulky, které ještě vůbec neexistují - u
    tabulky `profiles`, která existovala už dřív (v2), nové sloupce přidané
    v pozdějších verzích (v20+) samy od sebe nevzniknou. Tahle funkce projde
    sloupce definované v modelu a chybějící doplní přes `ALTER TABLE ...
    ADD COLUMN`, aby stará DB (a v ní existující uživatelé) nemusela být
    smazaná při každém rozšíření profilu.
    """
    from sqlalchemy import inspect, text
    from app.models.profile import Profile

    inspector = inspect(engine)
    if "profiles" not in inspector.get_table_names():
        return  # create_all ji teprve založí příště, není co migrovat

    existing_cols = {c["name"] for c in inspector.get_columns("profiles")}

    # SQLite typová mapa pro ALTER TABLE ADD COLUMN (jen typy použité v Profile)
    sqlite_type_map = {
        "VARCHAR": "TEXT",
        "TEXT": "TEXT",
        "DATE": "DATE",
        "JSON": "TEXT",
        "INTEGER": "INTEGER",
    }

    with engine.begin() as conn:
        for column in Profile.__table__.columns:
            if column.name in existing_cols:
                continue
            col_type = sqlite_type_map.get(
                column.type.__class__.__name__.upper(), "TEXT"
            )
            conn.execute(
                text(f"ALTER TABLE profiles ADD COLUMN {column.name} {col_type}")
            )


def _seed_default_badges():
    """Naplní tabulku `badges` výchozí sadou 15 odznaků, jen pokud je zatím
    prázdná - nepřepisuje pozdější admin úpravy (přejmenování/deaktivace/
    přidání vlastních) při dalších restartech serveru."""
    from app.models.badge import Badge, DEFAULT_BADGES

    db = SessionLocal()
    try:
        if db.query(Badge).first() is not None:
            return
        for i, (key, emoji, name) in enumerate(DEFAULT_BADGES):
            db.add(Badge(key=key, emoji=emoji, name=name, is_active=True, sort_order=i))
        db.commit()
    finally:
        db.close()
