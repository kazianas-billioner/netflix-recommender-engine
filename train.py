import os
os.environ["TF_USE_LEGACY_KERAS"] = "1" # Keep this fix

import tensorflow as tf
import tensorflow_datasets as tfds
import tensorflow_recommenders as tfrs
import numpy as np

# 1. Load Data
print("Loading data...")
ratings = tfds.load("movielens/100k-ratings", split="train")
movies = tfds.load("movielens/100k-movies", split="train")

# 2. Map Data
ratings = ratings.map(lambda x: {
    "movie_title": x["movie_title"],
    "user_id": x["user_id"],
})
movies = movies.map(lambda x: x["movie_title"])

# 3. Vocabularies
print("Building vocabularies...")
user_ids_vocabulary = tf.keras.layers.StringLookup(mask_token=None)
user_ids_vocabulary.adapt(ratings.map(lambda x: x["user_id"]))

movie_titles_vocabulary = tf.keras.layers.StringLookup(mask_token=None)
movie_titles_vocabulary.adapt(movies)

# 4. Model
class NetflixModel(tfrs.Model):
    def __init__(self):
        super().__init__()
        self.user_model = tf.keras.Sequential([
            user_ids_vocabulary,
            tf.keras.layers.Embedding(user_ids_vocabulary.vocabulary_size(), 32)
        ])
        self.movie_model = tf.keras.Sequential([
            movie_titles_vocabulary,
            tf.keras.layers.Embedding(movie_titles_vocabulary.vocabulary_size(), 32)
        ])
        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(
                candidates=movies.batch(128).map(self.movie_model)
            )
        )

    def compute_loss(self, features, training=False):
        user_embeddings = self.user_model(features["user_id"])
        movie_embeddings = self.movie_model(features["movie_title"])
        return self.task(user_embeddings, movie_embeddings)

# 5. Train
model = NetflixModel()
model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))
print("Training started...")
model.fit(ratings.batch(4096), epochs=3)

# 6. Save (THE FIX IS HERE)
print("Building search index...")
index = tfrs.layers.factorized_top_k.BruteForce(model.user_model)
index.index_from_dataset(
  tf.data.Dataset.zip((movies.batch(100), movies.batch(100).map(model.movie_model)))
)

# --- CRITICAL FIX: Run the model once so it creates the 'serving_default' signature ---
print("Warming up model to generate signature...")
_ = index(tf.constant(["42"])) 
# ------------------------------------------------------------------------------------

save_path = os.path.join(os.getcwd(), "my_model")
tf.saved_model.save(index, save_path)
print(f"SUCCESS: Model saved correctly to {save_path}")