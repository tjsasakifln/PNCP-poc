# BidIQ Uniformes POC - Backend API
# FastAPI application entrypoint
#
# This file will be implemented in issue #17 (Estrutura base FastAPI)

from fastapi import FastAPI

app = FastAPI(
    title="BidIQ Uniformes API",
    description="API para busca e análise de licitações de uniformes no PNCP",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Placeholder endpoint - will be removed in issue #17"""
    return {
        "status": "placeholder",
        "message": "Backend structure initialized. Awaiting FastAPI implementation."
    }
