from db.models import DeviceInspection
from sqlalchemy.orm.session import Session


# Funktion zum Hinzufügen einer Schiffsinspektion in die Datenbank
def create_device_inspection(db: Session, inspection_data):
    inspection = DeviceInspection(**inspection_data)
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


# Funktion zum Abrufen aller Schiffsinspektionen aus der Datenbank
def get_all_device_inspections(db):
    return db.query(DeviceInspection).all()


# Funktion zum Abrufen einer einzelnen Schiffsinspektion anhand der ID
def get_device_inspection_by_id(db, inspection_id):
    return db.query(DeviceInspection).filter(DeviceInspection.id == inspection_id).first()

