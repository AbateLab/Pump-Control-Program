import serial


def find_pumps(ser,tot_range=10):
    pumps = []
    for i in range(tot_range):
        ser.write('%iADR\x0D'%i)
        output = ser.readline()
        if len(output)>0:
            pumps.append(i)
    return pumps

def run_all(ser):
    cmd = '*RUN\x0D'
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from run_all not understood'

def stop_all(ser):
    cmd = '*STP\x0D'
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from stop_all not understood'

def stop_pump(ser,pump):
    cmd = '%iSTP\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from stop_pump not understood'

    cmd = '%iRAT0UH\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from stop_pump not understood'

def set_rates(ser,rate):
    cmd = ''
    for pump in rate:
        flowrate = float(rate[pump])
        direction = 'INF'
        if flowrate<0: direction = 'WDR'
        frcmd = '%iDIR%s\x0D'%(pump,direction)
        ser.write(frcmd)
        output = ser.readline()
        if '?' in output: print frcmd.strip()+' from set_rate not understood'
        fr = abs(flowrate)
                
        if fr<5000:
            cmd += str(pump)+'RAT'+str(fr)[:5]+'UH*'
        else:
            fr = fr/1000.0
            cmd += str(pump)+'RAT'+str(fr)[:5]+'MH*'
    cmd += '\x0D'
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from set_rates not understood'

def get_rate(ser,pump):
    #get direction
    cmd = '%iDIR\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    sign = ''
    if output[4:7]=='WDR':
        sign = '-'
    cmd = '%iRAT\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from get_rate not understood'
    units = output[-3:-1]
    if units=='MH':
        rate = str(float(output[4:-3])*1000)
    if units=='UH':
        rate = output[4:-3]
    return sign+rate

def get_rates(ser,pumps):
    rates = dict((p,get_rate(ser,p).split('.')[0]) for p in pumps)
    return rates

def set_diameter(ser,pump,dia):
    cmd = '%iDIA%s\x0D'%(pump,dia)
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from set_diameter not understood'

    
def get_diameter(ser,pump):
    cmd = '%iDIA\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from get_diameter not understood'
    dia = output[4:-1]
    return dia

def prime(ser,pump):
    # set infuse direction
    cmd = '%iDIRINF\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from prime not understood'

    # set rate
    cmd = '%iRAT10.0MH\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from prime not understood'

    # run
    cmd = '%iRUN\x0D'%pump
    ser.write(cmd)
    output = ser.readline()
    if '?' in output: print cmd.strip()+' from prime not understood'





#ser = serial.Serial('COM3',19200)
#print ser.name       # check which port was really used
#print ser.isOpen()
#ser.close()
#pumps = find_pumps(ser)
#rates = get_rates(ser,pumps)
