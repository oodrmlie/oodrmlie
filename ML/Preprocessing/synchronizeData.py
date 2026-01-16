import pandas as pd
import os

"""
Synchronize and merge camera and radar data based on timestamps.

This module aligns data from two asynchronous sensors (camera and radar)
by matching their timestamps within a specified tolerance window. The result
is a unified dataset where each camera observation is paired with the closest
radar measurement in time, enabling multi-sensor occupancy detection.

Written by: Saman Jejo, Abdulkadir Adde

Updated to work with radar module by: Kasper Schröder
"""

#File paths for camera detections, radar features, and merged output
camera_file = "ID_20260102_113918_734813"

camera_csv = f"results/{camera_file}/{camera_file}.csv"
radar_csv = "data/features2Jan.csv"
output_csv = "data/merged/merged_2Jan.csv"

def synchronize_and_merge(camera_csv, radar_csv, output_csv, max_diff_ms=150):
    """ 
    Merge camera and radar CSV files by matching timestamps
    The result is saved to output_csv

    Parameters:
    camera_csv (str): Path to the camera CSV file
    radar_csv (str): Path to the radar CSV file
    output_csv (str): Path to save the merged CSV file
    max_diff_ms (int): Maximum allowed time difference in milliseconds for matching entries

    Returns:
    None

    """
   
    #Read in the CSV files
    cam = pd.read_csv(camera_csv, names=["timestamp", "people_count"], skiprows=1)
    rad = pd.read_csv(radar_csv)
    feature_cols = [c for c in rad.columns if c != "timestamp"]

    #Convert timestamps to datetime
    cam["timestamp"] = pd.to_datetime(cam["timestamp"], format="%Y-%m-%d %H:%M:%S.%f")
    rad["timestamp"] = pd.to_datetime(rad["timestamp"], errors="coerce")

    #Create an empty list for the results
    merged_rows = []

    #Iterate through each camera frame and find the closest radar measurement in time
    for _, c_row in cam.iterrows():
        #Calculate time difference (in milliseconds) between this camera frame and all radar frames
        rad["diff"] = abs((rad["timestamp"] - c_row["timestamp"]).dt.total_seconds() * 1000)
        
        #Check if there are any valid differences (handle invalid radar timestamps)
        if rad["diff"].isna().all():
            radar_time = None
            radar_features = [None] * len(feature_cols)
            diff_ms = None
        else:
            nearest = rad.loc[rad["diff"].idxmin()]  #Find the radar row that is closest in time
            
            #If the nearest row is too far away (beyond tolerance), treat as no match
            if nearest["diff"] > max_diff_ms:
                radar_time = None
                radar_features = [None] * len(feature_cols)
                diff_ms = None
            else:
                radar_time = nearest["timestamp"]
                radar_features = [nearest[c] for c in feature_cols]
                diff_ms = nearest["diff"]


        #Construct merged row: camera data + radar data + time difference
        merged_rows.append(
            [c_row["timestamp"], c_row["people_count"], radar_time]
            + radar_features
            + [diff_ms]
        )

    #Create merged dataframe with combined camera and radar columns
    merged = pd.DataFrame(
        merged_rows,
        columns=["timestamp_camera", "people_count", "timestamp_radar"] + feature_cols + ["time_diff_ms"]
    )
    
    #Ensure output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    #Remove rows with missing radar timestamps (unpaired camera frames)
    initial_count = len(merged)
    merged = merged.dropna(subset=['timestamp_radar'])
    final_count = len(merged)
    removed_count = initial_count - final_count

    merged.to_csv(output_csv, index=False)

    print(f"Merged file saved to: {output_csv}")
    if removed_count > 0:
        print(f"Removed {removed_count} rows with missing radar timestamps")

if __name__ == "__main__":
    synchronize_and_merge(camera_csv, radar_csv, output_csv)