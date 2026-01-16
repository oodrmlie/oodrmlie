# ML Module

## Overview
This module is responsible for preprocessing data, training and testing a machine learning classification model that predicts the number of people detected based on processed feature data.

The system uses an **XGBoost multi-class classifier** trained on CSV datasets and supports:

* Incremental training (continuing from an existing model)
* Evaluation on new datasets
* Automatic saving of predictions/metrics

## Software Requirements

* Python 3.x (3.9+ recommended)
* pandas
* numpy
* scikit-learn
* xgboost
* joblib

## Installation and Setup

### 1. Install Python

Download and install Python 3 from:
- https://www.python.org/downloads/

Make sure Python is added to your system PATH.

### 2. Create a Virtual Environment (Recommended)

#### Windows

```bash
cd Camera
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### macOS/Linux

```bash
cd Camera
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Deactivating the Environment

```bash
deactivate
```

## Preprocessing the Data

### Output

## Training the ML

The training script:
* Loads a CSV dataset
* Removes timestamp-related columns
* Filters allowed classes
* Trains an XGBoost classifier
* Saves the trained model
* Supports continued training if a model already exists

### Expected Paths

- Training dataset: Ready_datasets/dataset.csv
- Saved model: XG_boost/people_counter_xgb_class.pkl

### Allowed Classes

Only the following labels are used for training: [0, 1, 2]
These represent the number of people detected.

### Run Training

```bash
python xgtrain.py
```

### Training Output

After training, the following will be generated:

* A trained model file:
  XG_boost/people_counter_xgb_class.pkl
  
* Console logs:
  * Number of training samples
  * Whether training is new or incremental
  * Total number of trees in the model

If a model already exists, the script will:
* Load it
* Add more trees
* Continue training
* Overwrite the saved model

## Testing the Trained ML

The testing script:
* Loads the trained model
* Loads a new test dataset
* Applies the same feature filtering
* Makes predictions
* Computes accuracy and classification metrics
* Saves predictions to a CSV file

### Expected Paths

- Test dataset: Ready_datasets/dataset1.csv
- Trained model: XG_boost/people_counter_xgb_class.pkl
- Output predictions: XG_boost/test_predictions.csv

### Run Testing

```bash
python xgtest.py
```

### Testing Output

The following outputs are generated:

#### 1. CSV File

XG_boost/test_predictions.csv

With columns:

- true_people
- predicted_people

#### 2. Console Metrics

* Total number of test samples
* Accuracy score
* Classification report (precision, recall, F1-score)
* Example predictions (last 20 rows)

## Notes

* Timestamp columns are automatically removed:
  * `timestamp_camera`
  * `timestamp_radar`
  * `time_diff_ms`

* The label column must be named: people_count
* Only classes `[0, 1, 2]` are used.
* If the trained model file is missing, testing will fail.
* Make sure preprocessing outputs match the expected format.