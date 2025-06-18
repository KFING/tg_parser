import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_api.dependencies import get_db_main
from src.app_api.middlewares import get_log_extra
from src.service_keycloak.action_user import (
    KeycloakLoginUserApiMdl,
    KeycloakMessage,
    KeycloakRegisterUser,
    keycloak_action_delete_user,
    keycloak_action_get_user_info,
    keycloak_action_group_user_add,
    keycloak_action_group_user_remove,
    keycloak_action_login,
    keycloak_action_logout,
    keycloak_action_refresh_token,
    keycloak_action_role_user_assign,
    keycloak_action_role_user_delete,
    keycloak_action_user_create,
    keycloak_action_user_set_password,
)
from src.service_keycloak.models.auth_token import AuthTokenApiMdl

logger = logging.getLogger(__name__)


auth_router = APIRouter(
    tags=["auth"],
)


@auth_router.post("/auth")
async def login(user: KeycloakLoginUserApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> AuthTokenApiMdl:
    return await keycloak_action_login(user, log_extra=log_extra)


@auth_router.patch("/auth")
async def refresh_token(refresh_token: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> AuthTokenApiMdl:
    return await keycloak_action_refresh_token(refresh_token, log_extra=log_extra)


@auth_router.delete("/auth")
async def logout(token: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return await keycloak_action_logout(token, log_extra=log_extra)


@auth_router.put("/users/user/{user_id}/groups/group/{group_id}")  # g: 2c3c8ee7-0490-45e8-a9d5-2d36c6ebb0dc
async def group_user_add(user_id: uuid.UUID, group_id: uuid.UUID, log_extra: dict[str, str] = Depends(get_log_extra)) -> None | KeycloakMessage:
    return await keycloak_action_group_user_add(user_id, group_id, log_extra=log_extra)


@auth_router.delete("/users/user/{user_id}/groups/group/{group_id}")
async def group_user_remove(user_id: uuid.UUID, group_id: uuid.UUID, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return await keycloak_action_group_user_remove(user_id, group_id, log_extra=log_extra)


@auth_router.put("/users/user/{user_id}/roles/")
async def role_user_assign(user_id: uuid.UUID, role: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None | KeycloakMessage:
    return await keycloak_action_role_user_assign(user_id, role, log_extra=log_extra)


@auth_router.delete("/users/user/{user_id}/roles/")
async def role_user_delete(user_id: uuid.UUID, role: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return await keycloak_action_role_user_delete(user_id, role, log_extra=log_extra)


@auth_router.post("/users/user")
async def register_user_without_password(
    user: KeycloakRegisterUser, db: AsyncSession = Depends(get_db_main), log_extra: dict[str, str] = Depends(get_log_extra)
) -> uuid.UUID:
    return await keycloak_action_user_create(db, user, log_extra=log_extra)


@auth_router.get("/users/user/{user_id}")
async def get_user_info(user_id: uuid.UUID, log_extra: dict[str, str] = Depends(get_log_extra)) -> list[str] | None:
    return await keycloak_action_get_user_info(user_id, log_extra=log_extra)


@auth_router.put("/users/user/{user_id}")
async def set_user_password(user_id: uuid.UUID, password: str, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return await keycloak_action_user_set_password(user_id, password, log_extra=log_extra)


@auth_router.delete("/users/user/{user_id}")
async def delete_user(user_id: uuid.UUID, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    return await keycloak_action_delete_user(user_id, log_extra=log_extra)
