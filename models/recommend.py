import pickle
import pandas as pd
import plotly.express as px
import numpy as np
import logging

def get_recommendations(user_id=None, product_id=None, customer_name=None, category=None):
    try:
        with open('data/model.pkl', 'rb') as f:
            model_data = pickle.load(f)
    except Exception as e:
        logging.error(f"Failed to load model: {str(e)}")
        raise Exception("Recommendation engine not available")

    data = model_data.get('data', pd.DataFrame())
    
    # Convert inputs to correct types
    try:
        user_id = int(user_id) if user_id else None
        product_id = int(product_id) if product_id else None
    except (ValueError, TypeError):
        logging.warning("Invalid ID format received")
        user_id, product_id = None, None

    # Initialize default recommendations
    recommendations = model_data.get('popular_items', [])
    
    # User-based recommendations
    if user_id is not None:
        if user_id in model_data.get('user_ids', []):
            user_idx = model_data['user_ids'].index(user_id)
            
            # Collaborative filtering with error handling
            try:
                distances, indices = model_data['cf_model'].kneighbors(
                    [model_data['user_item_values'][user_idx]],
                    n_neighbors=min(5, len(model_data['product_ids']))
                )
                cf_recommendations = []
                for i in indices.flatten():
                    if 0 <= i < len(model_data['product_ids']):
                        cf_recommendations.append(model_data['product_ids'][i])
                    else:
                        logging.warning(f"Invalid product index: {i}")
                
                # Content-based filtering
                user_data = data[data['user_id'] == user_id]
                cb_recommendations = []
                if not user_data.empty:
                    preferred_category = user_data['category'].mode()[0] if not user_data['category'].empty else None
                    if preferred_category:
                        cb_recommendations = data[
                            (data['category'] == preferred_category) & 
                            (~data['product_id'].isin(user_data['product_id']))
                        ].sort_values('rating', ascending=False)['product_id'].head(3).tolist()
                
                recommendations = list(set(cf_recommendations + cb_recommendations)) or recommendations
            except Exception as e:
                logging.error(f"CF recommendation error: {str(e)}")
    
    # Product-based recommendations
    elif product_id is not None:
        if product_id in model_data.get('product_ids', []):
            try:
                product_idx = data[data['product_id'] == product_id].index[0]
                sim_scores = list(enumerate(model_data['content_similarity'][product_idx]))
                sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
                valid_recommendations = []
                for i, score in sim_scores:
                    try:
                        valid_recommendations.append(data.iloc[i]['product_id'])
                    except IndexError:
                        continue
                recommendations = valid_recommendations or recommendations
            except Exception as e:
                logging.error(f"Content-based recommendation error: {str(e)}")
    
    # Customer name-based recommendations
    elif customer_name:
        try:
            user_ids = data[data['customer_name'].str.contains(str(customer_name), case=False, na=False)]['user_id'].unique()
            if len(user_ids) > 0:
                return get_recommendations(user_id=user_ids[0])
        except Exception as e:
            logging.error(f"Customer name lookup error: {str(e)}")
    
    # Category-based recommendations
    elif category:
        try:
            category_recs = data[data['category'] == category]\
                .groupby('product_id')['purchase_count']\
                .sum()\
                .sort_values(ascending=False)\
                .head(5)\
                .index.tolist()
            recommendations = category_recs or recommendations
        except Exception as e:
            logging.error(f"Category recommendation error: {str(e)}")
    
    # Prepare recommendation details with error handling
    try:
        rec_details = []
        if len(recommendations) > 0:
            rec_details = data[data['product_id'].isin(recommendations)][
                ['product_id', 'category', 'price', 'rating']
            ].drop_duplicates().to_dict('records')
        
        # Generate visualization
        if rec_details:
            fig = px.bar(
                pd.DataFrame(rec_details),
                x='product_id',
                y='rating',
                color='price',
                title='Recommended Products Analysis'
            )
            plot_html = fig.to_html(full_html=False)
        else:
            plot_html = "<div class='alert alert-warning'>No recommendations available</div>"
        
        return rec_details, plot_html
    except Exception as e:
        logging.error(f"Presentation error: {str(e)}")
        return [], "<div class='alert alert-danger'>Error generating recommendations</div>"