import json
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingsManager:
    def __init__(self, dataset_path):
        self.base_dir = os.path.dirname(dataset_path)
        with open(dataset_path, 'r') as f:
            self.config = json.load(f)
            
        self.embeddings = {}
        self.item_ids = {}
        self.item_metadata = {}
        self._load_libraries()

    def _load_libraries(self):
        libraries = self.config.get("item_libraries", {})
        for lib_name, lib_info in libraries.items():
            json_file = os.path.join(self.base_dir, lib_info["file"])
            if not os.path.exists(json_file):
                continue
                
            with open(json_file, 'r') as f:
                lib_data = json.load(f)
            
            # Determine correct list key by guessing (e.g. presets, progressions)
            list_key = [k for k in lib_data.keys() if isinstance(lib_data[k], list)][0]
            items = lib_data[list_key]
            
            ids = [item["id"] for item in items]
            self.item_ids[lib_name] = ids
            
            # Store full item metadata for context-aware selection
            self.item_metadata[lib_name] = {item["id"]: item for item in items}
            
            emb_file = lib_info.get("embedding_file")
            if emb_file:
                emb_path = os.path.join(self.base_dir, emb_file)
                if os.path.exists(emb_path):
                    matrix = np.load(emb_path)
                    # Create a dict mapping id -> vector
                    emb_dict = {}
                    for i, item_id in enumerate(ids):
                        if i < matrix.shape[0]:
                            emb_dict[item_id] = matrix[i]
                    self.embeddings[lib_name] = emb_dict

    def get_similarity(self, lib_name, item_a, item_b):
        """Returns cosine similarity between two items in a library. Fallback to 0.0 or 1.0."""
        if item_a == item_b:
            return 1.0
            
        if lib_name in self.embeddings:
            lib_embs = self.embeddings[lib_name]
            if item_a in lib_embs and item_b in lib_embs:
                vec_a = lib_embs[item_a].reshape(1, -1)
                vec_b = lib_embs[item_b].reshape(1, -1)
                return cosine_similarity(vec_a, vec_b)[0][0]
                
        return 0.0

    def get_library_items(self, lib_name):
        return self.item_ids.get(lib_name, [])

    def get_item_metadata(self, lib_name, item_id):
        return self.item_metadata.get(lib_name, {}).get(item_id, {})
