# migrate_verification.py
# Run: python migrate_verification.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_extensions import db  #your existing db from extensions.py
from app import app

app = create_app()
with app.app_context():
    db.engine.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_links (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            type        TEXT NOT NULL,
            url         TEXT NOT NULL,
            title       TEXT,
            description TEXT,
            created_at  DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS skill_verifications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            skill_id     INTEGER NOT NULL,
            status       TEXT DEFAULT 'pending',
            verified_at  DATETIME,
            evidence_url TEXT,
            notes        TEXT,
            created_at   DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
            UNIQUE(user_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS peer_reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reviewer_id INTEGER NOT NULL,
            reviewee_id INTEGER NOT NULL,
            skill_id    INTEGER NOT NULL,
            swap_id     INTEGER,
            rating      INTEGER NOT NULL,
            comment     TEXT,
            is_flagged  INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewee_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(reviewer_id, reviewee_id, skill_id, swap_id)
        );

        CREATE TABLE IF NOT EXISTS badges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slug        TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            description TEXT,
            icon        TEXT,
            tier        TEXT DEFAULT 'bronze',
            created_at  DATETIME DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_badges (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            badge_id   INTEGER NOT NULL,
            awarded_at DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
            UNIQUE(user_id, badge_id)
        );

        INSERT OR IGNORE INTO badges (slug, name, description, icon, tier) VALUES
            ('verified_skill',   'Verified Skill',   '3+ peer reviews & portfolio', '✅', 'silver'),
            ('swap_starter',     'Swap Starter',     'Completed first swap',        '🔰', 'bronze'),
            ('swap_veteran',     'Swap Veteran',     '10+ swaps completed',         '⚡', 'gold'),
            ('top_teacher',      'Top Teacher',      '5+ swaps, 4.5+ rating',       '🏆', 'gold'),
            ('trusted_reviewer', 'Trusted Reviewer', 'Gave 10+ peer reviews',       '🌟', 'silver');
    """)
    print("✅ Done.")