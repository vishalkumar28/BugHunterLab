from app.database import SessionLocal
from app.models.rules import VulnerabilityRule
from app.models.asset import Asset, AssetTechnology

def generate_scan_plan(asset_id: int):
    """
    Evaluates detected technologies against rules to generate a scan plan.
    """
    db = SessionLocal()
    plan = []
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return []

        technologies = db.query(AssetTechnology).filter(AssetTechnology.asset_id == asset_id).all()
        for tech in technologies:
            rules = db.query(VulnerabilityRule).filter(VulnerabilityRule.tech_name == tech.tech_name).all()
            for rule in rules:
                # Basic template formatting for arguments
                # For instance: "-t cves/ -tags {tech_name} -u {target}"
                formatted_args = rule.tool_args.format(target=asset.value, tech_name=tech.tech_name).split()
                
                plan.append({
                    "tool": rule.tool,
                    "args": formatted_args
                })
        
        # If no specific technologies, maybe a generic fallback plan could be added here
        return plan
    finally:
        db.close()
