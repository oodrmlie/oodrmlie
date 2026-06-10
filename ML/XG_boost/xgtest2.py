import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, confusion_matrix

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
    text_log_path = os.path.join(BASE_DIR, "Slutgiltiga_Resultat_Rapport.txt")
    
    with open(text_log_path, "w", encoding="utf-8") as log_file:
        
        def log_print(text=""):
            print(text)
            log_file.write(text + "\n")

        log_print("STARTAR UTVÄRDERING AV ALLA DATASET\n")

        for config in TEST_CONFIGS:
            level = config["level"]
            model_path = config["model"]
            data_path = config["data"]
            
            log_print("="*60)
            log_print(f"UTVÄRDERAR NIVÅ: {level} procent subtraktion")
            log_print("="*60)
            
            log_print(f"Laddar modell från {model_path}...")
            model = joblib.load(model_path)
            
            log_print(f"Laddar data från {data_path}...")
            df = pd.read_csv(data_path)
            
            for col in ["timestamp_camera", "timestamp_radar", "time_diff_ms"]:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    
            df = df[df['people_count'].isin(ALLOWED_CLASSES)]
            X_test = df.drop(columns=["people_count"])
            y_test = df["people_count"]
            
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            cm = confusion_matrix(y_test, preds, labels=ALLOWED_CLASSES)
            
            log_print(f"Total Träffsäkerhet (Accuracy): {acc:.4f}")
            
            total_frames = len(y_test)
            en_fel_procent = (1 / total_frames) * 100
            tva_fel_procent = (2 / total_frames) * 100
            kamerans_fel_frames = int(total_frames * 0.02)
            
            log_print(f"\nKÄNSLIGHETSANALYS (Baserat på {total_frames} frames i testsetet):")
            log_print(f"1 enda fel förändrar resultatet med exakt {en_fel_procent:.4f} procent.")
            log_print(f"2 fel förändrar resultatet med exakt {tva_fel_procent:.4f} procent.")
            log_print(f"Kamerans inbyggda felmarginal (2 procent) motsvarar hela {kamerans_fel_frames} felaktiga frames!")
            
            log_print("\nEXAKTA SIFFROR PER KLASS:")
            for i, class_label in enumerate(ALLOWED_CLASSES):
                TP = cm[i, i]
                FP = cm[:, i].sum() - TP
                FN = cm[i, :].sum() - TP
                TN = cm.sum() - (TP + FP + FN)
                
                log_print(f"\n--- Klass {class_label} ({class_label} personer i rummet) ---")
                log_print(f"True Positives  (TP) : {TP}")
                log_print(f"False Positives (FP) : {FP}")
                log_print(f"False Negatives (FN) : {FN}")
                log_print(f"True Negatives  (TN) : {TN}")
                log_print(f"Kontrollsumma        : {TP + FP + FN + TN}")
            
            log_print("\n")

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

            bildnamn = os.path.join(BASE_DIR, f"Confusion_Matrix_{level}_percent.png")
            plt.savefig(bildnamn)
            plt.close()
            
            log_print(f"Sparade värmekartan som bildfil: {bildnamn}\n")

    print(f"\Alla siffror och resultat har sparats i filen: {text_log_path}")

if __name__ == "__main__":
    run_evaluation()