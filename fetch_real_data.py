import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv # pip install python-dotenv

# Load environment variables
load_dotenv()

# Get Key securely (returns None if not found)
API_KEY = os.getenv("TMDB_API_KEY")

def fetch_movies():
    if not API_KEY:
        print("❌ ERROR: API Key not found. Create a .env file with TMDB_API_KEY=your_key")
        return

    print(f"🚀 Connecting to TMDB...")
    
    all_movies = []
    
    # Fetch 50 pages (1000 movies)
    for page in range(1, 51):
        try:
            url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page={page}"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"⚠️ Error on page {page}: {response.status_code}")
                break
            
            data = response.json()
            results = data.get('results', [])
            
            for item in results:
                genre_map = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 53: "Thriller", 10752: "War", 37: "Western"}
                g_id = item['genre_ids'][0] if item.get('genre_ids') else 18
                
                movie = {
                    "title": item.get('title', 'Unknown'),
                    "genre": genre_map.get(g_id, "Drama"),
                    "rating": int(item.get('vote_average', 0) * 10),
                    "poster_path": item.get('poster_path'),
                    "overview": item.get('overview', ''),
                    "id": item.get('id')
                }
                all_movies.append(movie)
            
            print(f"✅ Downloaded Page {page}/50")
            time.sleep(0.1) 
            
        except Exception as e:
            print(f"❌ Crash on page {page}: {e}")

    if len(all_movies) > 0:
        df = pd.DataFrame(all_movies)
        df.to_csv("movies.csv", index=False)
        print(f"\n🎉 SUCCESS! Saved {len(df)} real movies.")
    else:
        print("❌ No movies downloaded.")

if __name__ == "__main__":
    fetch_movies()