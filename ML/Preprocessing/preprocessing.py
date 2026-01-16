import sys
import os
#Import functions from other modules
from backgroundSubtraction import subtract_background
from featureExtraction import process_csv as extract_features
from synchronizeData import synchronize_and_merge

"""
Preprocessing pipeline for radar data processing.

This script orchestrates the complete preprocessing workflow by calling:
1. backgroundSubtraction.py - Remove background noise from raw radar data
2. featureExtraction.py - Extract features from background-subtracted data
3. synchronizeData.py - Merge radar features with camera data by timestamp

Simply update the FILE CONFIGURATION section with your input/output file names.

Written by: Kasper Schröder
"""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

#Folder paths (hardcoded)
RADAR_DATA_FOLDER = "../../Radar/data"
CAMERA_RESULTS_FOLDER = "../../Camera/results"

#CSV file names

#Raw radar data
RAW_RADAR_FILENAME = "2026-01-02 Dataset"
#Background data from radar for subtraction
RADAR_BACKGROUND_DATA = "avg_background30Dec"
#Output background-subtracted radar data
RADAR_BACKGROUND_SUBTRACTED_FILENAME = "subtractedTestWithCamera2Jan"
#Output features file from feature extraction
FEATURES_FILENAME = "features2Jan"
#Camera data folder and file
CAMERA_FOLDER_NAME = "ID_20260102_113918_734813"
#Output merged file
MERGED_FILENAME = "merged_2Jan"

#Construct full paths
RAW_RADAR_FILE = f"{RADAR_DATA_FOLDER}/{RAW_RADAR_FILENAME}.csv"
BACKGROUND_FILE = f"{RADAR_DATA_FOLDER}/{RADAR_BACKGROUND_DATA}.csv"
CAMERA_CSV_PATH = f"{CAMERA_RESULTS_FOLDER}/{CAMERA_FOLDER_NAME}/{CAMERA_FOLDER_NAME}.csv"
BACKGROUND_SUBTRACTED_FILE = f"{RADAR_DATA_FOLDER}/{RADAR_BACKGROUND_SUBTRACTED_FILENAME}.csv"
FEATURES_FILE = f"{RADAR_DATA_FOLDER}/{FEATURES_FILENAME}.csv"
MERGED_OUTPUT_FILE = f"../data/merged/{MERGED_FILENAME}.csv"

MAX_TIME_DIFF_MS = 150 #Maximum time difference (ms) for matching radar and camera frames

def run_preprocessing_pipeline():
    """
    Execute the complete preprocessing pipeline.

    The pipeline consists of three sequential steps:
    1. Background Subtraction - Remove background noise from raw radar data
    2. Feature Extraction - Extract features from background-subtracted data
    3. Data Synchronization - Merge radar features with camera data by timestamp

    Args:
        None

    Returns:
        None

    Raises:
        FileNotFoundError: If input files do not exist.
        Exception: If any processing step fails.
    """
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "RADAR DATA PREPROCESSING PIPELINE" + " "*19 + "║")
    print("╚" + "="*68 + "╝")

    try:
        #Step 1: Background Subtraction
        print("\n" + "="*70)
        print("STEP 1: BACKGROUND SUBTRACTION")
        print("="*70)
        subtract_background(RAW_RADAR_FILE, BACKGROUND_FILE, BACKGROUND_SUBTRACTED_FILE)
        print(f"Background subtraction completed")
        
        #Step 2: Feature Extraction
        print("\n" + "="*70)
        print("STEP 2: FEATURE EXTRACTION")
        print("="*70)
        extract_features(BACKGROUND_SUBTRACTED_FILE, FEATURES_FILE)
        print(f"Feature extraction completed")
        
        #Step 3: Data Synchronization
        print("\n" + "="*70)
        print("STEP 3: DATA SYNCHRONIZATION")
        print("="*70)
        synchronize_and_merge(CAMERA_CSV_PATH, FEATURES_FILE, MERGED_OUTPUT_FILE, MAX_TIME_DIFF_MS)
        print(f"Data synchronization completed")
        
        #Final summary
        print("\n" + "="*70)
        print("PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY")
        print("="*70)
        print(f"\nFinal output: {MERGED_OUTPUT_FILE}\n")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        raise

if __name__ == "__main__":
    run_preprocessing_pipeline()