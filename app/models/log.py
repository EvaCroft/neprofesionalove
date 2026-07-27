"""
Logovací systém - viz DEVLOG.md sekce 2 a 8 (rozhodnutí).

Architektonické rozhodnutí (v1): 11 log "typů" ze specifikace je
implementováno jako JEDNA tabulka `logs` s indexovaným sloupcem `log_type`,
místo 11 fyzicky oddělených tabulek. Funkčně ekvivalentní (lze filtrovat
podle typu), ale jednodušší na údržbu a rozšiřování. Pokud se v dalších
verzích ukáže potřeba fyzické separace (např. kvůli objemu dat u
system_log_FULL), lze tabulku později partitionovat/rozdělit beze změny
API vrstvy (logging_service.py).
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text

from app.db import Base


class LogType(str, enum.Enum):
    SYSTEM_LOG_FULL = "system_log_FULL"
    SYSTEM_LOG_FULL_BACKUP1 = "system_log_FULL_BACKUP1"
    OPERATION_SYSTEM_LOG = "operation_system_log"
    OPERATION_SYSTEM_LOG_ERROR = "operation_system_log_ERROR"
    OPERATION_USER_LOG = "operation_user_log"
    OPERATION_USER_LOG_ERROR = "operation_user_log_ERROR"
    SYSTEM_NETWORK_LOG = "system_network_LOG"
    SYSTEM_NETWORK_LOG_ERROR = "system_network_log_ERROR"
    SYSTEM_MESSENGER_LOG = "system_messenger_log"
    SYSTEM_MESSENGER_LOG_ERROR = "system_messenger_log_ERROR"
    SYSTEM_MODULE_MESSENGER_INCOME_LOG_FULL = "system_module_messenger_income_log_FULL"
    SYSTEM_MODULE_MESSENGER_SENT_LOG_FULL = "system_module_messenger_sent_log_FULL"
    SYSTEM_MEDIA_LOG = "system_media_log"
    SYSTEM_MEDIA_LOG_ERROR = "system_media_log_ERROR"


class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(Enum(LogType), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    actor_user_id = Column(Integer, nullable=True)  # kdo
    action = Column(String, nullable=False)  # co
    target = Column(String, nullable=True)  # koho/co to ovlivnilo
    ip_address = Column(String, nullable=True)  # kde (pro network logy)
    meta = Column(Text, nullable=True)  # volitelný JSON string s detaily
