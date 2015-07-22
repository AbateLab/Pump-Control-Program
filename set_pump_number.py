import serial

### SET THESE PARAMETERS HERE
serial_port = '/dev/cu.usbserial'
pump_number = 4


### LEAVE EVERYTHING BELOW HERE THE SAME
def print_pump_number(ser,tot_range=100):
    for i in range(tot_range):
        ser.write('%iADR\x0D'%i)
        output = ser.readline()
        if len(output)>0:
            print 'current pump set to %i'%i
            break

ser = serial.Serial(serial_port,19200,timeout=0.1)
print_pump_number(ser)
print 'setting pump to %i'%pump_number
ser.write('*ADR%iB19200\x0D'%pump_number)
ser.readline()
print_pump_number(ser)
ser.close()
