from typing import List
from app.database import SessionLocal
from app.models.asset import Asset
from datetime import datetime, timedelta

class DiffEngine:
    """
    Compares newly discovered assets with previous scans to identify differences.
    """
    def __init__(self, target_id: int):
        self.target_id = target_id
        self.db = SessionLocal()

    def get_new_assets(self, time_window_hours=24) -> List[Asset]:
        """
        Returns assets discovered within the last `time_window_hours`.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
            new_assets = self.db.query(Asset).filter(
                Asset.target_id == self.target_id,
                Asset.created_at >= cutoff
            ).all()
            return new_assets
        finally:
            self.db.close()
            
    def generate_delta_alert(self):
        """
        Generates an alert if new assets or ports were discovered recently.
        """
        new_assets = self.get_new_assets()
        if not new_assets:
            return None
            
        return {
            "type": "DeltaAlert",
            "message": f"Found {len(new_assets)} new assets in the last 24 hours.",
            "assets": [a.value for a in new_assets]
        }
