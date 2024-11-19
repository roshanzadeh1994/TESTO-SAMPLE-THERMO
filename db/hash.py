from passlib.context import \
    CryptContext  # Import der CryptContext-Klasse, die zur Verwaltung von Passwort-Hashing-Schemata verwendet wird

# Erstellen eines CryptContext für die Verwendung des bcrypt-Hashing-Algorithmus
# "deprecated='auto'" bedeutet, dass veraltete Hashing-Algorithmen automatisch markiert werden
pwd_cxt = CryptContext(schemes="bcrypt", deprecated="auto")


# Eine Hilfsklasse für Passwort-Hashing und Verifizierung
class Hash:
    """
    Diese Klasse enthält statische Methoden zur Verwaltung von Passwort-Hashes.

    Methoden:
    - bcrypt: Hasht ein Passwort mithilfe des bcrypt-Algorithmus.
    - verify: Überprüft, ob ein gegebenes Klartextpasswort mit einem gehashten Passwort übereinstimmt.
    """

    @staticmethod
    def bcrypt(password: str) -> str:
        """
        Hashes a given plain password using bcrypt.

        Parameter:
        - password (str): Das zu hashende Klartextpasswort.

        Rückgabewert:
        - Ein gehashter String, der das gehashte Passwort enthält.
        """
        return pwd_cxt.hash(password)  # Hasht das Passwort und gibt den gehashten Wert zurück

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        """
        Verifiziert ein Klartextpasswort gegen ein gehashtes Passwort.

        Parameter:
        - hashed_password (str): Das gespeicherte, gehashte Passwort.
        - plain_password (str): Das zu überprüfende Klartextpasswort.

        Rückgabewert:
        - True, wenn das Klartextpasswort dem gehashten Passwort entspricht, andernfalls False.
        """
        return pwd_cxt.verify(plain_password, hashed_password)  # Überprüft, ob das Klartextpasswort korrekt ist
