# Occupancy Detection System (Parameterized Preprocessing & Evaluation Version)

## Overview
This repository implements a multi-sensor occupancy detection system that combines mmWave radar and camera data to count the number of people in a room. 

This specific repository is an **extended and restructured version** of the original bachelor project https://github.com/KappeS101/OccupancyDetectionProject.git. While the initial system utilized a fixed, 100% background subtraction preprocessing mechanism, this version introduces a **Parameterized Preprocessing Artifact** (`backgroundSubtraction.py`) in ML/Preprocessing, that exposes the subtraction strength as a user-controlled parameter (0% to 100%), alongside an **Automated Evaluation Script** (`xgtest2.py`) in ML/XG_boost, designed to test model robustness and extract absolute multi-class classification metrics across varying environmental noise levels.

The system architecture consists of three main modules:
1. **Radar Module**: Captures range-Doppler data from an mmWave radar sensor.
2. **Camera Module**: Provides visual people counting using YOLO detection to serve as the ground truth.
3. **ML Module (Extended)**: Preprocesses and fuses sensor data with variable subtraction levels, extracts spatial features, and automates multi-class classification testing.

## Project Structure
```
OccupancyDetectionProject/
├── Radar/                      # mmWave radar data acquisition (Reused)
│   ├── esp32Radar.ino          # ESP32 firmware for radar sensor
│   ├── radarLogger.py          # Serial data logging script
│   ├── sendTime.py            # Time synchronization utility
│   └── run.py                 # Automated setup and data capture
├── Camera/                     # Camera-based people detection (Reused)
│   ├── GUI.py                  # Graphical interface for camera control
│   ├── pmain3.py               # YOLO detection and logging
│   └── yolo12m.pt              # YOLOv12 model weights
├── ML/                         # Extended Machine Learning Pipeline
│   ├── Preprocessing/          # Developed Data Processing Artifact
│   │   ├── backgroundSubtraction.py # Restructured script (0-100% variable level)
│   │   ├── featureExtraction.py     # Condenses radar maps into 24 features
│   │   ├── synchronizeData.py       # Matches features with camera ground truth
│   │   └── radarDataAverage.py      # Computes the baseline Reference Frame
│   └── Evaluation_Tool/        # Developed Automated Evaluation Instrument
│       ├── evaluation_script.py # Standardized testing loop across all datasets
│       ├── people_counter_xgb_0.pkl   # Pre-trained model (0% subtraction)
│       ├── people_counter_xgb_25.pkl  # Pre-trained model (25% subtraction)
│       ├── people_counter_xgb_50.pkl  # Pre-trained model (50% subtraction)
│       ├── people_counter_xgb_75.pkl  # Pre-trained model (75% subtraction)
│       └── people_counter_xgb_100.pkl # Pre-trained model (100% subtraction)
└── README.md                   # This file
```

## Hardware Requirements

### Radar System
- **Microcontroller**: AZ-Delivery ESP32-WROOM-32
- **Radar Sensor**: HMMD mmWave Sensor
- **Cables**: USB to Micro-USB cable, Dupont cables

### Camera System
- **Camera**: Axis network camera (with Axis API support)
- **Network Adapter**: PoE or standard network adapter
- **Cables**: Ethernet cables (×2)

## Software Requirements

- **Python 3.9+** (3.11.9 recommended)
- **Arduino IDE** (for ESP32 firmware upload)
- **AXIS Utilities** (for camera IP configuration)

### Python Dependencies
Install the required tracking, machine learning, and visualization libraries via pip:
```bash
pip install pandas numpy xgboost scikit-learn matplotlib seaborn joblib ultralytics opencv-python pyserial scipy
