
#  Voice User Interface (VUI) – Sprachgesteuerte Formularbearbeitung
#  Studierendenprojekt für Testo GmbH
#  Projektübersicht
Dieses Projekt demonstriert ein Voice User Interface (VUI), das Sprachaufnahmen nutzt, um Formulare automatisch auszufüllen.
Basierend auf FastAPI, OpenAI GPT-4 Turbo, Whisper, Tesseract OCR und SQLite.

  Entwickelt von: Amirhossein Roshanzadeh
  Studiengang: Informatik, Softwareentwicklung (Master)
  Praxispartner: Testo GmbH

# 📚 Inhaltsverzeichnis
Projektübersicht

Architektur

Technologien

API-Schnittstellen

Benutzeroberfläche

Sicherheit

Installation und Setup

Tests

Fazit und Ausblick

Quellen

# 🏗 Architektur
Hauptkomponenten
Backend (FastAPI) – API-Entwicklung und Logik

Frontend (HTML, JavaScript, Jinja2) – Benutzeroberfläche

Datenbank (SQLite) – Persistente Datenspeicherung

Externe KI-Services (OpenAI GPT-4 & Whisper) – Verarbeitung von Sprache und Text

Workflow
mermaid
Kopieren
Bearbeiten
flowchart TD
    A[Nutzer] -->|Upload Formular / Audio| B[FastAPI Server]
    B --> C[Tesseract OCR / Whisper STT]
    C --> D[OpenAI GPT-4: Feldextraktion / Form Matching]
    D --> E[Datenbank (SQLite)]
    E --> F[Frontend Ergebnisanzeige]
# 🛠 Technologien

Technologie	Funktion
FastAPI	Web-Framework (Backend/API)
OpenAI GPT-4 Turbo	Extraktion & Ausfüllung
OpenAI Whisper	Sprach-zu-Text-Umwandlung
Tesseract OCR	Texterkennung aus Bildern/PDFs
SQLite	Datenpersistenz
OAuth2 + JWT	Authentifizierung & Sicherheit
HTML/JS/Jinja2	Frontend-Entwicklung
# 🔌 API-Schnittstellen (Auswahl)

Methode	Pfad	Beschreibung
POST	/process_form	Formular hochladen und Felder extrahieren
POST	/process_voice	Sprachaufnahme verarbeiten und Formular ausfüllen
POST	/signup/submit	Benutzerregistrierung
POST	/api/save_inspection	Inspektionsdaten speichern
GET	/profile/	Benutzerprofil anzeigen
# 👉 Komplette API-Dokumentation: hier klicken

# 🖥 Benutzeroberfläche (UI)

Seite	Beschreibung
Homepage	Navigation zu Login/Signup
Login	Nutzeranmeldung
Signup	Registrierung
Manuelles Formular	Manuelle Eingabe von Inspektionsdaten
AI-Formular	Automatisches Formularausfüllen mit Sprache
Ergebnisseite	Anzeige der verarbeiteten Daten
🛡 Sicherheit
OAuth2 mit JWT für sichere Authentifizierung

Cookies (HTTPOnly & Secure) zur Sitzungsverwaltung

HTTPS-Unterstützung für verschlüsselte Verbindungen

# ⚙️ Installation und Setup
Voraussetzungen
Python 3.8+

Pip

FastAPI, Uvicorn, SQLAlchemy, python-dotenv

OpenAI API-Key

Tesseract-OCR Installation

Installationsschritte
bash
Kopieren
Bearbeiten
# Repository klonen
git clone https://github.com/roshanzadeh1994/TESTO-SAMPLE-THERMO.git

# Abhängigkeiten installieren
pip install -r requirements.txt

# Server starten
uvicorn main:app --reload
📍 Webanwendung erreichbar unter: http://127.0.0.1:8000

🧪 Tests
Textbasierte Eingabe (Beispiel 1):

"Inspektionsort: Berlin, Inspektionsdatum: 15. Januar 2025, Schiff: Alexandra"

Sprachbasierte Eingabe (Beispiel 2):

Aufnahme hochladen: Whisper transkribiert, GPT-4 extrahiert, Felder werden automatisch befüllt.

✅ Erfolgreiches automatisches Ausfüllen und Abspeichern der Formulare.

# 🎯 Fazit und Ausblick
Ziel erreicht: Sprachgesteuertes Formularausfüllen mit KI erfolgreich umgesetzt.

Stärken: Hohe Präzision bei Text- und Sprachverarbeitung, flexible Architektur.

Nächste Schritte:

Dynamische Datenfelder-Generierung

Mehrsprachige Unterstützung (Deutsch/Englisch/weitere)

Erweiterung auf Offline-Verarbeitung (lokale AI-Modelle)

# 📚 Quellen
FastAPI Documentation

OpenAI GPT-4

Whisper Speech-to-Text

Tesseract OCR

SQLite Documentation

🛠️ Erstellt im Rahmen der Masterarbeit von Amirhossein Roshanzadeh an der Hochschule im Bereich Softwareentwicklung in Kooperation mit Testo GmbH.
