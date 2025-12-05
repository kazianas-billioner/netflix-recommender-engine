import os
# Force Legacy Keras for TensorFlow Recommenders
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import tensorflow as tf
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np

app = FastAPI()

# ==========================================
# 1. LOAD DATABASE (Robustly)
# ==========================================
try:
    # Read as string to avoid type errors
    movie_db = pd.read_csv("movies.csv", dtype=str)
    
    # CRITICAL: Fill empty values so the server doesn't crash on filter
    movie_db.fillna("", inplace=True)
    
    print(f"✅ Loaded Movie DB: {len(movie_db)} movies.")
except Exception as e:
    print(f"⚠️ CSV Error: {e}")
    movie_db = pd.DataFrame(columns=["title", "genre", "rating", "poster_path"])

# ==========================================
# 2. LOAD AI MODEL
# ==========================================
MODEL_PATH = os.path.join(os.getcwd(), "my_model")
serving_fn = None
try:
    loaded_obj = tf.saved_model.load(MODEL_PATH)
    serving_fn = loaded_obj.signatures["serving_default"]
    print("✅ AI Brain Loaded")
except:
    print("⚠️ AI Brain not found (Running in Fallback Mode)")

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_movie_details(title_list):
    """
    Takes a list of titles (from AI) and finds their posters in our Real DB.
    """
    results = []
    for title in title_list:
        clean_title = title.strip()
        # Case-insensitive search
        match = movie_db[movie_db['title'].str.lower() == clean_title.lower()]
        
        if not match.empty:
            row = match.iloc[0]
            results.append({
                "title": row['title'],
                "poster_path": row['poster_path'],
                "rating": f"{row['rating']}% Match"
            })
    return results

# ==========================================
# 4. API ENDPOINTS
# ==========================================
class UserRequest(BaseModel):
    user_id: str

class SearchRequest(BaseModel):
    query: str
    genre: str = "All"

@app.get("/")
def home():
    return {"status": "Online", "movies_loaded": len(movie_db)}

@app.post("/recommend")
def recommend(req: UserRequest):
    ai_picks_data = []
    
    # A. Try AI Prediction
    if serving_fn:
        try:
            input_tensor = tf.constant([req.user_id])
            try:
                preds = serving_fn(input_tensor)
            except:
                key = list(serving_fn.structured_input_signature[1].keys())[0]
                preds = serving_fn(**{key: input_tensor})
            
            for k in preds:
                if preds[k].dtype.kind in {'S', 'U', 'O'}:
                    raw = preds[k].numpy()[0]
                    titles = [t.decode('utf-8') for t in raw]
                    
                    # Convert AI Titles -> Real Objects with Posters
                    ai_picks_data = get_movie_details(titles)
                    break
        except Exception as e:
            print(f"AI Prediction Error: {e}")

    # B. If AI returns < 4 movies (because our 2025 DB doesn't have 1998 movies),
    # FILL the rest with Trending movies so the UI looks full.
    if len(ai_picks_data) < 4:
        needed = 8 - len(ai_picks_data)
        if not movie_db.empty:
            trending = movie_db.sample(n=min(needed, len(movie_db))).to_dict(orient="records")
            for m in trending:
                ai_picks_data.append({
                    "title": m['title'],
                    "poster_path": m['poster_path'],
                    "rating": f"{m['rating']}% Match"
                })

    return {"movies": ai_picks_data[:8]}

@app.post("/search")
def search_movies(req: SearchRequest):
    df = movie_db.copy()
    
    # 1. Keyword Search
    if req.query:
        df = df[df['title'].str.contains(req.query, case=False, na=False)]
    
    # 2. Genre Filter
    if req.genre != "All":
        df = df[df['genre'].str.contains(req.genre, case=False, na=False)]
    
    # 3. Format Output
    results = []
    for _, row in df.head(12).iterrows():
        results.append({
            "title": row['title'],
            "poster_path": row['poster_path'],
            "rating": f"{row['rating']}%"
        })
        
    return {"results": results}