from api import app
import db


# Initialize the database
db.Base.metadata.create_all(bind=db.engine)
