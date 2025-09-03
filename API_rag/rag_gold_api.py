# rag_gold_api.py
import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from mistralai import Mistral  # you already used this client
import json
from dotenv import load_dotenv
from pathlib import Path


load_dotenv() 
keys_string = os.environ.get("MISTRAL_API_KEY", "")

# Convert back to list (split by comma, strip spaces)
keys = [k.strip() for k in keys_string.split(",") if k.strip()]

app = FastAPI(title="Gold-RAG-Detector")

import itertools
import requests


def get_mistral_client(api_key):
    return Mistral(api_key=api_key)

def get_valid_api_key():
    """
    Checks all API keys and returns the first valid one.
    If none are valid, raises an Exception.
    """
    for api_key in keys:
        try:
            client = get_mistral_client(api_key)
            # Do a tiny test request
            response = client.chat.complete(
                model="mistral-small-latest",  # lightweight check
                messages=[{"role": "user", "content": "ping"}]
            )
            if response:  # Key worked
                return api_key  
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Quota/rate limit reached
                continue
        except Exception:
            continue
    
    # If we reach here, no key worked
    raise Exception("No valid API key available!")

def call_mistral(messages, model="mistral-small", temperature=0.2, max_tokens=500, retries=None):
    

    for _ in range(retries):
        api_key = get_valid_api_key()
        client = Mistral(api_key=api_key)
        try:
            resp = client.chat.complete(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                print(f"[WARN] Key {api_key} rate-limited, switching key...")
                continue
            else:
                raise e
    raise HTTPException(status_code=429, detail="All API keys exhausted")

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good tradeoff
embedder = SentenceTransformer(EMBED_MODEL_NAME)

# Globals (built at startup)
faiss_index = None
chunks: List[str] = []
chunk_embeddings = None
EMBED_DIM = None

# Thresholds
SIMILARITY_THRESHOLD = 0.65  # tune between 0.55-0.8 depending on test set
TOP_K = 3

class QueryIn(BaseModel):
    message: str

class QueryOut(BaseModel):
    intent: str
    reply: str
    retrieved: List[str] = []

def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    # Simple chunker: split on paragraphs/sentences heuristically
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    print(f"[DEBUG] Found {len(paragraphs)} paragraphs")
    out = []
    buff = ""
    for p in paragraphs:
        if len(buff) + len(p) + 1 <= max_chars:
            buff = (buff + "\n\n" + p).strip()
        else:
            if buff:
                out.append(buff)
                print(f"[DEBUG] Added chunk (len={len(buff)}): {buff[:60]}...")
            buff = p
    if buff:
        out.append(buff)
        print(f"[DEBUG] Added chunk (len={len(buff)}): {buff[:60]}...")
    # Final safety: split any too-large chunk
    final = []
    for c in out:
        if len(c) <= max_chars:
            final.append(c)
        else:
            # split by sentences if too big
            parts = [c[i:i+max_chars] for i in range(0, len(c), max_chars)]
            final.extend(parts)
            print(f"[DEBUG] Split large chunk into {len(parts)} parts")
    print(f"[DEBUG] Total chunks after splitting: {len(final)}")
    return final

def build_index_from_file(path: str):
    global faiss_index, chunks, chunk_embeddings, EMBED_DIM
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"[DEBUG] Loaded KB file with {len(text)} characters")
    chunks = chunk_text(text, max_chars=700)
    print(f"[DEBUG] Chunks created: {len(chunks)}")
    # compute embeddings
    emb = embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
    # normalize
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms==0] = 1e-9
    emb = emb / norms
    EMBED_DIM = emb.shape[1]
    # build faiss index (inner product on normalized vectors = cosine similarity)
    faiss_index = faiss.IndexFlatIP(EMBED_DIM)
    faiss_index.add(emb)
    chunk_embeddings = emb

def retrieve(query: str, top_k: int = TOP_K):
    q_emb = embedder.encode([query], convert_to_numpy=True)
    q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-9)
    D, I = faiss_index.search(q_emb, top_k)  # D = inner products
    scores = D[0].tolist()
    idxs = I[0].tolist()
    results = []
    for s, i in zip(scores, idxs):
        if i < 0:
            continue
        results.append((s, chunks[i]))
    return results

@app.on_event("startup")
def startup_event():
    # Path to your gold KB text file
    kb_path = os.getenv("GOLD_KB_PATH", "gold_doc.txt")
    if not Path(gold_kb_path).exists():
        gold_kb_path = r"C:\Desktop\Chatbot\gold_doc.txt"
    if not os.path.exists(kb_path):
        raise RuntimeError(f"KB file not found at {kb_path}")
    build_index_from_file(kb_path)
    print(f"Built FAISS index with {len(chunks)} chunks. EMBED_DIM={EMBED_DIM}")

def classify_by_similarity(retrieved):
    # retrieved is list[(score, chunk)]
    if not retrieved:
        return False
    top_score = retrieved[0][0]
    return float(top_score) >= SIMILARITY_THRESHOLD

def format_context(retrieved):
    # join retrieved chunks into a context block
    parts = []
    for score, chunk in retrieved:
        parts.append(f"--- (score={score:.3f}) ---\n{chunk}")
    return "\n\n".join(parts)

def call_mistral_answer(query: str, context: str):
    messages = [
        {"role": "system", 
        "content": """You are a helpful financial assistant specialized in gold investments. 
            1. first answer their query normally using the context. 
            2. **Then, softly suggest Digital Gold as a modern option (mention convenience, security, and small investments).**
            3. Do not be pushy — just end by asking politely if they want to know more.
            Example:  
            User: "Is gold a good investment for the future?"  
            Assistant: "Yes, gold is traditionally considered a safe investment during uncertain times because it preserves value.  
                        Along with physical gold, many investors today also explore Digital Gold since it allows you to invest small amounts, offers secure storage, and is easy to buy or sell online.  
                        Would you like me to share more about how Digital Gold works?" """
        },
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"}
    ]
    return call_mistral(messages, model="mistral-small", temperature=0.2)

@app.post("/detect_gold_intent", response_model=QueryOut)
def detect_gold_intent(payload: QueryIn):
    # 1) Retrieve context
    retrieved = retrieve(payload.message, top_k=TOP_K)
    # 2) Decide intent
    is_gold = classify_by_similarity(retrieved)
    if not is_gold:
        # Optional: run a light clarifying classification via Mistral (structured JSON)
        # Here we return 'other' with a short model-generated reply
        # Keep the reply short to save tokens
        messages = [
            {"role": "system", "content": "You are an intent classifier. Reply ONLY in JSON with the field 'intent': 'gold_investment' or 'other'."},
            {"role": "user", "content": f"Query: {payload.message}\n\nExamples:\nQ: 'Should I buy SGBs?' -> intent: gold_investment\nQ: 'How to file income tax' -> intent: other\n\nNow classify the query above."}
        ]
        try:
            # r = client.chat.complete(model="mistral-small", messages=messages, temperature=0.0)
            txt = call_mistral(messages, model="mistral-small", temperature=0.0)
            # attempt to parse JSON in response
            parsed = {}
            try:
                parsed = json.loads(txt)
                if parsed.get("intent") == "gold_investment":
                    is_gold = True
            except Exception:
                # fallback: keep is_gold False
                pass
        except Exception:
            pass

    if is_gold:
        context = format_context(retrieved)
        answer = call_mistral_answer(payload.message, context)
        return QueryOut(intent="gold_investment", reply=answer, retrieved=[c for (_s,c) in retrieved])
    else:
        # not gold: short reply or route to general assistant
        messages = [
            {"role": "system", "content": "You are a general assistant. Answer briefly if the query is not about gold investment."},
            {"role": "user", "content": payload.message}
        ]
        reply = call_mistral(messages, model="mistral-small", temperature=0.2)
        return QueryOut(intent="other", reply=reply, retrieved=[c for (_s,c) in retrieved])