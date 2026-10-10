import pandas as pd
import datetime
import os
import requests
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()


def notify_escalation(doc: dict) -> bool:
    """Instant Slack message when a ticket is escalated. No-op without SLACK_WEBHOOK_URL."""
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return False
    arts = ", ".join(a.get("title", "") for a in doc.get("recommended_articles", [])[:3]) or "none"
    text = (
        f":rotating_light: *Ticket escalated* `{doc.get('ticket_id')}`\n"
        f"*Category:* {doc.get('category')}  |  *Priority:* {doc.get('priority')}  |  "
        f"*Confidence:* {doc.get('confidence_score', 0):.2f}\n"
        f"*Issue:* {doc.get('issue_summary')}\n"
        f"*Likely cause:* {doc.get('probable_root_cause')}\n"
        f"*Closest KB articles:* {arts}"
    )
    try:
        requests.post(url, json={"text": text}, timeout=5).raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Slack escalation alert failed: {e}")
        return False


class DailyAlertScheduler:
    def __init__(self, slack_webhook_url, coverage_report_path="logs/coverage_report5.csv", alert_log_path="logs/alerts5.log"):
        self.slack_webhook_url = slack_webhook_url
        self.coverage_report_path = coverage_report_path
        self.alert_log_path = alert_log_path

        # Initialize the scheduler (imported lazily so the API doesn't need apscheduler)
        from apscheduler.schedulers.blocking import BlockingScheduler
        self.scheduler = BlockingScheduler()

        # Set thresholds
        self.CTR_THRESHOLD = 0.5
        self.COVERAGE_THRESHOLD = 0.7  # For future use

        # Add daily job
        self.scheduler.add_job(self.daily_alert, "interval", hours=24)

    def send_slack_alert(self, message: str):
        payload = {
            "text": f"*Daily Gap Analysis Alert*\n{message}"
        }
        try:
            response = requests.post(self.slack_webhook_url, json=payload)
            response.raise_for_status()
            print("Slack alert sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Slack alert: {e}")

    # Perform the daily alert check, read the coverage report, and send the alert.
    def daily_alert(self):
        # Check if coverage report exists
        if not os.path.exists(self.coverage_report_path):
            print(f"No coverage report found at {self.coverage_report_path}. Please run gap_analysis.py first.")
            return

        # Load coverage report
        df = pd.read_csv(self.coverage_report_path)

        # Filter low CTR articles
        low_ctr = df[df["CTR"] < self.CTR_THRESHOLD]

        # Create alert message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_message = f"\n[{timestamp}] ALERT SUMMARY\n"

        if low_ctr.empty:
            alert_message += "All articles performing well. No low CTR detected.\n"
        else:
            alert_message += f"Low CTR articles detected (CTR < {self.CTR_THRESHOLD * 100}%):\n"
            alert_message += low_ctr[["article", "CTR", "impressions"]].to_string(index=False)
            alert_message += "\n"

        # Save Alert Log
        os.makedirs("logs", exist_ok=True)
        with open(self.alert_log_path, "a") as f:
            f.write(alert_message + "\n")

        # Print Alert Summary
        print(alert_message)
        print(f"Alert logged successfully at {self.alert_log_path}")

        # Send Slack Alert
        self.send_slack_alert(alert_message)

    def start(self):
        print("Alert scheduler started... (runs every 24 hours)")
        print("Press Ctrl+C to stop.\n")

        # Run immediately for testing (optional)
        self.daily_alert()

        # Start the scheduler
        self.scheduler.start()


# Main execution
if __name__ == "__main__":
    # Slack webhook URL should be provided as an environment variable
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL environment variable not set.")
    
    # Initialize and start the alert scheduler
    alert_scheduler = DailyAlertScheduler(slack_webhook_url=SLACK_WEBHOOK_URL, coverage_report_path="logs/coverage_report5.csv", alert_log_path="logs/alerts5.log")
    alert_scheduler.start()