import api
from api import app
import db
from db.models import reaction_type_enum

# Explicitly create the enum type
reaction_type_enum.create(bind=db.engine, checkfirst=True)

# Initialize the database
db.Base.metadata.create_all(bind=db.engine)

