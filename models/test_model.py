import joblib
import os

def test_model():
    try:
        # Check if files exist
        model_files = ['customer_classification_model_lr.pkl', 'tfidf_vectorizer.pkl', 'label_encoder.pkl']
        
        for file in model_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} is missing")
                return False
        
        # Try to load models
        print("Loading models...")
        model = joblib.load('customer_classification_model_lr.pkl')
        tfidf_vect = joblib.load('tfidf_vectorizer.pkl')
        encoder = joblib.load('label_encoder.pkl')
        
        print("✓ All models loaded successfully!")
        
        # Test prediction
        test_complaint = "I have issues with my billing statement"
        X_input = tfidf_vect.transform([test_complaint])
        prediction = model.predict(X_input)
        predicted_label = encoder.inverse_transform(prediction)[0]
        
        print(f"✓ Test prediction successful: {predicted_label}")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_model()