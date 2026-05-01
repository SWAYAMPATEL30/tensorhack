import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import Base, engine
from backend import models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
