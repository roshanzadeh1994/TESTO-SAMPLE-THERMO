from sqlalchemy import create_engine  # Import der Funktion zur Erstellung einer Datenbank-Engine
from sqlalchemy.ext.declarative import declarative_base  # Import der Funktion zur Deklaration von Basisklassen für Modelle
from sqlalchemy.orm import sessionmaker  # Import des SessionMakers, um eine Verbindung zur Datenbank zu erstellen

# Erstellung einer Datenbank-Engine, die eine SQLite-Datenbank verwendet
# "sqlite:///MasterArbeit_1.db" gibt den Pfad zur Datenbankdatei an
# "connect_args={"check_same_thread": False}" wird verwendet, um die Verbindung in einem Multi-Threading-Kontext zu erlauben
engine = create_engine("sqlite:///testoSample.db", connect_args={"check_same_thread": False})

# Deklarative Basisklasse, von der alle ORM-Modelle erben
Base = declarative_base()

# Erstellung einer sessionmaker-Funktion, die an die Datenbank-Engine gebunden ist
# Diese Funktion wird verwendet, um neue Datenbank-Sitzungen zu erstellen
sessionLocal = sessionmaker(bind=engine)

# Abhängigkeit, die eine Datenbank-Sitzung bereitstellt
def get_db():
    """
    Diese Funktion stellt eine Datenbank-Sitzung bereit, die in FastAPI als Abhängigkeit verwendet werden kann.

    Ablauf:
    1. Eine neue Sitzung wird erstellt.
    2. Die Sitzung wird an die aufrufende Funktion weitergegeben (mit `yield`).
    3. Nach Abschluss wird die Sitzung ordnungsgemäß geschlossen, um Speicherlecks zu verhindern.

    Rückgabewert:
    - Eine Datenbank-Sitzung, die zur Abfrage und Manipulation der Datenbank verwendet wird.
    """
    session = sessionLocal()  # Erstellt eine neue Datenbank-Sitzung
    try:
        yield session  # Gibt die Sitzung zurück, um sie in der API zu verwenden
    finally:
        session.close()  # Schließt die Sitzung nach Verwendung, um Ressourcen freizugeben
