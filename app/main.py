from fastapi import FastAPI
from app.routers import tour, sync

app = FastAPI(title="HFO AI Service", description="Microservice tách biệt xử lý RAG AI")

# Gắn các router vào ứng dụng chính
app.include_router(tour.router)
app.include_router(sync.router)