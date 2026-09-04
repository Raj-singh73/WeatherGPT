"""
retriever.py - Lightweight Vector & Semantic Document Retrieval Engine for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

import os
import glob
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "rag", "documents")

class RAGRetriever:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.tfidf_matrix = None
        self._load_and_index_documents()
        
    def _load_and_index_documents(self):
        doc_files = glob.glob(os.path.join(DOCS_DIR, "*.md"))
        for fpath in doc_files:
            fname = os.path.basename(fpath)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Chunk by markdown sections (##)
            sections = content.split("## ")
            doc_title = sections[0].replace("#", "").strip() if len(sections) > 0 else fname
            
            for sec in sections[1:]:
                lines = sec.strip().split("\n")
                heading = lines[0].strip()
                body = "\n".join(lines[1:]).strip()
                
                self.chunks.append({
                    "title": f"{doc_title} — {heading}",
                    "source": f"WeatherGPT Knowledge Base ({fname})",
                    "content": f"{heading}\n{body}"
                })
                
        if self.chunks:
            corpus = [c["content"] for c in self.chunks]
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieves top-k most relevant knowledge base chunks for a user query."""
        if not self.chunks or self.tfidf_matrix is None:
            return []
            
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        top_indices = scores.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.05: # Minimum relevance threshold
                c = self.chunks[idx].copy()
                c["relevance_score"] = round(score, 3)
                results.append(c)
                
        return results

# Singleton instance
_RETRIEVER = None

def get_retriever() -> RAGRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = RAGRetriever()
    return _RETRIEVER

if __name__ == "__main__":
    r = get_retriever()
    print(f"Loaded {len(r.chunks)} knowledge chunks.")
    query = "Is it safe to spray pesticide when rain is coming?"
    res = r.retrieve(query)
    for match in res:
        print(f"\n--- {match['title']} (Score: {match['relevance_score']}) ---")
        print(match['content'][:250] + "...")
