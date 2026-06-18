from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE asset_technologies ADD COLUMN category VARCHAR(100);"))
        conn.commit()
        print("Column added successfully!")
    except Exception as e:
        print(f"Error: {e}")
