from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, init_db
from app.api import (
    health, targets, identities, sessions, transactions,
    imports, dependencies, workflows, shadow, openapi, interceptor
)

# Initialize Database tables (schema creation only, demo data only if AUTHTWIN_DEMO_MODE=true)
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AuthTwin: Workflow-Aware Authorization Testing Framework Foundation (Milestone 1)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(targets.router, prefix=settings.API_V1_STR)
app.include_router(identities.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(imports.router, prefix=settings.API_V1_STR)
app.include_router(dependencies.router, prefix=settings.API_V1_STR)
app.include_router(workflows.router, prefix=settings.API_V1_STR)
app.include_router(shadow.router, prefix=settings.API_V1_STR)
app.include_router(openapi.router, prefix=settings.API_V1_STR)
app.include_router(interceptor.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "AuthTwin Backend System Operational",
        "docs": "/docs",
        "version": "1.0.0",
        "milestone": "M1 - Workflow Reconstruction & Shadow Workflow Foundation"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.AUTHTWIN_API_HOST,
        port=settings.AUTHTWIN_API_PORT,
        reload=True,
    )
