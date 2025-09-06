import RPi.GPIO as GPIO
import datetime
import time
import smbus # Import SMBus for I2C communication
import paho.mqtt.client as mqtt

# Define the broker and the topic for the MQTT connection with Raspberry Camera
BROKER = "192.168.1.8"
TOPIC = "parking/camera"

# MQTT client initialization
mqtt_sent = False
client = mqtt.Client()
client.connect(BROKER, 1883, 60)
client.loop_start()

# Define GPIO pins for three ultrasonic sensors
# Sensor 1
TRIG_PIN1 = 23
ECHO_PIN1 = 24
# Sensor 2
TRIG_PIN2 = 17
ECHO_PIN2 = 27
# Sensor 3
TRIG_PIN3 = 5
ECHO_PIN3 = 6

# Define GPIO pin for entrance IR sensor
ENTRANCE_IR_PIN = 22

# IR sensor for exit barrier control
EXIT_IR_PIN = 26

# Servo Motor pin (PWM capable pin)
SERVO_PIN = 12

# LCD I2C Configuration
I2C_ADDR = 0x27 # I2C device address
I2C_BUS = 1 # I2C bus

# LCD constants
LCD_WIDTH = 16 # Maximum characters per line
LCD_CHR = 1 # Character mode
LCD_CMD = 0 # Command mode
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_BACKLIGHT = 0x08 # Backlight on bit

# LCD flags for commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# LCD flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# LCD flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# LCD flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# LCD flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# I2C bus
i2c_bus = None

# Total parking spots
TOTAL_SPOTS = 3
available_spots = 3 # Start with empty parking lot

# Smart parking system settings
CAR_DETECTION_DISTANCE = 3 # Car detected when under 3cm
MIN_VALID_DISTANCE = 1 # Ignore readings below 1cm (sensor noise)
MAX_VALID_DISTANCE = 10 # Ignore readings above 10cm (not relevant)

# Barrier timing
BARRIER_OPEN_TIME = 5  # seconds


class SimpleTimer:
    def sleep(self, seconds):
        start_time = self.get_time()
        while self.get_time() - start_time < seconds:
            pass # Busy wait

    def get_time(self):
        # Use datetime standard module in Python
        return datetime.datetime.now().timestamp()


class ServoMotor:
    def __init__(self, pin, timer):
        self.pin = pin
        self.timer = timer
        self.is_open = False
        self.current_angle = 0 # Tracking current position

        # Setup servo pin
        GPIO.setup(self.pin, GPIO.OUT)

        # Initialize custom PWM at 50Hz (20ms period)
        self.frequency = 50
        self.period = 1.0 / self.frequency
        print("Servo initialized.")

    def set_angle(self, angle):
        if angle < 0:
            angle = 0
        elif angle > 90:
            angle = 90

        # Calculate duty cycle: 2.5% for 0°, 12.5% for 90°
        duty_cycle = 2.5 + (angle / 90.0) * 5

        # Convert duty cycle to pulse width in seconds
        pulse_width = (duty_cycle / 100.0) * self.period

        # Send PWM pulses for 0.5 seconds (25 pulses at 50Hz)
        pulses = 25
        for i in range(pulses):
            # High pulse
            GPIO.output(self.pin, GPIO.HIGH)
            self.timer.sleep(pulse_width)

            # Low pulse
            GPIO.output(self.pin, GPIO.LOW)
            self.timer.sleep(self.period - pulse_width)

        # Stop PWM signal (setting 0% duty cycle)
        GPIO.output(self.pin, GPIO.LOW)
        self.current_angle = angle

    def open_barrier(self):
        if not self.is_open:
            print("Opening barrier...")
            self.set_angle(90) # 90 degrees = barrier open
            self.is_open = True
            print("Barrier opened")

    def close_barrier(self):
        if self.is_open:
            print("Closing barrier...")
            self.set_angle(0) # 0 degrees = barrier closed
            self.is_open = False
            print("Barrier closed")

    def cleanup(self):
        print("Cleaning up servo...")
        if self.is_open or self.current_angle != 0:
            self.set_angle(0) # Ensuring initial position - CLOSED
            self.is_open = False
        GPIO.output(self.pin, GPIO.LOW)


def setup_gpio():
    GPIO.setmode(GPIO.BCM)

    # Setup Ultrasonic Sensors
    # Sensor 1
    GPIO.setup(TRIG_PIN1, GPIO.OUT)
    GPIO.setup(ECHO_PIN1, GPIO.IN)
    GPIO.output(TRIG_PIN1, False)

    # Sensor 2
    GPIO.setup(TRIG_PIN2, GPIO.OUT)
    GPIO.setup(ECHO_PIN2, GPIO.IN)
    GPIO.output(TRIG_PIN2, False)

    # Sensor 3
    GPIO.setup(TRIG_PIN3, GPIO.OUT)
    GPIO.setup(ECHO_PIN3, GPIO.IN)
    GPIO.output(TRIG_PIN3, False)

    # Setup IR sensors
    GPIO.setup(ENTRANCE_IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(EXIT_IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def lcd_init():
    global i2c_bus

    # Initialize the I2C bus
    i2c_bus = smbus.SMBus(I2C_BUS)

    # Initialize display in 4-bit mode
    lcd_byte(0x33, LCD_CMD) # Initialize
    lcd_byte(0x32, LCD_CMD) # Initialize
    lcd_byte(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE, LCD_CMD) # 2 lines, 5x8 font, 4-bit mode
    lcd_byte(LCD_DISPLAYCONTROL | LCD_DISPLAYON, LCD_CMD) # Display on, cursor off
    lcd_byte(LCD_ENTRYMODESET | LCD_ENTRYLEFT, LCD_CMD) # Left to right
    lcd_byte(LCD_CLEARDISPLAY, LCD_CMD) # Clear display
    time.sleep(0.005) # Wait for clear display command to complete


def lcd_byte(bits, mode):
    # Mode = 1 for character, 0 for command

    # High bits
    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    try:
        i2c_bus.write_byte(I2C_ADDR, bits_high)
    except IOError:
        print("I2C Error: Could not write to device")
        return

    # Toggle 'Enable' bit
    i2c_bus.write_byte(I2C_ADDR, (bits_high | 0x04)) # Enable high
    time.sleep(0.0005)
    i2c_bus.write_byte(I2C_ADDR, (bits_high & ~0x04)) # Enable low
    time.sleep(0.0001)

    # Low bits
    bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    i2c_bus.write_byte(I2C_ADDR, bits_low)
    i2c_bus.write_byte(I2C_ADDR, (bits_low | 0x04))
    time.sleep(0.0005)
    i2c_bus.write_byte(I2C_ADDR, (bits_low & ~0x04))
    time.sleep(0.0001)


def lcd_string(message, line):
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


def update_lcd_display(spots):
    lcd_string("Parking Spaces", LCD_LINE_1)
    lcd_string(f"Available: {spots}", LCD_LINE_2)


def check_entrance_ir_sensor():
    return GPIO.input(ENTRANCE_IR_PIN) == GPIO.LOW


def check_exit_ir_sensor():
    return GPIO.input(EXIT_IR_PIN) == GPIO.LOW


def handle_entrance_barrier(servo, timer):
    """Handle entrance barrier - open for 5 seconds then close"""
    print("\nCar detected at entrance - Opening barrier")
    servo.open_barrier()
    
    # Wait for 5 seconds
    timer.sleep(BARRIER_OPEN_TIME)
    
    print("Closing entrance barrier")
    servo.close_barrier()


def handle_exit_barrier(servo, timer):
    """Handle exit barrier - open for 5 seconds then close"""
    print("\nCar detected at exit - Opening barrier")
    servo.open_barrier()
    
    # Wait for 5 seconds
    timer.sleep(BARRIER_OPEN_TIME)
    
    print("Closing exit barrier")
    servo.close_barrier()


def measure_distance(timer, trig_pin, echo_pin):
    # Send 10 microseconds pulse to trigger
    GPIO.output(trig_pin, GPIO.HIGH)
    timer.sleep(0.00001)
    GPIO.output(trig_pin, GPIO.LOW)

    # Wait for echo to go HIGH
    pulse_start = time.time()
    timeout = pulse_start + 0.04 # 40ms timeout for echo
    while GPIO.input(echo_pin) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None # Timeout - no echo

    # Wait for echo to go LOW
    pulse_end = time.time()
    timeout = pulse_end + 0.04
    while GPIO.input(echo_pin) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None # Timeout - echo too long

    # Calculate pulse duration
    pulse_duration = pulse_end - pulse_start

    # Calculate distance in cm
    distance = pulse_duration * 17150 # speed of sound / 2 * 100 cm

    if distance < MIN_VALID_DISTANCE or distance > MAX_VALID_DISTANCE:
        return None

    return round(distance, 2)


def check_parking_spots(d1, d2, d3):
    spots = [d1, d2, d3]
    available = 0
    for dist in spots:
        if dist is None or dist > CAR_DETECTION_DISTANCE:
            available += 1
    return available


def main():
    global available_spots, mqtt_sent
    timer = SimpleTimer()

    # Do cleanup at beginning of the program
    GPIO.cleanup()

    # Setup GPIO pins
    setup_gpio()

    servo = ServoMotor(SERVO_PIN, timer)

    try:
        print("Initializing LCD on I2C")
        lcd_init()
        update_lcd_display(available_spots)

        print("Smart Parking System Running")

        last_entrance_ir_state = False
        last_exit_ir_state = False

        while True:
            # Check entrance IR sensor
            entrance_ir_detected = check_entrance_ir_sensor()
            
            # Handle entrance - trigger on rising edge (when car is first detected)
            if entrance_ir_detected and not last_entrance_ir_state:
                handle_entrance_barrier(servo, timer)
                
                # After barrier operation, update parking spots
                d1 = measure_distance(timer, TRIG_PIN1, ECHO_PIN1)
                d2 = measure_distance(timer, TRIG_PIN2, ECHO_PIN2)
                d3 = measure_distance(timer, TRIG_PIN3, ECHO_PIN3)
                actual_available = check_parking_spots(d1, d2, d3)
                available_spots = actual_available
                update_lcd_display(available_spots)

                # MQTT publish when car parks on spot d1
                if d1 is not None and d1 < 9:
                    print("Publishing to MQTT: car parked on spot 1")
                    client.publish(TOPIC, "start_camera")
                    mqtt_sent = True

                if d1 is None or d1 >= 9:
                    mqtt_sent = False

            last_entrance_ir_state = entrance_ir_detected

            # Check exit IR sensor
            exit_ir_detected = check_exit_ir_sensor()
            
            # Handle exit - trigger on rising edge (when car is first detected)
            if exit_ir_detected and not last_exit_ir_state:
                handle_exit_barrier(servo, timer)
                
                # After barrier operation, increment available spots
                if available_spots < TOTAL_SPOTS:
                    available_spots += 1
                    update_lcd_display(available_spots)

            last_exit_ir_state = exit_ir_detected

            # Parking spots monitoring (continuous monitoring)
            d1 = measure_distance(timer, TRIG_PIN1, ECHO_PIN1)
            timer.sleep(0.05)
            d2 = measure_distance(timer, TRIG_PIN2, ECHO_PIN2)
            timer.sleep(0.05)
            d3 = measure_distance(timer, TRIG_PIN3, ECHO_PIN3)

            actual_available = check_parking_spots(d1, d2, d3)
            if actual_available != available_spots:
                available_spots = actual_available
                update_lcd_display(available_spots)

            print(
                f"\rSensors: {d1}cm, {d2}cm, {d3}cm | Available: {available_spots}",
                end="",
            )

            timer.sleep(0.2)

    except KeyboardInterrupt:
        print("\n\nProgram stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Cleaning up...")
        try:
            servo.cleanup()
            lcd_byte(LCD_CLEARDISPLAY, LCD_CMD)
            lcd_string("System Offline", LCD_LINE_1)
            lcd_string("", LCD_LINE_2)
        except:
            pass
        GPIO.cleanup()
        print("GPIO pins cleaned up")
        print("Parking system shutdown complete")


if __name__ == "__main__":
    main()