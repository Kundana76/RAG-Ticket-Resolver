"""Central settings, overridable via environment variables."""
import os

CONFIDENCE_HIGH = float(os.getenv("CONFIDENCE_HIGH", "0.85"))
CONFIDENCE_MEDIUM = float(os.getenv("CONFIDENCE_MEDIUM", "0.50"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
