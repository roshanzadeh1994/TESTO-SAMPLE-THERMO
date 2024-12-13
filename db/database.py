from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Datenbank-Engine erstellen
engine = create_engine("sqlite:///testoSample.db", connect_args={"check_same_thread": False})

# Basisklasse für Modelle
Base = declarative_base()

# Session-Maker erstellen
sessionLocal = sessionmaker(bind=engine)

# Datenbank-Sitzung bereitstellen
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
