import pandas as pd
from xgboost import XGBClassifier
import joblib
import os

"""
XGBoost Model Training for Occupancy Classification.

This script trains or continues training an XGBoost classifier to predict
the number of people in a room based on fused radar and camera features.
It supports both new model creation and incremental training (continuing from
an existing model by adding more decision trees).

Written by: Rana Noorzadeh
"""

#File paths and training configuration
MODEL_PATH = "../XG_boost/people_counter_xgb_class.pkl"  #Path to save/load trained model
TRAIN_DATA_PATH = "../Ready_datasets/dataset1.csv"       #Path to training dataset
ALLOWED_CLASSES = [0, 1, 2]                             #Valid occupancy classes: 0, 1, or 2 people

def load_train_data():
    """
    Load and preprocess training dataset.
    
    This function:
    1. Loads the training CSV file
    2. Removes timestamp and synchronization columns
    3. Filters to only allowed occupancy classes [0, 1, 2]
    4. Separates features (X) from labels (y)
    
    Returns:
        Tuple of (X_train, y_train) where X_train is features and y_train is people_count labels
    """
    df = pd.read_csv(TRAIN_DATA_PATH)

    #Remove timestamp and metadata columns that shouldn't be used for training
    for col in ["timestamp_camera", "timestamp_radar", "time_diff_ms"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    #Filter to only allowed occupancy classes to ensure valid training data
    df = df[df['people_count'].isin(ALLOWED_CLASSES)]

    #Separate features (X) from target label (y)
    X = df.drop(columns=["people_count"])  #All columns except target
    y = df["people_count"]                  #Target: number of people

    return X, y

def train_and_save_model():
    """
    Train or continue training an XGBoost classifier.
    
    This function implements two workflows:
    1. NEW MODEL: Creates and trains a new XGBoost classifier from scratch
    2. INCREMENTAL: Loads existing model and adds more decision trees (boosts)
    
    The incremental approach allows for continuous model improvement as new data
    becomes available without retraining from scratch.
    
    Returns:
        Trained XGBoost classifier object
    """
    print("1. loading training data...")
    X_train, y_train = load_train_data()

    #Number of additional trees to add during incremental training
    additional_trees = 100

    if os.path.exists(MODEL_PATH):
        #INCREMENTAL TRAINING: Load existing model and add more trees (boosting)
        print("2. loading existing model and continuing training...")
        model = joblib.load(MODEL_PATH)

        #Increase n_estimators to add more trees
        model.set_params(
            n_estimators=model.n_estimators + additional_trees
        )

        #Train with existing booster to preserve learned patterns
        model.fit(
            X_train,
            y_train,
            xgb_model=model.get_booster()
        )

    else:
        #NEW MODEL: Create and train XGBoost classifier from scratch
        print("2. training new model...")
        model = XGBClassifier(
            n_estimators=300,                #Number of decision trees
            learning_rate=0.05,              #Shrinkage factor for each booster (0-1)
            max_depth=6,                     #Maximum tree depth (prevents overfitting)
            subsample=0.8,                   #Fraction of samples used for each tree
            colsample_bytree=0.8,            #Fraction of features used for each tree
            objective="multi:softmax",       #Multi-class classification objective
            num_class=3,                     #Number of classes: 0, 1, 2 people
            random_state=42                  #Random seed for reproducibility
        )

        model.fit(X_train, y_train)  #Train on entire dataset

    #Save trained model to disk for later use in predictions
    joblib.dump(model, MODEL_PATH)
    print(f"model saved to: {MODEL_PATH}")
    print(f"total trees in model: {model.n_estimators}")

    return model

if __name__ == "__main__":
    train_and_save_model()  #Execute training workflow
