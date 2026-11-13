from src.database.connection import engine
from src.database.models import Base

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
print("Tables:", list(Base.metadata.tables.keys()))
