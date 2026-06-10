import numpy as np
import pandas as pd

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
                        ●	Abdulkadir Adde		
                        ●	Amer Shikh-Alzor 	
                        ●	Artem Blinkov 		
                        ●	Kasper Schröder 	
                        ●	Martin Frick 		
                        ●	Martins Egbe 		
                        ●	Rana Noorzadeh 	
                        ●	Saman Jejo 	


___________________________________________________________________________


This module removes static background reflections from radar measurements
by subtracting a pre-computed background reference. The process isolates
moving objects and dynamic changes in the environment, which is essential
for accurate occupancy detection and motion tracking.

Originally Written by: Kasper Schröder, Martins Egbe
Updated by: Martin Frick
Updated Date      : 2026-05-21
___________________________________________________________________________

"""
    
"""
# Variablelist 
  
    Lists for:
parsed_rows              | Storing parsed data
timestamps               | Storing timestamps (corresponding to parsed data rows)
values                   | Storing converted and parsed data to numpy array in order to effectivize processing
rd_maps                  | Storing flat data into a 3 dimentional array: +-- [frame]
-                                                                            |
-                                                                            +-- [range_bin]
-                                                                                |
-                                                                                +-- [doppler_bin]

    Strings containing file paths for:
test_csv                 | Input test data
background_csv           | Background reference / Reference Frame(s)
output_csv               | Output location & filename

    Intergers for:
num_frames               | Number of frames within a shape
num_bins                 |

level                    | Percent of Reference Frame to remove from raw radar measurements.
-                        | Initialized with 100.
-                        | ______________________________________________________________________
-                        | Range: 0% - 100% 
-                        | ----------------------------------------------------------------------
-                        |        0%   =
-                        | Reference Frame value is not subtracted from raw radar measurement.
-                        | This means the full scope of a radars reading is stored in output csv file
-                        |  - including any and all background noise and static. 
-                        | ----------------------------------------------------------------------
-                        |             100% = 
-                        | Entire Reference Frame value is subtracted from raw radar measurement.
-                        | This removes most of background noise and static.
-                        | ______________________________________________________________________


    NumPy arrays ("np.ndarrays") for:
background               | Static background reference (20x16)
subtracted               | Result after background removal
subtracted_flat          | Flattened back to 2D for output

    Pandas arrays ("pd.DataFrames") for:
test_data                | Raw input loaded from test CSV
output_df                | Final output with timestamps and processed radar data
"""

test_csv = "data/2026-01-02 Dataset.csv"                # Sets a default value for single script runs, or testing. Is overwritten when fulle preprocessing pipeline is run.
background_csv = "data/avg_background30Dec.csv"         # Sets a default value for single script runs, or testing. Is overwritten when fulle preprocessing pipeline is run.
output_csv = "data/subtractedTestWithCamera2Jan.csv"    # Sets a default value for single script runs, or testing. Is overwritten when fulle preprocessing pipeline is run.

#--------------------------------------------
# CLI INPUT
#--------------------------------------------

#
# "prompt_level"
# _______________________
# Asks user via CLI for background subtraction level in percent (%) .
# Loops until valid integer between 0 and 100 is provided by user.
#
def prompt_level():
    while True:
        raw = input("Enter background subtraction level (0-100%): ")
        try:
            value = int(raw)
        except ValueError:
            print(f"  -> '{raw}' is not a valid integer. Try again.")
            continue
        if 0 <= value <= 100:
            return value
        print(f"  -> {value} is out of range. Must be between 0 and 100.")


#--------------------------------------------
# STEP SEQUENCE
#--------------------------------------------

#
# "load_data"
# _______________________
# Step 1 - Load test dataset from CSV, parse each row into 320 int:s,
# validates the dimensions and proceeds to return values as an (NumPy) np.ndarray + timestamps list.
#
def load_data(test_csv):
    test_data = pd.read_csv(test_csv, sep=",")
    
    # Local variables. Only valid rows make it into returned arrays.
    parsed_rows = []
    timestamps = []
    
    for idx, (ts, line) in enumerate(zip(test_data["timestamp"], test_data["raw"])):
        tokens = str(line).split()
        if len(tokens) == 320:
            parsed_rows.append([int(v) for v in tokens])
            timestamps.append(ts)
        else:
            print(f"Skipping row {idx}: expected 320 values, got {len(tokens)}")
    
    values = np.array(parsed_rows)
    
    num_bins = 20 * 16

    # Validation belongs with the step that produces the actual data.
    if values.shape[1] != num_bins:
        raise ValueError(f"Expected {num_bins} values per frame, got {values.shape[1]}")
    
    return values, timestamps


#
# "load_background"
# _______________________
# Step 2 - Loads the background (Which is the "Reference Frame") from .csv-file and validate its shape (Must be 20x16).
# This ensures the array dimensions align exactly with the radar measurement format, enabling future background subtraction -
# of the Reference Frame value.
def load_background(background_csv):
    referenceFrame = pd.read_csv(background_csv, header=None).values
    
    if referenceFrame.shape != (20, 16):
        raise ValueError("Background CSV must be 20x16.")
    
    return referenceFrame


#
# "reshape_data"
# _______________________
# Step 3 - Reshape flat two-dimensional value arrays into a two-dimensional range-doppler maps according to following structure:
# (frames -> range_bins -> doppler_bins).
# 
def reshape_data(values):
    num_frames = values.shape[0]
    rd_maps = values.reshape(num_frames, 20, 16)
    return rd_maps


#
# "backgroundSubtraction"
# _______________________
# Step 4 - Subtract the scaled Reference Frame from each frame of new radar readings.
# Scaling is done by dividing user selected background subtraction amount ("level" in code below) by 100
# (100 = Represents max amount of percent(%)), and the multiplying this amount with the currently relevant
# part of the Reference Frame ("referenceFrame" in code below). 
#
# A user input of "0" (level=0) results in the radar measurement data being unaltered.
# Correspondingly, a user input of "100" (level=0) subtracts the full value of the Reference Frame.
#
# "rd_maps" represents the incoming radar measurement values which will have the background subtraction 
# applied on them. 
# By using the "NumPy" array datastructure and arranging the two array dimensions 
# to align exactly with eachother,the background subtraction operation is able to be applied over
# the entire array.
# 
def backgroundSubtraction(rd_maps, referenceFrame, level):
    subtracted = rd_maps - (level / 100) * referenceFrame
    return subtracted


#
# "format_output"
# _______________________
# Step 5 - Clips negative values to zero and flattens back to 2D (frames x 320).
# Builds the output DataFrame, pairing each row with its corresponding timestamp.
#
def format_output(subtracted, timestamps):
    subtracted = np.clip(subtracted, a_min=0, a_max=None)
    
    num_frames = subtracted.shape[0]
    subtracted_flat = subtracted.reshape(num_frames, -1)
    
    output_df = pd.DataFrame({
        "timestamp": timestamps,
        "raw": [" ".join(map(str, row)) for row in subtracted_flat]
    })
    
    return output_df


#
# "save_output"
# _______________________
# Step 6 - Write output DataFrame to CSV.
# Used for individual script runs or testing.
def save_output(output_df, output_csv):
    output_df.to_csv(output_csv, index=False)
    print(f"Background-subtracted data saved to {output_csv}")
    print(f"Frames processed: {len(output_df)}")

#
# "run"
# _______________________
# Calls each operating in sequence. Each step's output feeds the next one.
#
def subtract_background(test_csv, background_csv, output_csv):
    level = prompt_level()

    values, timestamps = load_data(test_csv)

    referenceFrame     = load_background(background_csv)

    rd_maps            = reshape_data(values)

    subtracted         = backgroundSubtraction(rd_maps, referenceFrame, level)

    output_df          = format_output(subtracted, timestamps)

    output_df.to_csv(output_csv, index=False)
    print(f"Background-subtracted data saved to {output_csv}")
    print(f"Frames processed: {len(output_df)}")

    #save_output(output_df, output_csv) # Used for individual script runs or testing.


if __name__ == "__main__":
    subtract_background(test_csv, background_csv, output_csv)