import RPi.GPIO as GPIO
import datetime
import time
import smbus  # Import SMBus for I2C communication

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

# Define GPIO pin for IR sensors
IR_SENSOR_PIN1 = 22  # GPIO pin connected to IR sensor output
IR_SENSOR_PIN2 = 26  # GPIO pin connected to IR sensor output


# LCD I2C Configuration
I2C_ADDR = 0x27    # I2C device address 
I2C_BUS = 1        # I2C bus (0 for older Raspberry Pi, 1 for newer ones)

# LCD constants
LCD_WIDTH = 16     # Maximum characters per line
LCD_CHR = 1        # Character mode
LCD_CMD = 0        # Command mode
LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
LCD_BACKLIGHT = 0x08  # Backlight on bit

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
available_spots = TOTAL_SPOTS

class SimpleTimer:
    def sleep(self, seconds):
        """Sleep for the specified number of seconds using a busy wait"""
        start_time = self.get_time()
        while self.get_time() - start_time < seconds:
            pass  # Busy wait
    
    def get_time(self):
        """Get current time in seconds"""
        # Use datetime module which is standard in Python
        return datetime.datetime.now().timestamp()

def setup_gpio():
    """Set up GPIO pins for all sensors"""
    GPIO.setmode(GPIO.BCM)
    
    # Setup Sensor 1
    GPIO.setup(TRIG_PIN1, GPIO.OUT)
    GPIO.setup(ECHO_PIN1, GPIO.IN)
    GPIO.output(TRIG_PIN1, False)
    
    # Setup Sensor 2
    GPIO.setup(TRIG_PIN2, GPIO.OUT)
    GPIO.setup(ECHO_PIN2, GPIO.IN)
    GPIO.output(TRIG_PIN2, False)
    
    # Setup Sensor 3
    GPIO.setup(TRIG_PIN3, GPIO.OUT)
    GPIO.setup(ECHO_PIN3, GPIO.IN)
    GPIO.output(TRIG_PIN3, False)

    # Setup IR sensor as input
    GPIO.setup(IR_SENSOR_PIN1, GPIO.IN)
    GPIO.setup(IR_SENSOR_PIN2, GPIO.IN)

    # Note: LCD is connected via I2C (GPIO 2/SDA and GPIO 3/SCL)
    # So no specific GPIO setup needed for LCD

def lcd_init():
    """Initialize the LCD display via I2C"""
    global i2c_bus
    
    # Initialize the I2C bus
    i2c_bus = smbus.SMBus(I2C_BUS)
    
    # Initialize display in 4-bit mode
    lcd_byte(0x33, LCD_CMD)  # Initialize
    lcd_byte(0x32, LCD_CMD)  # Initialize
    lcd_byte(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE, LCD_CMD)  # 2 lines, 5x8 font, 4-bit mode
    lcd_byte(LCD_DISPLAYCONTROL | LCD_DISPLAYON, LCD_CMD)  # Display on, cursor off
    lcd_byte(LCD_ENTRYMODESET | LCD_ENTRYLEFT, LCD_CMD)  # Left to right
    lcd_byte(LCD_CLEARDISPLAY, LCD_CMD)  # Clear display
    time.sleep(0.005)  # Wait for clear display command to complete

def lcd_byte(bits, mode):
    """Send byte to I2C LCD"""
    # Mode = 1 for character, 0 for command
    
    # High bits
    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    try:
        i2c_bus.write_byte(I2C_ADDR, bits_high)
    except IOError:
        print("I2C Error: Could not write to device")
    
    # Toggle 'Enable' bit
    i2c_bus.write_byte(I2C_ADDR, (bits_high | 0x04))  # Enable high
    time.sleep(0.0005)
    i2c_bus.write_byte(I2C_ADDR, (bits_high & ~0x04))  # Enable low
    time.sleep(0.0005)
    
    # Low bits
    bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    try:
        i2c_bus.write_byte(I2C_ADDR, bits_low)
    except IOError:
        print("I2C Error: Could not write to device")
    
    # Toggle 'Enable' bit
    i2c_bus.write_byte(I2C_ADDR, (bits_low | 0x04))  # Enable high
    time.sleep(0.0005)
    i2c_bus.write_byte(I2C_ADDR, (bits_low & ~0x04))  # Enable low
    time.sleep(0.001)

def lcd_string(message, line):
    """Send string to display"""
    # Send line address to LCD
    lcd_byte(line, LCD_CMD)
    
    # Send each character of the message
    message = message.ljust(LCD_WIDTH, " ")
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

def measure_distance(timer, trig_pin, echo_pin):
    """Measure distance using HC-SR04 ultrasonic sensor
    
    Args:
        timer: SimpleTimer instance
        trig_pin: GPIO pin connected to the TRIG pin of sensor
        echo_pin: GPIO pin connected to the ECHO pin of sensor
        
    Returns:
        Distance in cm or -1 if error
    """
    # Make sure trigger is low
    GPIO.output(trig_pin, False)
    timer.sleep(0.05)  # Wait for sensor to settle
    
    # Send 10μs pulse to trigger
    GPIO.output(trig_pin, True)
    timer.sleep(0.00001)  # 10 microseconds
    GPIO.output(trig_pin, False)
    
    # Wait for echo to start (pin goes HIGH)
    start_time = timer.get_time()
    timeout = start_time + 1  # 1 second timeout
    
    while GPIO.input(echo_pin) == 0:
        pulse_start = timer.get_time()
        if pulse_start > timeout:
            return -1  # Timeout error
    
    # Wait for echo to end (pin goes LOW)
    while GPIO.input(echo_pin) == 1:
        pulse_end = timer.get_time()
        if pulse_end > timeout:
            return -1  # Timeout error
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    
    # Distance = (time × speed of sound) ÷ 2
    # Speed of sound = 343 m/s = 34300 cm/s
    distance_cm = (pulse_duration * 34300) / 2
    
    return round(distance_cm, 2)

def check_parking_spots(distance1, distance2, distance3):
    """Check how many parking spots are occupied based on ultrasonic sensors
    
    Returns:
        Number of available spots
    """
    occupied = 0
    
    # Consider a spot occupied if distance is less than 50 cm
    if distance1 > 0 and distance1 < 50:
        occupied += 1
    if distance2 > 0 and distance2 < 50:
        occupied += 1
    if distance3 > 0 and distance3 < 50:
        occupied += 1
        
    return TOTAL_SPOTS - occupied

def check_ir_sensors():
    """Check IR sensors for entrance and exit detection

    Returns:
        Tuple (entrance_detected, exit_detected)
    """
    entrance_detected = GPIO.input(IR_SENSOR_PIN1) == 0  # entrance
    exit_detected = GPIO.input(IR_SENSOR_PIN2) == 0      # exit
    return entrance_detected, exit_detected


def update_lcd_display(available, total):
    """Update the LCD display with parking information"""
    lcd_string("Parking Lot", LCD_LINE_1)
    lcd_string(f"Available spots: {available}/{total}", LCD_LINE_2)

def main():
    global available_spots
    
    # Create the timer
    timer = SimpleTimer()
    
    # Setup GPIO pins
    setup_gpio()
    
    try:
        # Initialize LCD
        print("Initializing LCD on I2C (SDA: GPIO 2, SCL: GPIO 3)")
        lcd_init()
        
        # Initial display
        update_lcd_display(available_spots, TOTAL_SPOTS)
        
        print("Parking System Running")
        print("Press CTRL+C to exit")
        
        last_ir_state = False
        
        while True:
            # Check IR sensor for entrance
            vehicle_detected = check_ir_sensor()
            
            # Print only when state changes
            if vehicle_detected != last_ir_state:
                if vehicle_detected:
                    print("Vehicle detected at entrance!")
                    # Decrease available spots when car enters
                    if available_spots > 0:
                        available_spots -= 1
                    # Update LCD display
                    update_lcd_display(available_spots, TOTAL_SPOTS)
                else:
                    print("Entrance clear")
                last_ir_state = vehicle_detected
            
            # Measure distance from each sensor
            distance1 = measure_distance(timer, TRIG_PIN1, ECHO_PIN1)
            timer.sleep(0.1)  # Small delay between sensors
            
            distance2 = measure_distance(timer, TRIG_PIN2, ECHO_PIN2)
            timer.sleep(0.1)
            
            distance3 = measure_distance(timer, TRIG_PIN3, ECHO_PIN3)
            
            # Print sensor readings
            print("\n--- Sensor Readings ---")
            
            if distance1 >= 0:
                print(f"Sensor 1 Distance: {distance1} cm")
            else:
                print("Sensor 1 Error: Timeout")
                
            if distance2 >= 0:
                print(f"Sensor 2 Distance: {distance2} cm")
            else:
                print("Sensor 2 Error: Timeout")
                
            if distance3 >= 0:
                print(f"Sensor 3 Distance: {distance3} cm")
            else:
                print("Sensor 3 Error: Timeout")
            
            # Check parking spots based on ultrasonic sensors
            actual_available = check_parking_spots(distance1, distance2, distance3)
            
            # If actual available spots from sensors differs from our count,
            # update the count and display
            if actual_available != available_spots:
                available_spots = actual_available
                update_lcd_display(available_spots, TOTAL_SPOTS)
                print(f"Updated parking spots: {available_spots}/{TOTAL_SPOTS}")
            
            # Check if any sensor detects an object within 20 cm
            if (distance1 > 0 and distance1 < 20) or \
               (distance2 > 0 and distance2 < 20) or \
               (distance3 > 0 and distance3 < 20):
                print("WARNING: Object detected in close proximity!")
            
            # Wait before next measurement cycle
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            # Clear display on exit
            lcd_byte(LCD_CLEARDISPLAY, LCD_CMD)
        except:
            pass
        GPIO.cleanup()
        print("GPIO pins cleaned up")

if __name__ == "__main__":
    main()