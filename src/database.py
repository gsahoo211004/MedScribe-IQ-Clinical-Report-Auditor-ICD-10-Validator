from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ClinicalReport(Base):
    __tablename__ = "clinical_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_text = Column(Text, nullable=False)
    source = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, nullable=False)
    entity_text = Column(String(200))
    entity_label = Column(String(100))
    is_negated = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, nullable=False)
    entity_text = Column(String(200))
    suggested_icd10 = Column(String(20))
    icd10_description = Column(Text)
    confidence = Column(Float)
    status = Column(String(50))
    llm_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()