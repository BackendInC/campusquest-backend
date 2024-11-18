import db
import api


# Initialize the database
db.Base.metadata.create_all(bind=db.engine)

# Start the server
api.start_app()
