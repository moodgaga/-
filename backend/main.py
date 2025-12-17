from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.routers import items, auth, users, portfolio

#db tablichki
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Digital Production Agency API",
    description="API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для правильной кодировки UTF-8
@app.middleware("http")
async def add_charset_header(request, call_next):
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

# routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(items.router, prefix="/api/v1", tags=["items"])


@app.get("/", response_class=JSONResponse)
async def root():
    return JSONResponse(
        content={
            "message": "Добро пожаловать в API агентства цифрового производства",
            "version": "1.0.0"
        },
        media_type="application/json; charset=utf-8"
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


