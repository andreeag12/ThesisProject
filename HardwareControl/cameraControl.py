from picamera2 import Picamera2
from time import sleep
import requests
from PIL import Image
import io
import paho.mqtt.client as mqtt
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurations
API_KEY = "2491ff317ab16b7b95c78f964d041bfca5ccedc5"  # Plate Recognizer API Key
API_URL = "https://api.platerecognizer.com/v1/plate-reader/"
FASTAPI_URL = "http://192.168.1.13:8000/private-parking/upload/"
IMAGE_PATH = "/home/raspberry_user/ParckingSystem/car.jpg"
MQTT_BROKER = "192.168.1.8"  # Pi 4 broker IP
MQTT_TOPIC = "parking/camera"

# Functions
def capture_image(image_path: str):
    """Capture an image with Raspberry Pi camera."""
    camera = Picamera2()
    config = camera.create_still_configuration(main={"size": (2028, 1520)})
    camera.configure(config)
    print("Starting camera...")
    camera.start()
    sleep(3)  # camera warm-up
    camera.capture_file(image_path)
    camera.stop()
    print(f"Image captured and saved at {image_path}")

def recognize_plate(image_path):
    """Send image to Plate Recognizer API and return plate in uppercase."""
    try:
        with open(image_path, "rb") as image_file:
            files = {"upload": image_file}
            headers = {"Authorization": f"Token {API_KEY}"}
            response = requests.post(API_URL, files=files, headers=headers, timeout=10)
            
            if response.status_code != 201:
                logger.error(f"Plate Recognizer API error: {response.status_code} - {response.text}")
                return None
                
            data = response.json()
            logger.info(f"Plate Recognizer response: {data}")
            
            if "results" not in data or len(data["results"]) == 0:
                logger.warning("No plates detected")
                return None
                
            plate = data["results"][0].get("plate", "")
            result = plate.upper() if plate else None
            logger.info(f"Detected plate: {result}")
            return result
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Plate Recognizer API: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in recognize_plate: {e}")
        return None


def send_image_to_fastapi(image_path, plate):
    """Send image and detected plate to FastAPI."""
    try:
        logger.info(f"Sending image to FastAPI - plate: {plate}")
        
        with Image.open(image_path) as image:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

        # Prepare files for multipart/form-data
        files = {
            'file': ('car.jpg', img_byte_arr, 'image/jpeg')
        }
        
        # Prepare form data
        data = {
            'plate': plate or "",
            'spot_id': "1"
        }
        
        logger.info(f"Sending request to {FASTAPI_URL}")
        logger.info(f"Form data: {data}")
        
        response = requests.post(
            FASTAPI_URL,
            files=files,
            data=data,  # Use data parameter for form fields
            timeout=30
        )
        
        logger.info(f"FastAPI response status: {response.status_code}")
        logger.info(f"FastAPI response headers: {response.headers}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"FastAPI success response: {result}")
            return result
        else:
            logger.error(f"FastAPI error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Request to FastAPI timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to FastAPI")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to FastAPI: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in send_image_to_fastapi: {e}")
        return None

# MQTT Callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")


def on_message(client, userdata, msg):
    message = msg.payload.decode()
    logger.info(f"MQTT message received on topic {msg.topic}: {message}")
    
    if message == "start_camera":
        logger.info("\n--- Triggered by MQTT: Starting camera capture workflow ---")
        try:
            # Step 1: Capture image
            capture_image(IMAGE_PATH)
            
            # Step 2: Recognize plate
            plate = recognize_plate(IMAGE_PATH)
            
            # Step 3: Send to FastAPI (even if no plate detected)
            result = send_image_to_fastapi(IMAGE_PATH, plate)
            
            if result:
                logger.info("FastAPI workflow completed successfully")
                logger.info(f"Result: {result}")
            else:
                logger.error("FastAPI workflow failed")
                
        except Exception as e:
            logger.error(f"Error during workflow: {e}", exc_info=True)

def on_disconnect(client, userdata, rc):
    logger.info(f"Disconnected from MQTT broker with result code: {rc}")

# MAIN
def main():
    logger.info("Starting Pi Zero parking system...")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}...")
    
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        logger.info("Starting MQTT loop...")
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        client.disconnect()
    except Exception as e:
        logger.error(f"MQTT connection error: {e}")


if __name__ == "__main__":
    main()