# SMART PARKING SYSTEM - Thesis Project

## Purpose of the project
This project proposes a smart parking system that automates the process for detection of available parking spots, manages reservations and verifies the validity of them by using a license car plate recognition API. The system offers to all users a modern and efficient access experience and reservation of spots in a parking lot.

## Main Functionalities
- Monitoring parking spaces using ultrasonic sensors connected to Raspberry Pi 4.
- Controlling entry/exit from the parking lot using IR sensors and a servo motor that acts as a barrier.
- A dedicated module with Raspberry Pi Zero 2W and camera for the reserved parking space.
- Mobile application through which users can create accounts and make reservations.
- Verification of license plates by integrating with an external license plate recognition API.
- Validation of reservations and notification of users via SMS (AWS SNS) in case of unauthorized occupancy.
- Storage of user and reservation data in AWS DynamoDB.
- Containerized infrastructure (Docker) for running the FastAPI backend.

## Repository
The project repository is available at:  
[TODO: Insert repository link here]  

## Technologies Used
- **Hardware & Sensors**:
  - Raspberry Pi 4 with:
    - 3 ultrasonic sensors (detect parking slot availability)
    - 2 infrared sensors (detect entry/exit)
    - 1 servo motor (controls parking barrier)
  - Raspberry Pi Zero 2W with:
    - Raspberry Pi Camera Module (for reserved parking slot validation)

- **Software**:
  - Python (hardware control scripts and backend with FastAPI)
  - React Native (mobile app for reservations)
  - AWS DynamoDB (user and reservation data storage)
  - AWS SNS (SMS notifications for users)
  - Docker & Docker Compose (for backend deployment)
  - MQTT (communication between Raspberry Pi modules)
  - Automatic License Plate Recognition API

## Build Instructions
1. Clone the repository:  
   ```bash
   git clone <repository_link>
   cd smart-parking-system
   ```

2. Build the backend using Docker Compose:  
   ```bash
   docker-compose up --build
   ```

3. For Raspberry Pi hardware scripts (Python):  
   ```bash
   pip install -r requirements.txt
   ```

## Installation
1. Ensure you have **Docker** and **Docker Compose** installed for the backend.  
2. Install required Python libraries on Raspberry Pi devices:  
   ```bash
   pip install -r requirements.txt
   ```
3. Configure MQTT broker connection in the Raspberry Pi scripts.  
4. Set up AWS services:
   - DynamoDB tables for users and reservations
   - SNS topic for SMS notifications
   - IAM credentials for accessing AWS resources

## Run Instructions
1. **Backend (FastAPI)**:  
   ```bash
   docker-compose up
   ```
   Accessible at: `http://localhost:8000` (or configured host).

2. **Mobile App (React Native)**:  
   - On Android emulator (recommended if you don't have a physical device):
     ```bash
     cd mobile-app
     npm install
     npx expo start
     ```
     Then open the Expo Go app on the emulator.
   - Alternatively, on a physical device:
     ```bash
     cd mobile-app
     npm install
     npx expo start
     ```
     Scan the QR code with Expo Go app on your phone.

3. **Hardware scripts (on Raspberry Pi)**:  
   - For Raspberry Pi 4:
     ```bash
     cd HardwareControl
     python3 sensorControl.py
     ```
   - For Raspberry Pi Zero 2W:
     ```bash
     cd HardwareControl
     python3 cameraControl.py
     ```

## Configuration
- MQTT broker must be running and accessible by both Raspberry Pi modules.  
- To configure MQTT connection:
  1. Install an MQTT broker (e.g., Mosquitto is the one used for this project) on a server or one of the Raspberry Pi devices.
     ```bash
     sudo apt update
     sudo apt install mosquitto mosquitto-clients
     sudo systemctl enable mosquitto
     sudo systemctl start mosquitto
     ```
  2. Ensure the broker is reachable on the network (note its IP address and port, default 1883).  
  3. In the Python scripts (`sensorControl.py` and `cameraControl.py`), set the broker IP and port in the connection parameters:
     ```python
     client.connect("BROKER_IP", 1883, 60)
     ```
  4. Both Raspberry Pi modules must subscribe/publish to the correct topics defined in the scripts.  
- To configure License Plate Recognition API:
  1. Sign up for an account at [https://platerecognizer.com].
  2. Obtain your API key.
  3. Configure the API key in the backend, e.g., in `cameraControl.py`:
     ```python
     API_KEY = "your_api_key"
     API_URL = "https://api.platerecognizer.com/v1/plate-reader/"      
     ```
  4. The backend will send images to the API and receive the recognized license plate as a string.
- AWS credentials for DynamoDB and SNS must be configured in the backend.  
  - Set the credentials as environment variables in `docker-compose.yml`:
    ```yaml
    environment:
      AWS_ACCESS_KEY_ID: "your_access_key"
      AWS_SECRET_ACCESS_KEY: "your_secret_key"
      AWS_DEFAULT_REGION: "your_region"
    ```
  - This allows the backend FastAPI container to access AWS services correctly.

## Project Structure
SMARTPARKING/ (root project folder)
│
├── API_Smart_Park/           # Backend
│   ├── src/                  # Python modules, routers, imports
│   ├── main.py               # Includes all routers
│   ├── uploads/              # Contains the captured image
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── HardwareControl/          # Hardware scripts
│   ├── sensorControl.py
│   └── cameraControl.py
│
├── SmartMobileApp/            # Mobile app
|    ├── api/                  # Services: authentication, plates, reservations
|    ├── app.json              # Main configuration of the mobile app
|    ├── index.js              # For setting up the environment properly
|    └── [frontend screens]    # All React Native UI files for the app screens
|
├── .gitignore                 # Git ignore file             
└── README.md

## Authors
- Galetan Andreea
