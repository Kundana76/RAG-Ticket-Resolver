"""
Run the AI Support Copilot API server.
Usage: python run_copilot.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "copilot.copilot_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
