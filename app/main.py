from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.auth.eds.router import router as eds_router
from app.api.auth import registration
from app.api.auth.email import router as email_router
from app.api.auth.me import router as me_router
from app.api.users import router as users_router
from app.api.departments import router as departments_router
from app.api.requests import router as requests_router
from app.api.statistics import router as statistics_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(eds_router, prefix=f"{settings.API_STR}/auth/eds", tags=["auth"])
app.include_router(registration.router, prefix=f"{settings.API_STR}/auth", tags=["auth"])
app.include_router(email_router, prefix=f"{settings.API_STR}/auth/email", tags=["auth"])
app.include_router(me_router, prefix=f"{settings.API_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_STR}/users", tags=["users"])
app.include_router(departments_router, prefix=f"{settings.API_STR}/departments", tags=["departments"])
app.include_router(requests_router, prefix=f"{settings.API_STR}/requests", tags=["requests"])
app.include_router(statistics_router, prefix=f"{settings.API_STR}/statistics", tags=["statistics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Akimat Requests API"} 