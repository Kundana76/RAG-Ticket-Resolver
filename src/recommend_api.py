from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import pandas as pd, faiss, pickle, os


class Ticket(BaseModel):
    ticket_id: str
    ticket_text: str
    

class RecommendationAPI:
    def __init__(self, model_dir="models", log_dir="logs", top_k=3):
        self.model_dir = model_dir
        self.log_dir = log_dir
        self.top_k = top_k
        self.model, self.articles, self.index = self._load_resources()
        self.app = FastAPI(title="Real-Time Recommendation Engine")
        self._setup_routes()

    def _load_resources(self):
        with open(os.path.join(self.model_dir, "embed_model.pkl"), "rb") as f:
            model_info = pickle.load(f)
        model = SentenceTransformer(model_info["model_name"])
        articles = pd.read_pickle(os.path.join(self.model_dir, "articles_meta.pkl"))
        index = faiss.read_index(os.path.join(self.model_dir, "article_index.faiss"))
        return model, articles, index

    def _setup_routes(self):
        @self.app.get("/")
        def root():
            return {"message": "API is running!"}

        @self.app.post("/recommend")
        def recommend(ticket: Ticket):
            query_emb = self.model.encode([ticket.ticket_text], convert_to_numpy=True)
            faiss.normalize_L2(query_emb)
            D, I = self.index.search(query_emb, self.top_k)
            results = [
                {
                    "rank": i + 1,
                    "article_title": self.articles.iloc[idx]["title"],
                    "score": float(D[0][i]),
                }
                for i, idx in enumerate(I[0])
            ]
            os.makedirs(self.log_dir, exist_ok=True)
            pd.DataFrame([{
                "ticket_id": ticket.ticket_id,
                "query_text": ticket.ticket_text,
                "results": results,
            }])
            return {"ticket_id": ticket.ticket_id, "ticket_text": ticket.ticket_text, "recommendations": results}

    def get_app(self):
        return self.app



# Export the FastAPI app instance for uvicorn
api = RecommendationAPI(model_dir="models", log_dir="logs", top_k=3)
app = api.get_app()

