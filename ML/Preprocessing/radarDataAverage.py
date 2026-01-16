import numpy as np
import pandas as pd

"""
Compute average background reference from static radar measurements.

This module processes radar data collected from an empty/static environment
and computes the temporal average across all frames. The resulting background
reference can be used for background subtraction to isolate moving objects.
This is a key preprocessing step for occupancy detection systems.

Written by: Kasper Schröder, Martins Egbe
"""

#File paths for input static background data and output average reference
input_csv = "data/2025-12-30 Background Extraction.csv"
output_csv = "data/avg_background30Dec.csv"

def compute_background_average(input_csv, output_csv):
    """
    Compute temporal average of radar frames to create background reference.
    
    Args:
        input_csv: Path to CSV file with radar data from static environment
        output_csv: Path to save the computed 20x16 background reference
    """
    #Load radar data from CSV file
    data = pd.read_csv(input_csv, sep=",")
    
    #Parse raw radar values from space-separated strings to integer lists
    values = data["raw"].apply(lambda x: [int(v) for v in str(x).split()]).tolist()
    
    #Filter out rows that don't have exactly 320 values
    num_bins = 20 * 16  #Total radar bins (20 doppler x 16 range)
    valid_values = [v for v in values if len(v) == num_bins]
    
    if not valid_values:
        raise ValueError("No valid frames with 320 values found")
    
    print(f"Using {len(valid_values)} valid frames out of {len(values)} total frames")
    #Convert to numpy array for efficient computation
    values = np.array(valid_values)
    
    num_frames = values.shape[0]
    
    rd_maps = values.reshape(num_frames, 20, 16)
    
    avg_background = np.mean(rd_maps, axis=0)  #Result is 20x16 matrix  #Result is 20x16 matrix
    
    #Save the averaged background as CSV (20 rows x 16 columns, no headers)
    pd.DataFrame(avg_background).to_csv(output_csv, header=False, index=False)
    print(f"Average background saved to {output_csv}")

if __name__ == "__main__":
    compute_background_average(input_csv, output_csv)
