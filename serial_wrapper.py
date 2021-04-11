
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
    arduino.write(bytes(x, 'utf-8'))
    time.sleep(0.05)
    data = arduino.readline()
    return data
    
# Send boolean value to arduino and return whether the query was successful or not
def send_boolean_to_arduino(b: bool):
    s = '1' if b else '0'
    
    # A helper function for trying to read data from arduino. Usually result
    # comes after 3-4 tries, but sometimes it may take longer or not come at all
    def try_to_read_data(upper_limit: int, var: bool):
        tries = 0
        raw = write_read(var)
        while tries < upper_limit and not raw:
            raw = write_read(var)
            tries += 1
        return raw
    
    # Stop function if the connection can not be established
    conn, desc = establish_connection()
    if not conn: 
        return conn, desc
        
    # Arduino might sometimes return some trash, which causes utf-8 decode to throw UnicodeDecodeError.
    # In this case, we just return false for the main function and let user try the operation again. The reason
    # for this is that they are so rare and complicated to deal with
    res = try_to_read_data(maximum_iteration,s)
    if not res:
        return False, 'connection timed out, too many tries'
    else:
        try:
            value = res.decode('utf-8')
            if value == 'S':
                return True, None
            else:
                return False, 'arduino returned error code'
        except UnicodeDecodeError:
            return False, 'problems with utf-8 decoding'
            
            
                