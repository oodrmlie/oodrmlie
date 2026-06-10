import os
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, classification_report

"""
XGBoost Model Testing and Evaluation.

This script loads a trained XGBoost classification model and evaluates it
on a test dataset. It computes accuracy, generates a detailed classification
report, and saves predictions to a CSV file for further analysis.

Written by: Rana Noorzadeh
"""

#File paths and configuration
MODEL_PATH = "../XG_boost/people_counter_xgb_class.pkl"  #Path to trained XGBoost model
TEST_DATA_PATH = "../Ready_datasets/dataset4.csv"        #Path to test dataset
ALLOWED_CLASSES = [0, 1, 2]                             #Valid occupancy classes: 0, 1, or 2 people

def load_test_data():
    """
    Load and preprocess test dataset.
    
    This function:
    1. Loads the test CSV file
    2. Removes timestamp and synchronization columns
    3. Filters to only allowed occupancy classes [0, 1, 2]
    4. Separates features (X) from labels (y)
    
    Returns:
        Tuple of (X_test, y_test) where X_test is features and y_test is people_count labels
    """
    df = pd.read_csv(TEST_DATA_PATH)

    #Remove timestamp and metadata columns that shouldn't be used for prediction
    for col in ["timestamp_camera", "timestamp_radar", "time_diff_ms"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    #Filter to only allowed occupancy classes to ensure valid training data
    df = df[df['people_count'].isin(ALLOWED_CLASSES)]

    #Separate features (X) from target label (y)
    X_test = df.drop(columns=["people_count"])  #All columns except target
    y_test = df["people_count"]                  #Target: number of people

    return X_test, y_test

def load_model():
    """
    Load the trained XGBoost classifier from disk.
    
    The model was previously trained and saved by xgtrain.py.
    
    Returns:
        Loaded XGBoost classifier object
        
    Raises:
        FileNotFoundError: If the model file doesn't exist at MODEL_PATH
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"model not found at {MODEL_PATH}")
    
    print(f"loading model from {MODEL_PATH}...")
    model = joblib.load(MODEL_PATH)  #Load pickled XGBoost model
    print("model loaded successfully.")

    return model

def predict_people(model, X_test):
    """
    Make occupancy predictions on test data.
    
    Args:
        model: Trained XGBoost classifier
        X_test: Feature matrix with test samples
        
    Returns:
        Array of predicted occupancy classes [0, 1, or 2]
    """
    return model.predict(X_test)

if __name__ == "__main__":
    #Load the trained model and test data
    model = load_model()
    X_test, y_test = load_test_data()

    print(f"test samples: {len(X_test)}")

    #Generate predictions on test set
    preds = predict_people(model, X_test)

    #Compute overall accuracy
    acc = accuracy_score(y_test, preds)

    #Create results dataframe and save to CSV for further analysis
    results = pd.DataFrame({
        "true_people": y_test.values,
        "predicted_people": preds
    })
    results.to_csv("../XG_boost/test_predictions.csv", index=False)

    #Display sample of predictions (last 20 rows)
    print("\nexample of predictions:")
    print(results)

    #Print evaluation metrics
    print(f"test accuracy: {acc:.3f}")
    print("\nclassification report:\n", classification_report(y_test, preds))

    print("predictions have been saved to test_predictions.csv")