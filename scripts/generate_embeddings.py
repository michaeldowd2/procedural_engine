import json
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

def generate_instrument_embeddings():
    filepath = "../models/song/data/instrument_presets.json"
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    presets = data['presets']
    
    # Create a string representation of properties for each preset
    documents = []
    ids = []
    for preset in presets:
        ids.append(preset['id'])
        # Combine instrument, tags, and genres
        features = [preset['instrument']] + preset['tags'] + preset['genres']
        documents.append(" ".join(features))
    
    # Use TF-IDF to create numerical representations
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(documents).toarray()
    
    # If the user requested size=100 in the schema, but we only have a few features,
    # let's just use what we have, or pad it. However, the vectorizer will find N features.
    print(f"Generated {X.shape[1]} features for {len(documents)} instruments.")
    
    # The example config expects 100 dimensions (from item2vec), 
    # but since this is small data, we'll just save the raw tfidf vectors (or pad to 100 if we must).
    # Since we're building the engine, we won't strictly enforce dim=100 dynamically.
    
    # Save the embeddings file
    out_file = "../models/song/data/instrument_embeddings.npy"
    # To keep it useful, we can save a dictionary rather than just raw numpy array, 
    # but dataset.json implies an `.npy` file. We will save the matrix, and expect 
    # the order to match the presets array, or we save an npz with 'vectors' and 'ids'.
    # Let's just save the matrix and let the embeddings manager pair by index.
    np.save(out_file, X)
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    os.makedirs(os.path.dirname("../models/song/data/instrument_embeddings.npy"), exist_ok=True)
    generate_instrument_embeddings()
