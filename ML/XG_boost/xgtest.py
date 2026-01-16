import os
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, classification_report

# this class is used for testing the trained ML with a new dataset

MODEL_PATH = "../XG_boost/people_counter_xgb_class.pkl"
TEST_DATA_PATH = "../Ready_datasets/dataset4.csv"
ALLOWED_CLASSES = [0, 1, 2]

def load_test_data():
    df = pd.read_csv(TEST_DATA_PATH)

    # drop timestamp columns
    for col in ["timestamp_camera", "timestamp_radar", "time_diff_ms"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    # only keep allowed classes
    df = df[df['people_count'].isin(ALLOWED_CLASSES)]

    # remove people_count from list of features
    X_test = df.drop(columns=["people_count"])

    # add people_count as label/result
    y_test = df["people_count"]

    return X_test, y_test

# load the model we trained in xgtrain.py
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"model not found at {MODEL_PATH}")
    
    print(f"loading model from {MODEL_PATH}...")
    model = joblib.load(MODEL_PATH)
    print("model loaded successfully.")

    return model

def predict_people(model, X_test):
    return model.predict(X_test)

if __name__ == "__main__":
    model = load_model()
    X_test, y_test = load_test_data()

    print(f"test samples: {len(X_test)}")

    # predicting
    preds = predict_people(model, X_test)

    # evaluate the predictions
    acc = accuracy_score(y_test, preds)

    # save all predictions to CSV
    results = pd.DataFrame({
        "true_people": y_test.values,
        "predicted_people": preds
    })
    results.to_csv("../XG_boost/test_predictions.csv", index=False)

    # print latest 20 predictions
    print("\nexample of predictions:")
    print(results.tail(20))

    # print statistics
    print(f"test accuracy: {acc:.3f}")
    print("\nclassification report:\n", classification_report(y_test, preds))

    print("predictions have been saved to test_predictions.csv")


    