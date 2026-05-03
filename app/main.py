from fastapi import FastAPI
from app.routers import tour, sync
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HFO AI Service", description="Tách biệt xử lý RAG AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
app.include_router(tour.router)
app.include_router(sync.router)