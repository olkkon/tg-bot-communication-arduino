
import serial
import time

arduino = None
arduino_port = 'COM4'
maximum_iteration = 10

# A function to open new connection, re-open expired connection or detect that connection is not available
def establish_connection():
    global arduino
    # Check the connection to arduino
    if arduino == None:
        try: # No connection to arduino, try to create it
            arduino = serial.Serial(port=arduino_port, baudrate=115200, timeout=.1)
        except serial.SerialException:
            # Connection could not be created
            return False, 'arduino is not connected to the server'
    else:
        try: # Connection exist, try whether is has been expired or not
            arduino.read()
            # Connection working, move on inside the function
        except serial.SerialException:
            try: # Connection expired, try to create it
                arduino = serial.Serial(port=arduino_port, baudrate=115200, timeout=.1)
                # Connection working, move on inside the function
            except serial.SerialException:
                # Connection could not be created
                return False, 'arduino is not connected to the server'
    return True, None

# Encode data and send it to arduino. Read result and return it
def write_read(x):
    tries, data = 0,0
    while tries < maximum_iteration and not data:
        arduino.write(bytes(x, 'utf-8'))
        time.sleep(0.05)
        data = arduino.readline()
        tries += 1
    return data
    
# NOTE TO FOLLOWING FUNCTIONS:
# Arduino might sometimes return some trash, which causes utf-8 decode to throw UnicodeDecodeError.
# In this case, we just return false for the main function and let user try the operation again. The reason
# for this is that they are so rare and complicated to deal with.

# Toggle a led connected to arduino to value given in the parameter.
# Returns boolean whether the operation was successful and description as string if not.
def toggle_led(b: bool):
    s = '1' if b else '0'
    
    # Stop function if the connection can not be established
    conn, desc = establish_connection()
    if not conn: 
        return conn, desc
        
    res = write_read(f"w{s}")
    if not res:
        return False, 'connection timed out, too many tries'
    else:
        try:
            value = res.decode('utf-8')
            if value[0] == 'S':
                return True, None
            else:
                return False, 'arduino returned error code'
        except UnicodeDecodeError:
            return False, 'problems with utf-8 decoding'

# Get current led state. 
# Returns boolean whether the operation was successful and description,
# where in the positive case is led state and in fail case the description of the error.
def get_led_state():
    # Stop function if the connection can not be established
    conn, desc = establish_connection()
    if not conn: 
        return conn, desc
        
    res = write_read('r')
    if not res:
        return False, 'connection timed out, too many tries'
    else:
        try:
            value = res.decode('utf-8')
            if value[0] == 'A':
                s = True if value[1] == '1' else False
                return True, s
            else:
                return False, 'arduino returned error code'
        except UnicodeDecodeError:
            return False, 'problems with utf-8 decoding'

            
            
                