import numpy as np
import pandas as pd

"""
Perform background subtraction on radar range-Doppler maps.

This module removes static background reflections from radar measurements
by subtracting a pre-computed background reference. The process isolates
moving objects and dynamic changes in the environment, which is essential
for accurate occupancy detection and motion tracking.

Written by: Kasper Schröder, Martins Egbe
"""

#File paths for input test data, background reference, and output
test_csv = "data/2026-01-02 Dataset.csv"
background_csv = "data/avg_background30Dec.csv"
output_csv = "data/subtractedTestWithCamera2Jan.csv"

def subtract_background(test_csv, background_csv, output_csv):
    #Load the test dataset containing radar measurements
    test_data = pd.read_csv(test_csv, sep=",")
    
    #Initialize lists to store parsed data and corresponding timestamps
    parsed_rows = []
    timestamps = []
    #Parse each row from the test data and validate it has 320 values (20x16 radar grid)
    for idx, (ts, line) in enumerate(zip(test_data["timestamp"], test_data["raw"])):
        tokens = str(line).split()
        if len(tokens) == 320:
            parsed_rows.append([int(v) for v in tokens])
            timestamps.append(ts)
        else:
            print(f"Skipping row {idx}: expected 320 values, got {len(tokens)}")
    
    #Convert parsed data to numpy array for efficient processing
    values = np.array(parsed_rows)
    num_frames = values.shape[0]
    num_bins = 20 * 16
    
    #Validate data dimensions
    if values.shape[1] != num_bins:
        raise ValueError(f"Expected 320 values per frame, got {values.shape[1]}")
    
    #Reshape flat data into 3D array: (frames, range_bins, doppler_bins)
    rd_maps = values.reshape(num_frames, 20, 16)
    
    #Load the background reference (average of static environment measurements)
    background = pd.read_csv(background_csv, header=None).values
    if background.shape != (20, 16):
        raise ValueError("Background CSV must be 20x16.")
    
    #Subtract background from each frame to isolate moving objects
    subtracted = rd_maps - background    
    #Clip negative values to zero (only keep positive differences)
    subtracted = np.clip(subtracted, a_min=0, a_max=None)
    #Flatten back to 2D array for saving (frames x 320 values)
    subtracted_flat = subtracted.reshape(num_frames, -1)
    
    #Create output dataframe with timestamps and background-subtracted data
    output_df = pd.DataFrame({
        "timestamp": timestamps,
        "raw": [" ".join(map(str, row)) for row in subtracted_flat]
    })
    
    #Save processed data to CSV file
    output_df.to_csv(output_csv, index=False)
    print(f"Background-subtracted data saved to {output_csv}")
    print(f"Frames processed: {num_frames}")

if __name__ == "__main__":
    subtract_background(test_csv, background_csv, output_csv)