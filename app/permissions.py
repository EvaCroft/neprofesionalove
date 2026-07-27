"""
Role-based access control (RBAC).

Hierarchie rolí (nejnižší → nejvyšší): guest < user < creator < moderator < admin.
Guest = neautentizovaný návštěvník (bez User záznamu, bez JWT) - endpointy
pro guesty jednoduše nemají Depends(get_current_user)/require_role.
"""
from typing import Iterable

from fastapi import Depends, HTTPException, status

from app.models.user import RoleEnum, User
from app.routers.auth import get_current_user

# Pořadí důležité - používá se pro "role X a vyšší"
ROLE_HIERARCHY = [
    RoleEnum.USER,
    RoleEnum.CREATOR,
    RoleEnum.MODERATOR,
    RoleEnum.ADMIN,
]


def require_role(minimum_role: RoleEnum):
    """Vrátí FastAPI dependency, která povolí přístup uživatelům s rolí
    `minimum_role` NEBO vyšší v hierarchii (require_role(CREATOR) pustí
    i MODERATOR a ADMIN)."""
    min_index = ROLE_HIERARCHY.index(minimum_role)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_index = ROLE_HIERARCHY.index(current_user.role)
        if user_index < min_index:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vyžadována role '{minimum_role.value}' nebo vyšší",
            )
        return current_user

    return dependency


def require_exact_roles(roles: Iterable[RoleEnum]):
    """Dependency povolující jen explicitně vyjmenované role (bez hierarchie)."""
    allowed = set(roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            allowed_str = ", ".join(r.value for r in allowed)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vyžadována jedna z rolí: {allowed_str}",
            )
        return current_user

    return dependency
