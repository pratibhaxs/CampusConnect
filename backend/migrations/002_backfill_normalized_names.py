"""Fills companies.normalized_name for existing rows. Run from the backend/ folder:
    python migrations/002_backfill_normalized_names.py
Reports companies that normalize to the same name — merge those in Admin > Suggestions
(or rename one) before adding the UNIQUE index from 002_company_suggestions.sql."""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.matching import normalize_name  # noqa: E402
from app.models.company import Company  # noqa: E402

db = SessionLocal()
groups = defaultdict(list)
for c in db.query(Company).all():
    c.normalized_name = normalize_name(c.name)
    groups[c.normalized_name].append(c.name)
db.commit()

dupes = {k: v for k, v in groups.items() if len(v) > 1}
print(f"Backfilled {sum(len(v) for v in groups.values())} companies.")
if dupes:
    print("These names collide after normalization — resolve before adding the UNIQUE index:")
    for k, v in dupes.items():
        print(f"  {k!r}: {v}")
