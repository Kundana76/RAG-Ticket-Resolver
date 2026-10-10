import os
import ast
import numpy as np
import pandas as pd


class RecommendationAnalyzer:
    def __init__(self, log_path="logs/recommendation_results_tickets5.csv", output_dir="logs"):
        self.log_path = log_path
        self.output_dir = output_dir
        self.logs_df = None
        self.expanded_df = None
        self.summary_df = None
        os.makedirs(self.output_dir, exist_ok=True)


    def load_logs(self):
        if not os.path.exists(self.log_path):
            raise FileNotFoundError("No recommendation logs found. Run recommend_api.py first!")

        # Load the recommendation logs
        self.logs_df = pd.read_csv(self.log_path)
        
        # Rename columns to match expected names
        self.logs_df.rename(columns={"ticket_text": "text", "recommendations": "results"}, inplace=True)

        # Safely evaluate the stringified Python list of dicts
        import ast
        def safe_eval(x):
            if isinstance(x, str):
                try:
                    return ast.literal_eval(x)
                except (ValueError, SyntaxError):
                    print("Skipping malformed entry:", x)
                    return []
            return []

        self.logs_df["results"] = self.logs_df["results"].apply(safe_eval)

        print(f"Loaded {len(self.logs_df)} log entries.")

    def expand_logs(self):
        if self.logs_df is None:
            raise ValueError("Logs not loaded. Run load_logs() first.")

        rows = []
        for _, row in self.logs_df.iterrows():
            for rec in row["results"]:
                rows.append({
                    "ticket_id": row["ticket_id"],
                    "article": rec.get("article_title", "Unknown"),
                    "score": rec.get("score", 0.0)
                })

        if not rows:
            raise ValueError("No recommendations found in logs!")

        self.expanded_df = pd.DataFrame(rows)
        print(f"Expanded to {len(self.expanded_df)} recommendation rows.")

    def compute_metrics(self):
        """
        Compute impressions, average score, simulated clicks, and CTR.
        """
        if self.expanded_df is None:
            raise ValueError("No expanded logs available. Run expand_logs() first.")

        summary = self.expanded_df.groupby("article").agg(
            impressions=("ticket_id", "count"),
            avg_score=("score", "mean")
        ).reset_index()

        # Simulate clicks for demo (replace with real click data in production)
        np.random.seed(42)
        summary["clicks"] = np.random.randint(0, summary["impressions"] + 1)
        summary["CTR"] = summary["clicks"] / summary["impressions"].replace(0, 1)

        self.summary_df = summary
        print("Metrics computed successfully.")


    def detect_low_engagement(self, ctr_threshold=0.6):
        """
        Detect articles with low click-through rate (CTR) and unused ones.
        """
        if self.summary_df is None:
            raise ValueError("Metrics not computed. Run compute_metrics() first.")

        low_ctr = self.summary_df[self.summary_df["CTR"] < ctr_threshold]
        unused = self.summary_df[self.summary_df["impressions"] == 0]

        print(f"Found {len(low_ctr)} low CTR articles and {len(unused)} unused ones.")
        return low_ctr, unused


    def save_report(self, filename="coverage_report5.csv"):
        if self.summary_df is None:
            raise ValueError("No summary data available to save.")

        output_path = os.path.join(self.output_dir, filename)
        self.summary_df.to_csv(output_path, index=False)
        print(f"Coverage report saved at: {output_path}")
        return output_path


    def run_full_analysis(self):
        self.load_logs()
        self.expand_logs()
        self.compute_metrics()
        low_ctr, unused = self.detect_low_engagement()
        report_path = self.save_report()

        print("\nSUMMARY REPORT")
        print(f"Total Articles Analyzed: {len(self.summary_df)}")
        print(f"Low CTR Articles: {len(low_ctr)}")
        print(f"Unused Articles: {len(unused)}")

        return {
            "summary": self.summary_df,
            "low_ctr": low_ctr,
            "unused": unused,
            "report_path": report_path
        }


# Example Usage
if __name__ == "__main__":
    analyzer = RecommendationAnalyzer(log_path="logs/recommendation_results5.csv", output_dir="logs")
    results = analyzer.run_full_analysis()

    print("\nLow CTR Articles:")
    print(results["low_ctr"][["article", "CTR", "impressions"]])

    print("\nUnused Articles:")
    print(results["unused"][["article", "impressions"]])
