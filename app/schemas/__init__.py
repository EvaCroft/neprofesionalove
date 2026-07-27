"""Pydantic schémata rozdělená podle domény.

Balíček re-exportuje všechny třídy/konstanty ze všech modulů, takže
stávající `from app.schemas import X` v routerech nadále funguje
beze změny - `app.schemas` se navenek chová stejně jako dřívější
jednosouborový `app/schemas.py`.
"""

from .common import *  # noqa: F401,F403
from .auth import *  # noqa: F401,F403
from .profile import *  # noqa: F401,F403
from .messenger import *  # noqa: F401,F403
from .rooms import *  # noqa: F401,F403
from .moderation import *  # noqa: F401,F403
from .settings import *  # noqa: F401,F403
from .wallet import *  # noqa: F401,F403
from .referral import *  # noqa: F401,F403
from .games import *  # noqa: F401,F403
from .auctions import *  # noqa: F401,F403
from .media import *  # noqa: F401,F403
from .events import *  # noqa: F401,F403
from .posts import *  # noqa: F401,F403
from .friendship import *  # noqa: F401,F403
from .badge import *  # noqa: F401,F403
from .presence import *  # noqa: F401,F403
