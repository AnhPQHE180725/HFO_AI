import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector

# Load biến môi trường
load_dotenv(override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PG_DIRECT_CONN = os.getenv("PG_DIRECT_CONN")
PG_VECTOR_CONN = os.getenv("PG_VECTOR_CONN")
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION")

# Khởi tạo AI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.1)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Kết nối Vector DB
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=PG_VECTOR_CONN,
    use_jsonb=True,
)