import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request
from sqlalchemy import create_engine, Column, Integer, DateTime, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import URL

load_dotenv()  
db_url = URL.create(
    drivername="postgresql+psycopg",  
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()



class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=False) 


# --- Flask-приложение ---
app = Flask(__name__)


@app.before_request
def _ensure_tables():
    Base.metadata.create_all(bind=engine)


def get_client_ip() -> str:
    # Учитываем возможный прокси (в Codespaces запросы идут через проброс)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/hello", methods=["GET"])
def hello():
    now = datetime.utcnow()
    ip = get_client_ip()

    session = SessionLocal()
    try:
        session.add(Visit(visit_time=now, ip_address=ip))
        session.commit()
    finally:
        session.close()

    return "Hello", 200



if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    app.run(host="0.0.0.0", port=5000)