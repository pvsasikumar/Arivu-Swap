from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        columns = [
            "ALTER TABLE message ADD COLUMN msg_type VARCHAR(20) DEFAULT 'text'",
            "ALTER TABLE message ADD COLUMN file_url VARCHAR(300)",
            "ALTER TABLE message ADD COLUMN file_name VARCHAR(200)",
            "ALTER TABLE message ADD COLUMN file_size INTEGER",
            "ALTER TABLE message ADD COLUMN code_lang VARCHAR(30)",
            "ALTER TABLE message ADD COLUMN is_deleted BOOLEAN DEFAULT 0",
        ]
        for col in columns:
            try:
                conn.execute(text(col))
                print(f"OK: {col[:50]}")
            except Exception as e:
                print(f"SKIP: {e}")
        conn.commit()
        print("Migration complete!")

