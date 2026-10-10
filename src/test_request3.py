import json
import requests
import pandas as pd
from typing import List, Dict


class RecommendationClient:
    """
    A client for interacting with the RecommendationAPI service.
    
    Sends support tickets to the FastAPI endpoint and retrieves
    the recommended knowledge base articles.
    """

    def __init__(self, api_url: str = "http://127.0.0.1:8000/recommend"):
        self.api_url = api_url

    # Core request method
    def send_ticket(self, ticket: Dict) -> Dict:
        # Sends a single ticket to the API and returns JSON response.
        try:
            response = requests.post(self.api_url, json=ticket, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending ticket {ticket.get('ticket_id')}: {e}")
            return {"ticket_id": ticket.get("ticket_id"), "error": str(e)}

    # Batch processing
    def process_tickets(self, csv_path: str) -> List[Dict]:
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        tickets = df.to_dict(orient="records")
        print(f"Loaded {len(tickets)} tickets from {csv_path}\n")

        all_results = []
        for ticket in tickets:
            result = self.send_ticket(ticket)
            all_results.append(result)

            # Pretty print each result
            print(json.dumps(result, indent=2))
            print("-" * 50)

        return all_results

    # Save results
    def save_results(self, results: List[Dict], output_path: str):
        if output_path.endswith(".csv"):
            pd.DataFrame(results).to_csv(output_path, index=False)
        else:
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

        print(f"Results saved to: {output_path}")


# Example Run
if __name__ == "__main__":
    client = RecommendationClient(api_url="http://127.0.0.1:8000/recommend")

    results = client.process_tickets("data/raw/tickets5.csv")
    client.save_results(results, "logs/recommendation_results5.csv")