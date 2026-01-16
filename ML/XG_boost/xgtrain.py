import pandas as pd
from xgboost import XGBClassifier
import joblib
import os

# this class is used for training the ML with classification

MODEL_PATH = "../XG_boost/people_counter_xgb_class.pkl"
TRAIN_DATA_PATH = "../Ready_datasets/dataset1.csv"
ALLOWED_CLASSES = [0, 1, 2]

def load_train_data():
    df = pd.read_csv(TRAIN_DATA_PATH)

    # drop timestamp columns
    for col in ["timestamp_camera", "timestamp_radar", "time_diff_ms"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    # only keep allowed classes
    df = df[df['people_count'].isin(ALLOWED_CLASSES)]

    # remove people_count from list of features
    X = df.drop(columns=["people_count"])

    # add people_count as label/result
    y = df["people_count"]

    return X, y

def train_and_save_model():
    print("1. loading training data...")
    X_train, y_train = load_train_data()

    additional_trees = 100

    if os.path.exists(MODEL_PATH):
        print("2. loading existing model and continuing training...")
        model = joblib.load(MODEL_PATH)

        model.set_params(
            n_estimators=model.n_estimators + additional_trees
        )

        model.fit(
            X_train,
            y_train,
            xgb_model=model.get_booster()
        )

    else:
        print("2. training new model...")
        model = XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softmax",
            num_class=3,
            random_state=42
        )

        model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    print(f"model saved to: {MODEL_PATH}")
    print(f"total trees in model: {model.n_estimators}")

    return model

if __name__ == "__main__":
    train_and_save_model()
