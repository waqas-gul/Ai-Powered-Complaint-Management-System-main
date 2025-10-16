import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import pandas as pd

def create_dummy_models():
    # Sample training data
    sample_data = {
        'text': [
            "I have issues with my billing statement",
            "My internet connection is very slow",
            "The product quality is poor",
            "I want to cancel my subscription",
            "The customer service was rude",
            "I have problems with my account",
            "The website is not working properly",
            "I was charged twice for the same service",
            "The delivery was late",
            "The product arrived damaged"
        ],
        'category': [
            'Billing', 'Technical', 'Product', 'Billing', 'Customer Service',
            'Account', 'Technical', 'Billing', 'Delivery', 'Product'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create and fit vectorizer
    tfidf_vect = TfidfVectorizer(max_features=1000)
    X = tfidf_vect.fit_transform(df['text'])
    
    # Create and fit encoder
    encoder = LabelEncoder()
    y = encoder.fit_transform(df['category'])
    
    # Create and train model
    model = LogisticRegression()
    model.fit(X, y)
    
    # Save models
    joblib.dump(model, 'customer_classification_model_lr.pkl')
    joblib.dump(tfidf_vect, 'tfidf_vectorizer.pkl')
    joblib.dump(encoder, 'label_encoder.pkl')
    
    print("Dummy models created successfully!")
    print("You can now test the complaint classification system.")

if __name__ == "__main__":
    create_dummy_models()