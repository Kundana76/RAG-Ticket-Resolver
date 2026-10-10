import os
import json
import time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv


class TicketClassifier:
    """
    A class-based system to classify support tickets using Groq's LLaMA model.
    """
    def __init__(self, api_key_env="GROQ_API_KEY", model="llama-3.1-8b-instant"):
        # Load Environment Variables
        load_dotenv()

        # Initialize Groq Client
        self.client = Groq(api_key=os.getenv(api_key_env))
        self.model = model

        # Define few-shot examples
        self.examples = [
            {"text": "App not loading after update",
             "category": "Technical",
             "tags": ["app-crash", "update"]},

            {"text": "Payment deducted twice",
             "category": "Billing",
             "tags": ["refund", "duplicate-charge"]},

            {"text": "Password reset email not received",
             "category": "Account",
             "tags": ["login", "email"]}
        ]


    def load_tickets(self, filepath: str):
        try:
            df = pd.read_csv(filepath)
            self.tickets = df["clean_text"].tolist()
            print(f"Info: Loaded {len(self.tickets)} tickets for classification.\n")
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{filepath}' not found. Please ensure preprocessing completed.")


    def build_prompt(self, ticket_text: str) -> str:
        example_block = "\n\n".join(
            [f"""Example:
    Ticket: {e['text']}
    Category: {e['category']}
    Tags: {e['tags']}""" for e in self.examples]
        )

        format_example = """
    Expected Output Format (JSON):
    {
        "category": "Billing",
        "tags": ["refund", "duplicate-charge"],
        "confidence": 0.92
    }
    """

        prompt = f"""
    You are a support ticket classification engine.

    Your job is to read customer support tickets and classify them into one of the categories:
    [Billing, Technical, Account, Product, Refund, Delivery, Other]

    For each ticket, return a JSON with the following keys:
    - category (string)
    - tags (list of 2-3 relevant keywords)
    - confidence (a float between 0 and 1 showing how confident you are)

    Use the examples below as guidance:

    {example_block}

    {format_example}

    Now classify this new ticket:
    Ticket: {ticket_text}

    Respond ONLY in JSON.
    """
        return prompt.strip()

    def classify_ticket(self, ticket_id: str, text: str) -> dict:
        """
        Sends a single ticket to the LLaMA model and returns classification result.
        """
        prompt = self.build_prompt(text)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a support ticket classification engine. "
                            "Given a support ticket, classify it into one of the categories: "
                            "[Billing, Technical, Account, Product, Refund, Delivery, Other].\n"
                            "Return a JSON with these keys:\n"
                            "- category (string)\n"
                            "- tags (list of 2-3 relevant keywords)\n"
                            "- confidence (float between 0 and 1)\n"
                            "Follow the few-shot examples and return only valid JSON. Do not include explanations."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )

            raw_output = completion.choices[0].message.content.strip()

            # Clean markdown JSON wrappers
            if raw_output.startswith("```json"):
                raw_output = raw_output.replace("```json", "").replace("```", "").strip()
            elif raw_output.startswith("```"):
                raw_output = raw_output.replace("```", "").strip()

            try:
                parsed = json.loads(raw_output)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                parsed = {
                    "category": "Unknown",
                    "tags": [],
                    "confidence": 0.0,
                    "error": f"JSONDecodeError: {str(e)}"
                }

            return {
                "ticket_id": ticket_id,
                "ticket_text": text,
                "pred_category": parsed.get("category"),
                "tags": parsed.get("tags"),
                "confidence": parsed.get("confidence")
            }

        except Exception as e:
            return {
                "ticket_id": ticket_id,
                "ticket_text": text,
                "pred_category": None,
                "tags": None,
                "confidence": None,
                "error": str(e)
            }

    def classify_all(self, ticket_id: list[str], text: list[str], rate_limit = 1):
        print("Ticket classification started...\n")
        self.results = []

        for ticket_id, text in zip(ticket_id, text):
            result = self.classify_ticket(ticket_id,text)
            self.results.append(result)
            time.sleep(rate_limit)

        print("Ticket classification completed.\n")

    def save_results(self, output_path="data/processed/classified_tickets6.csv"):
        results_df = pd.DataFrame(self.results)
        results_df.to_csv(output_path, index=False)
        print(f"Results saved to '{output_path}'.")

        # Log errors if any
        error_df = results_df[results_df["pred_category"].isna()]
        if not error_df.empty:
            os.makedirs("logs", exist_ok=True)
            error_df.to_csv("logs/error_log6.csv", index=False)
            print(f"Logged {len(error_df)} failed records to 'logs/error_log6.csv'.")

        print("\nSUMMARY REPORT:")
        print(f"Total Tickets Processed: {len(self.tickets)}")
        print(f"Successful: {len(results_df) - len(error_df)} | Failed: {len(error_df)}")



# Example Usage
if __name__ == "__main__":
    classifier = TicketClassifier()
    classifier.load_tickets("data/processed/preprocessed_tickets6.csv")
    classifier.classify_all(rate_limit=1)
    classifier.save_results("data/processed/classified_tickets6.csv")
