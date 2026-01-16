# Occupancy Detection System

## Overview

This project implements a multi-sensor occupancy detection system that combines mmWave radar and camera data to accurately count the number of people in a room. The system consists of three main modules that work together to collect, process, and analyze data for real-time occupancy monitoring.

The system architecture:
1. **Radar Module**: Captures range-Doppler data from mmWave radar sensor
2. **Camera Module**: Provides visual people counting using YOLO detection
3. **ML Module**: Preprocesses and fuses sensor data, trains classification models

## Project Structure

```
OccupancyDetectionProject/
├── Radar/                      #mmWave radar data acquisition
│   ├── esp32Radar.ino         #ESP32 firmware for radar sensor
│   ├── radarLogger.py         #Serial data logging script
│   ├── sendTime.py            #Time synchronization utility
│   ├── run.py                 #Automated setup and data capture
│   └── README.md              #Detailed radar module documentation
├── Camera/                     #Camera-based people detection
│   ├── GUI.py                 #Graphical interface for camera control
│   ├── pmain3.py              #YOLO detection and logging
│   ├── yolo12m.pt             #YOLOv12 model weights
│   └── README.md              #Detailed camera module documentation
├── ML/                         #Machine learning pipeline
│   ├── Preprocessing/         #Data processing scripts
│   │   ├── backgroundSubtraction.py
│   │   ├── featureExtraction.py
│   │   ├── synchronizeData.py
│   │   └── radarDataAverage.py
│   ├── XG_boost/              #XGBoost training and testing
│   │   ├── xgtrain.py
│   │   └── xgtest.py
│   └── README.md              #Detailed ML module documentation
└── README.md                   #This file
```

## Hardware Requirements

### Radar System
- **Microcontroller**: AZ-Delivery ESP32-WROOM-32
- **Radar Sensor**: HMMD mmWave Sensor
- **Cables**: USB to Micro-USB cable, Dupont cables
- **Optional**: Breadboard for easier mounting

### Camera System
- **Camera**: Axis network camera (with Axis API support)
- **Network Adapter**: PoE or standard network adapter
- **Cables**: Ethernet cables (×2)
- **Power**: Electrical outlet for adapter

## Software Requirements

- **Python 3.9+** (3.11.9 recommended)
- **Arduino IDE** (for ESP32 firmware upload)
- **AXIS Utilities** (for camera IP configuration)
- **arduino-cli** (optional, for automated firmware upload)

### Python Dependencies

Each module has its own `requirements.txt`. Key libraries include:
- `ultralytics` (YOLO detection)
- `opencv-python` (image processing)
- `pandas`, `numpy` (data manipulation)
- `xgboost`, `scikit-learn` (machine learning)
- `pyserial` (serial communication)
- `scipy` (signal processing)

## Installation

```bash
git clone <repository-url>
cd OccupancyDetectionProject
```

Each module requires its own setup (virtual environment, dependencies, and hardware configuration). **Complete installation and setup instructions are provided in each module's README:**

- **[Radar/README.md](Radar/README.md)** - Hardware connections, Arduino IDE setup, Python dependencies
- **[Camera/README.md](Camera/README.md)** - Camera connection, AXIS Utilities configuration, Python dependencies
- **[ML/README.md](ML/README.md)** - Python environment setup and dependencies

## System Workflow

### Phase 1: Data Collection

#### 1.1 Background Data Collection (Radar)
Collect baseline radar data from an empty room to establish background reference. Record for several minutes with no people in the room. This data will be used for background subtraction.

**Instructions**: See [Radar/README.md - Gathering background data](Radar/README.md#gathering-background-data)

#### 1.2 Synchronized Data Collection
Collect synchronized radar and camera data with known occupancy. Run both the radar logger and camera GUI simultaneously in separate terminals. Record multiple sessions with 0, 1, and 2 people in the room. Data is automatically timestamped for synchronization.

**Instructions**: 
- Radar: See [Radar/README.md - Running the Python Scripts](Radar/README.md#running-the-python-scripts)
- Camera: See [Camera/README.md - Starting the Application via GUI](Camera/README.md#starting-the-application-via-gui)

### Phase 2: Data Preprocessing

Process the collected data through the ML preprocessing pipeline. This involves four steps:

1. **Compute Background Reference** - Temporal average of background radar frames
2. **Background Subtraction** - Remove static background to isolate moving objects
3. **Feature Extraction** - Extract 25 statistical and spatial features from range-Doppler maps
4. **Data Synchronization** - Merge camera and radar data by matching timestamps (±150ms tolerance)

**Instructions**: See [ML/README.md - Preprocessing the Data](ML/README.md#preprocessing-the-data)

### Phase 3: Model Training and Testing

Train an XGBoost multi-class classifier on the synchronized dataset and evaluate performance on test data.

**Instructions**: See [ML/README.md - Training and Testing](ML/README.md#training-the-ml)

**Outputs**: 
- Trained model: `people_counter_xgb_class.pkl`
- Predictions: `test_predictions.csv`
- Metrics: accuracy, precision, recall, F1-score

## Data Flow

```
┌──────────────┐
│ mmWave Radar │ → Raw RD Maps → Background Subtraction
└──────────────┘                         ↓
                                 Feature Extraction
                                         ↓
┌──────────────┐                 Radar Features (320→25)
│   Camera     │ → YOLO Detection        ↓
└──────────────┘         ↓          Synchronization ← Timestamps
                  People Count           ↓
                         ↓          Merged Dataset
                         └───────────────┘
                                  ↓
                           XGBoost Training
                                  ↓
                         Classification Model
                                  ↓
                     Occupancy Prediction (0, 1, 2 people)
```

## Output Formats

### Radar Data
- **Location**: `Radar/data/`
- **Format**: CSV with columns `[timestamp, raw]`
- **Raw values**: 320 space-separated integers (20×16 range-Doppler map)

### Camera Data
- **Location**: `Camera/results/ID_YYYYMMDD_HHMMSS_nnnnnn/`
- **Formats**: Images (`.png`), Videos (`.mp4`), Text (`.txt`), CSV (`.csv`)
- **CSV columns**: `[timestamp, people_count]`

### Preprocessed Data
- **Location**: `ML/data/`
- **Stages**:
  - `avg_background30Dec.csv`: Background reference (20×16)
  - `subtractedTestWithCamera2Jan.csv`: Background-subtracted radar data
  - `features2Jan.csv`: Extracted features (25 features per frame)
  - `merged/merged_2Jan.csv`: Synchronized radar+camera data

### Model Predictions
- **Location**: `ML/XG_boost/`
- **File**: `test_predictions.csv`
- **Columns**: `[true_people, predicted_people]`

## Troubleshooting

For module-specific troubleshooting and common issues:

- **Radar Issues**: See [Radar/README.md - Troubleshooting](Radar/README.md#troubleshooting)
- **Camera Issues**: See [Camera/README.md - Notes](Camera/README.md#notes)
- **ML Issues**: See [ML/README.md - Notes](ML/README.md#notes)

## System Architecture

### Time Synchronization
Both sensors must be synchronized for accurate data fusion:
1. Computer time is sent to ESP32 via `sendTime.py`
2. ESP32 timestamps all radar frames
3. Camera system uses computer time for timestamps
4. ML preprocessing matches timestamps within 150ms tolerance

### Multi-Sensor Fusion
The system combines complementary sensor modalities:
- **Radar**: Motion detection, works in darkness, privacy-preserving
- **Camera**: Visual confirmation, accurate counting, provides ground truth
- **Combined**: More robust than either sensor alone

### Feature Engineering
Radar data is transformed from raw range-Doppler maps (320 values) to compact feature vectors (25 features):
- Reduces dimensionality by 92.8%
- Captures essential motion and spatial patterns
- Enables efficient machine learning

## Performance Considerations

- **Radar frame rate**: ~10-20 Hz (depends on configuration)
- **Camera frame rate**: Configurable (default ~10 FPS)
- **Synchronization tolerance**: ±150ms
- **Training time**: Minutes to hours (depends on dataset size)
- **Inference time**: Real-time capable (<100ms per frame)

## Future Improvements

- Real-time prediction pipeline combining all modules
- Support for more than 2 people detection
- Deep learning models (LSTM, CNN) for temporal patterns
- Web-based monitoring dashboard
- Multiple camera/radar sensor fusion
- Automated data collection and retraining

## References

- YOLOv12 for object detection
- XGBoost for classification
- ESP32 mmWave radar integration
- Axis camera API

## Module Documentation

For detailed information about each module, see:
- [Radar Module Documentation](Radar/README.md)
- [Camera Module Documentation](Camera/README.md)
- [ML Module Documentation](ML/README.md)
