from extensions import db
from models import User, NfcTag, DoorLog, DoorbellLog

# verify new table columns
for column in NfcTag.__table__.columns:
    print(column.name, column.type)

for column in User.__table__.columns:
    print(column.name, column.type)

for column in DoorLog.__table__.columns:
    print(column.name, column.type)

for column in DoorbellLog.__table__.columns:
    print(column.name, column.type)
