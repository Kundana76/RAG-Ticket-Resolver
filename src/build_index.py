"""
Build the FAISS index over data/kb_articles.csv.

Usage (from repo root):  python -m src.build_index
Creates models/article_index.faiss, models/articles_meta.pkl, models/embed_model.pkl
"""
import os
import pickle

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer

DATA_PATH = "data/kb_articles.csv"
MODEL_NAME = "all-MiniLM-L6-v2"
OUT_DIR = "models"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    missing = {"title", "content"} - set(df.columns)
    if missing:
        raise ValueError(f"{DATA_PATH} missing columns: {missing}")

    df["text"] = df["title"].fillna("") + ". " + df["content"].fillna("")
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(df["text"].tolist(), convert_to_numpy=True, show_progress_bar=True)
    faiss.normalize_L2(emb)

    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)

    faiss.write_index(index, os.path.join(OUT_DIR, "article_index.faiss"))
    df.to_pickle(os.path.join(OUT_DIR, "articles_meta.pkl"))
    with open(os.path.join(OUT_DIR, "embed_model.pkl"), "wb") as f:
        pickle.dump({"model_name": MODEL_NAME}, f)
    print(f"Indexed {index.ntotal} articles -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
