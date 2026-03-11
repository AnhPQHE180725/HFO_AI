from fastapi import FastAPI
from app.routers import tour, sync
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HFO AI Service", description="Microservice tách biệt xử lý RAG AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế nên để ["http://localhost:5173", "http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi method (GET, POST, OPTIONS, PUT, DELETE)
    allow_headers=["*"],  # Cho phép mọi header
)
app.include_router(tour.router)
app.include_router(sync.router)