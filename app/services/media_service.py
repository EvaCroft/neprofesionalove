"""
Media service - ukládání nahraných souborů na disk + odvození typu média.

Soubory se ukládají do `MEDIA_ROOT` (výchozí `./media_uploads`, mimo `frontend/`
i `app/`, aby se nepletly do statického mountu design-šablon) pod názvem
`{uuid4}.{přípona}`. Do DB se ukládá jen relativní cesta - `main.py` mountuje
`MEDIA_ROOT` jako statické `/media-files/...`, takže `MediaAssetOut.url` je
vždy `/media-files/{stored_name}`.
"""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

from app.models.media import MediaType

MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / "media_uploads"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# mime prefix/hodnota -> MediaType. Řadu specifických kontejnerů (mp4 apod.)
# necháváme spadnout pod obecný "video/" a "audio/" prefix - REEL se odlišuje
# explicitním parametrem v requestu (viz router), ne podle mime typu.
_MIME_TYPE_MAP = {
    "video/": MediaType.VIDEO,
    "audio/": MediaType.AUDIO,
    "image/": MediaType.PHOTO,
}

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB - MVP limit, viz DEVLOG


def infer_media_type(mime_type: str, requested_type: Optional[str] = None) -> MediaType:
    """`requested_type` (z formuláře) má přednost - hlavně kvůli REEL, který
    sdílí mime typy s VIDEO, ale patří do jiné kategorie v galerii."""
    if requested_type:
        try:
            return MediaType(requested_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Neznámý media_type: {requested_type}")

    for prefix, media_type in _MIME_TYPE_MAP.items():
        if mime_type.startswith(prefix):
            return media_type

    raise HTTPException(status_code=400, detail=f"Nepodporovaný typ souboru: {mime_type}")


def save_upload(file: UploadFile) -> tuple[str, int]:
    """Uloží nahraný soubor na disk. Vrací (relativní_cesta, velikost_v_bytech)."""
    suffix = Path(file.filename).suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = MEDIA_ROOT / stored_name

    size = 0
    with open(dest, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Soubor je příliš velký (limit 200 MB)")
            out.write(chunk)

    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Nahraný soubor je prázdný")

    return stored_name, size


def to_url(stored_name: str) -> str:
    return f"/media-files/{stored_name}"
