import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, confusion_matrix

"""
This Python script was made as part of Martin Frick and Kasper Schröder's Bachelor Thesis.
The work on the bachelor thesis took place in 2026 from Febuary up until June at the
Faculty of Technology and Society in Malmö University, Sweden ( https://mau.se/ )

This python script is based work done in:
          Course:  " Degree Project: Information Architect and Computer Systems Developer "
         Project:  " Occupancy Detection Using Radar Sensors and Machine Learning in Indoor Environments "
            From:  September 2025
           Until:  Febuary   2026
        Location:  Malmö University, Sweden ( https://mau.se/ )
         Faculty:  Faculty of technology and society
 Project Members:  (In alphabetical order)
                        ●   Abdulkadir Adde     
                        ●   Amer Shikh-Alzor    
                        ●   Artem Blinkov       
                        ●   Kasper Schröder     
                        ●   Martin Frick        
                        ●   Martins Egbe        
                        ●   Rana Noorzadeh  
                        ●   Saman Jejo  


___________________________________________________________________________


This module evaluates the performance of multiple trained XGBoost models 
across different background subtraction levels (0%, 25%, 50%, 75%, 100%).
It calculates total accuracy, performs a sensitivity analysis, extracts 
detailed confusion matrix metrics (TP, FP, FN, TN) per occupancy class, 
and exports both a text report and visual heatmap figures.

Originally Written by: Rana Noorzadeh
Updated by: Kasper Schröder
Updated Date      : 2026-06-04
___________________________________________________________________________

"""

"""
# Variablelist 

    Strings & Config Lists:
BASE_DIR                 | Absolute path to the directory containing this script
ALLOWED_CLASSES          | List of valid target labels/occupancy classes [0, 1, 2]
TEST_CONFIGS             | List of dictionaries mapping subtraction levels to model and dataset filepaths
text_log_path            | Output filepath for the final summary evaluation report text file
imageName                | Output filepath for the generated Confusion Matrix PNG heatmap

    Scikit-learn / Evaluation Variables:
model                    | The loaded pre-trained XGBoost classification model object
df                       | Pandas DataFrame containing the raw imported test dataset
X_test                   | Feature matrix extracted from data (radar bins / measurements)
y_test                   | Target vector containing true ground truth occupant labels
preds                    | Model predictions generated from X_test
acc                      | Total classification accuracy score (0.0 - 1.0)
cm                       | Standard multi-class confusion matrix array

    Sensitivity Analysis Variables:
total_frames             | Total number of instances/rows in the evaluation test set
single_error_percent     | Statistical impact of a single incorrect prediction in percent (%)
two_errors_percent       | Statistical impact of two incorrect predictions in percent (%)
camera_error_frames      | The number of frames corresponding to the camera's baseline 2% error margin

    Binary Metrics (Per Class Evaluation):
TP                       | True Positives: Correctly predicted instances for the class
FP                       | False Positives: Instances incorrectly predicted as the class
FN                       | False Negatives: Instances belonging to the class but predicted otherwise
TN                       | True Negatives: Instances correctly identified as not belonging to the class
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_CLASSES = [0, 1, 2]

TEST_CONFIGS = [
    {
        "level": "0",
        "model": os.path.join(BASE_DIR, "people_counter_xgb_class_0.pkl"),
        "data": os.path.join(BASE_DIR, "..", "Ready_datasets", "Test_0per_T1851.csv")
    },
    {
        "level": "25",
        "model": os.path.join(BASE_DIR, "people_counter_xgb_class_25.pkl"),
        "data": os.path.join(BASE_DIR, "..", "Ready_datasets", "Test_25per_T1900.csv")
    },
    {
        "level": "50",
        "model": os.path.join(BASE_DIR, "people_counter_xgb_class_50.pkl"),
        "data": os.path.join(BASE_DIR, "..", "Ready_datasets", "Test_50per_T1728.csv")
    },
    {
        "level": "75",
        "model": os.path.join(BASE_DIR, "people_counter_xgb_class_75.pkl"),
        "data": os.path.join(BASE_DIR, "..", "Ready_datasets", "Test_75per_T1907.csv")
    },
    {
        "level": "100",
        "model": os.path.join(BASE_DIR, "people_counter_xgb_class_100.pkl"),
        "data": os.path.join(BASE_DIR, "..", "Ready_datasets", "Test_100per_T1923.csv")
    }
]

def run_evaluation():
    text_log_path = os.path.join(BASE_DIR, "Final_Results_Report.txt")
    
    #Step 1 - Initialize the evaluation log file and prepare tracking systems
    with open(text_log_path, "w", encoding="utf-8") as log_file:
        
        #Dual-output logging helper
        def log_print(text=""):
            print(text)
            log_file.write(text + "\n")

        log_print("STARTING EVALUATION OF ALL DATASETS\n")

        #Step 2 - Loop through each subtraction configuration profile
        for config in TEST_CONFIGS:
            level = config["level"]
            model_path = config["model"]
            data_path = config["data"]
            
            log_print("="*60)
            log_print(f"EVALUATING LEVEL: {level} percent subtraction")
            log_print("="*60)
            
            #Step 2.1 - Load the pre-trained classification model using joblib
            log_print(f"Loading model from {model_path}...")
            model = joblib.load(model_path)
            
            #Step 2.2 - Load target dataset into a Pandas DataFrame
            log_print(f"Loading data from {data_path}...")
            df = pd.read_csv(data_path)
            
            #Step 2.3 - Preprocess data by dropping non-feature timestamp and metadata columns
            for col in ["timestamp_camera", "timestamp_radar", "time_diff_ms"]:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    
            #Step 2.4 - Filter rows to only keep valid occupancy classes (0, 1, 2)
            df = df[df['people_count'].isin(ALLOWED_CLASSES)]
            X_test = df.drop(columns=["people_count"])
            y_test = df["people_count"]
            
            #Step 2.5 - Execute ML predictions and compute core matrix metrics
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            cm = confusion_matrix(y_test, preds, labels=ALLOWED_CLASSES)
            
            log_print(f"Total Accuracy: {acc:.4f}")
            
            #Step 3 - Perform Sensitivity Analysis relative to camera reference limitations
            total_frames = len(y_test)
            single_error_percent = (1 / total_frames) * 100
            two_errors_percent = (2 / total_frames) * 100
            camera_error_frames = int(total_frames * 0.02)
            
            log_print(f"\nSENSITIVITY ANALYSIS (Based on {total_frames} frames in the test set):")
            log_print(f"A single error changes the result by exactly {single_error_percent:.4f} percent.")
            log_print(f"2 errors change the result by exactly {two_errors_percent:.4f} percent.")
            log_print(f"The camera's built-in margin of error (2 percent) corresponds to a total of {camera_error_frames} incorrect frames!")
            
            #Step 4 - Calculate and extract binary classification metrics (One-vs-All) per class
            log_print("\nEXACT NUMBERS PER CLASS:")
            for i, class_label in enumerate(ALLOWED_CLASSES):
                TP = cm[i, i]
                FP = cm[:, i].sum() - TP
                FN = cm[i, :].sum() - TP
                TN = cm.sum() - (TP + FP + FN)
                
                log_print(f"\n--- Class {class_label} ({class_label} people in the room) ---")
                log_print(f"True Positives  (TP) : {TP}")
                log_print(f"False Positives (FP) : {FP}")
                log_print(f"False Negatives (FN) : {FN}")
                log_print(f"True Negatives  (TN) : {TN}")
                log_print(f"Checksum             : {TP + FP + FN + TN}")
            
            log_print("\n")

            #Step 5 - Generate and save a visual Confusion Matrix heatmap using Seaborn
            plt.figure(figsize=(8, 6))

            sns.heatmap(cm, 
                        annot=True, 
                        fmt='g', 
                        cmap='Blues',
                        xticklabels=['0 occupants', '1 occupant', '2 occupants'],
                        yticklabels=['0 occupants', '1 occupant', '2 occupants'])

            plt.title(f'Confusion Matrix {level}% Subtraction')
            plt.ylabel('True Label (Ground Truth)')
            plt.xlabel('Predicted Label')

            imageName = os.path.join(BASE_DIR, f"Confusion_Matrix_{level}_percent.png")
            plt.savefig(imageName)
            plt.close()
            
            log_print(f"Saved the heatmap as an image file: {imageName}\n")

    print(f"\nAll numbers and results have been saved to the file: {text_log_path}")

if __name__ == "__main__":
    run_evaluation()