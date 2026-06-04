from fastapi import APIRouter

from backend.app.api.v1 import admin, chat, conversations, search, system, user_settings

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(search.router)
api_router.include_router(user_settings.router)
api_router.include_router(admin.router)
