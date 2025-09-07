import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.neighbors import NearestNeighbors
import pickle

class RecommendationEngine:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        self.prepare_data()
        self.train_models()
        
    def prepare_data(self):
        # Feature engineering
        self.data['features'] = self.data.apply(lambda row: 
            f"{row['category']} {row['price']} {row['user_age']} {row['user_gender']}", axis=1)
        
        # Create user-item matrix (sparse format for efficiency)
        self.user_item_matrix = self.data.pivot_table(
            index='user_id',
            columns='product_id',
            values='rating',
            fill_value=0
        )
        self.product_ids = self.user_item_matrix.columns.tolist()
        self.user_ids = self.user_item_matrix.index.tolist()
        
    def train_models(self):
        # Content-based filtering
        self.tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = self.tfidf.fit_transform(self.data['features'])
        self.content_similarity = linear_kernel(tfidf_matrix, tfidf_matrix)
        
        # Collaborative filtering (convert to sparse matrix)
        self.cf_model = NearestNeighbors(metric='cosine', algorithm='brute')
        self.cf_model.fit(self.user_item_matrix.values)
        
        # Popular items
        self.popular_items = self.data.groupby('product_id')['purchase_count'].sum().sort_values(ascending=False).head(10).index.tolist()
        
    def save_models(self, output_path):
        # Save only what's needed for recommendations
        model_data = {
            'content_similarity': self.content_similarity,
            'cf_model': self.cf_model,
            'popular_items': self.popular_items,
            'product_ids': self.product_ids,
            'user_ids': self.user_ids,
            'data': self.data[['product_id', 'category', 'price', 'rating', 'user_id', 'customer_name']],
            'user_item_values': self.user_item_matrix.values  # Save the matrix values
        }
        with open(output_path, 'wb') as f:
            pickle.dump(model_data, f)

if __name__ == '__main__':
    engine = RecommendationEngine('data/Realtime.csv')
    engine.save_models('data/model.pkl')
    print("Model trained and saved successfully")