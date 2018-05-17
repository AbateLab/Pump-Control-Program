import sys
from PyQt4 import QtGui, QtCore
import serial
import new_era
import datetime

serial_port = 'COM3'

syringes = {'1 ml BD':'4.699',
            '3 ml BD':'8.585',
            '5 ml BD':'12.06',
            '10 ml BD':'14.60',
            '20 ml BD':'19.13',
            '30ml BD':'21.59'}


class PumpControl(QtGui.QWidget):
    
    def __init__(self):
        super(PumpControl, self).__init__()
        self.initUI()
        
    def initUI(self):      

        self.ser = serial.Serial(serial_port,19200,timeout=.1)
        print 'connected to',self.ser.name
        
        # set grid layout
        grid = QtGui.QGridLayout()
        grid.setSpacing(5)
        
        # setup two buttons along top
        self.runbtn = QtGui.QPushButton('Run/Update',self)
        grid.addWidget(self.runbtn,1,2)
        self.runbtn.setCheckable(True)
        self.runbtn.clicked.connect(self.run_update)

        self.stopbtn = QtGui.QPushButton('Stop',self)
        grid.addWidget(self.stopbtn,1,3)
        self.stopbtn.setCheckable(True)
        self.stopbtn.clicked.connect(self.stop_all)

        # setup timer stuff
        self.timerbtn = QtGui.QPushButton('Run with Timer',self)
        grid.addWidget(self.timerbtn,2,2,1,2)
        self.timerbtn.setCheckable(True)
        self.timerbtn.clicked.connect(self.run_update_timer)
        label = QtGui.QLabel('Set timer (in minutes):')
        label2 = QtGui.QLabel('Time remaining:')
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        label2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        grid.addWidget(label,3,1)
        
        grid.addWidget(label2,3,3)
        self.timein = QtGui.QLineEdit(self)
        grid.addWidget(self.timein,3,2)
        
        # create and display the timer
        self.label_time = QtGui.QLabel()
        self.timer = QtCore.QTimer()
        text = "--:--:--"
        font = QtGui.QFont("SansSerif", 16, QtGui.QFont.Bold)
        self.label_time.setFont(font)
        self.label_time.setText(text)
        grid.addWidget(self.label_time,3,4)

        # optional column labels
        grid.addWidget(QtGui.QLabel('Pump number'),4,0)
        grid.addWidget(QtGui.QLabel('Syringe'),4,1)
        grid.addWidget(QtGui.QLabel('Contents'),4,2)
        grid.addWidget(QtGui.QLabel('Flow rate'),4,3)
        grid.addWidget(QtGui.QLabel('Current flow rate'),4,4)
        
        # find pumps
        pumps = new_era.find_pumps(self.ser)
        
        # interate over pumps, adding a row for each
        self.mapper = QtCore.QSignalMapper(self)
        self.primemapper = QtCore.QSignalMapper(self)
        self.currflow = dict()
        self.rates = dict()
        self.prime_btns = dict()
        for i,pump in enumerate(pumps):
            row = 5+i
            
            # add pump number
            pumplab = QtGui.QLabel('Pump %i'%pump)
            pumplab.setAlignment(QtCore.Qt.AlignHCenter)
            grid.addWidget(pumplab,row,0)

            # add syringe pulldown
            combo = QtGui.QComboBox(self)
            [combo.addItem(s) for s in sorted(syringes)]
            self.mapper.setMapping(combo,pump)
            combo.activated.connect(self.mapper.map)
            grid.addWidget(combo,row,1)

            # add textbox to put syring contents
            grid.addWidget(QtGui.QLineEdit(),row,2)

            # add textbox to enter flow rates
            self.rates[pump] = QtGui.QLineEdit(self)
            grid.addWidget(self.rates[pump],row,3)

            # add label to show current flow rates
            self.currflow[pump] = QtGui.QLabel(self)
            self.currflow[pump].setAlignment(QtCore.Qt.AlignHCenter)
            grid.addWidget(self.currflow[pump],row,4)

            # add prime button
            btn = QtGui.QPushButton('Prime',self)
            btn.setCheckable(True)# makes the button toggleable
            self.primemapper.setMapping(btn,pump)
            btn.clicked.connect(self.primemapper.map)
            grid.addWidget(btn,row,5)
            self.prime_btns[pump] = btn


        # mapper thing
        self.mapper.mapped.connect(self.update_syringe)        
        self.primemapper.mapped.connect(self.prime_pumps)        

        # set up the status bar
        self.curr_state = 'Stopped'
        self.statusbar = QtGui.QLabel(self)
        grid.addWidget(self.statusbar,1,4)
        self.statusbar.setText('Status: '+self.curr_state)
        
        # set up the last command bar
        self.commandbar = QtGui.QLabel(self)
        grid.addWidget(self.commandbar,row+1,0,1,4)
        
        # make the prime state: a set containing the priming pumps
        self.prime_state = set()

        #initialize: set all flow rates to zero
        self.run_update()
        self.stop_all()
        [self.update_syringe(p) for p in pumps]
        self.commandbar.setText('')

        # keyboard shortcuts
        QtGui.QShortcut(QtGui.QKeySequence('Space'),self,self.stop_all)

        # format the page
        self.setLayout(grid)
        self.setWindowTitle('Pump control')
        #self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint) # always on top
        self.show()
        
    def stop_all(self):

        self.timer.stop()
        self.label_time.setText('-:--:--')
        
        self.runbtn.setChecked(0)
        self.timerbtn.setChecked(0)
        self.stopbtn.setChecked(1)
        new_era.stop_all(self.ser)
        self.curr_state = 'Stopped'
        self.statusbar.setText('Status: '+self.curr_state)
        self.commandbar.setText('Last command: stop all pumps') 
        [self.currflow[pump].setText('0 ul/hr') for pump in self.rates]
        self.prime_state = set()
        [self.prime_btns[p].setChecked(0) for p in self.rates]

    def run_update(self):
        #check if the flow rates are legit numbers, if not set to zero
        self.runbtn.setChecked(1)
        self.stopbtn.setChecked(0)
        rates = {}
        for pump in self.rates:
            if isfloat(self.rates[pump].text()):
                rates[pump] = str(self.rates[pump].text()).strip()
            else:
                rates[pump] = '0'
                self.rates[pump].setText('0')

        self.timer.stop()
        self.label_time.setText('-:--:--')
        self.timerbtn.setChecked(0)

        if self.curr_state=='Running':
            new_era.stop_all(self.ser)
            new_era.set_rates(self.ser,rates)
            new_era.run_all(self.ser)
            actual_rates = new_era.get_rates(self.ser,rates.keys())
            self.commandbar.setText('Last command: update '+', '.join(['p%i=%s'%(p,actual_rates[p]) for p in actual_rates]))
            [self.currflow[pump].setText(actual_rates[pump]+' ul/hr') for pump in actual_rates]
                
        if self.curr_state=='Stopped':
            new_era.set_rates(self.ser,rates)
            new_era.run_all(self.ser)
            self.curr_state = 'Running'
            self.statusbar.setText('Status: '+self.curr_state)
            actual_rates = new_era.get_rates(self.ser,rates.keys())
            self.commandbar.setText('Last command: run '+', '.join(['p%i=%s'%(p,actual_rates[p]) for p in actual_rates]))
            [self.currflow[pump].setText(actual_rates[pump]+' ul/hr') for pump in actual_rates]

    def startTimerDisplay(self):
        self.timer.start(1000)

    def updateTimerDisplay(self):
        self.time -= 1
        text = "%d:%02d:%02d" % (self.time/3600,self.time/60 % 60,self.time % 60)
        self.label_time.setText(text)
        if self.time == 0:
            self.timer.stop()
            self.stop_all()
     
    def run_update_timer(self):
        #check if the flow rates are legit numbers, if not set to zero
        self.timerbtn.setChecked(1)
        self.stopbtn.setChecked(0)
        rates = {}
        for pump in self.rates:
            if isfloat(self.rates[pump].text()):
                rates[pump] = str(self.rates[pump].text()).strip()
            else:
                rates[pump] = '0'
                self.rates[pump].setText('0')
                
        # check time input is valid
        if isfloat(self.timein.text()):
            if float(self.timein.text()) > 0:

                # set the pumps
                if self.curr_state=='Running':
                    new_era.stop_all(self.ser)
                    new_era.set_rates(self.ser,rates)
                    new_era.run_all(self.ser)
                    actual_rates = new_era.get_rates(self.ser,rates.keys())
                    self.commandbar.setText('Last command: update '+', '.join(['p%i=%s'%(p,actual_rates[p]) for p in actual_rates]))
                    [self.currflow[pump].setText(actual_rates[pump]+' ul/hr') for pump in actual_rates]
                        
                if self.curr_state=='Stopped':
                    new_era.set_rates(self.ser,rates)
                    new_era.run_all(self.ser)
                    self.curr_state = 'Running'
                    self.statusbar.setText('Status: '+self.curr_state)
                    actual_rates = new_era.get_rates(self.ser,rates.keys())
                    self.commandbar.setText('Last command: run '+', '.join(['p%i=%s'%(p,actual_rates[p]) for p in actual_rates]))
                    [self.currflow[pump].setText(actual_rates[pump]+' ul/hr') for pump in actual_rates]

                # connect the button to the start method ...
                self.time = float(self.timein.text())*60
                text = "%d:%02d:%02d" % (self.time/3600,self.time/60 % 60,self.time % 60)
                self.label_time.setText(text)
                self.timer = QtCore.QTimer()
                self.startTimerDisplay()
                # connect timer to the update method
                self.timer.timeout.connect(self.updateTimerDisplay)

            else:
                self.commandbar.setText("Not a valid timer input")
                self.timerbtn.setChecked(0)
                self.stopbtn.setChecked(1)
            
        else:
            self.commandbar.setText("Not a valid timer input")
            self.timerbtn.setChecked(0)
            self.stopbtn.setChecked(1)
                 
    def update_syringe(self,pump):
        if self.curr_state == 'Stopped':
            dia = syringes[str(self.mapper.mapping(pump).currentText())]
            new_era.set_diameter(self.ser,pump,dia)
            dia = new_era.get_diameter(self.ser,pump)
            self.commandbar.setText('Last command: pump %i set to %s (%s mm)'%(pump,self.mapper.mapping(pump).currentText(),dia))
        else:
            self.commandbar.setText("Can't change syringe while running")

    def prime_pumps(self,pump):
        if self.curr_state == 'Stopped':
            if pump not in self.prime_state: # currently not priming
                new_era.prime(self.ser,pump)
                self.commandbar.setText('Last command: priming pump %i'%pump)
                self.statusbar.setText('Status: Priming')
                self.prime_state.add(pump)# add to prime state
            else: # currently priming
                new_era.stop_pump(self.ser,pump)
                self.commandbar.setText('Last command: stopped pump %i'%pump)
                self.prime_state.remove(pump)# remove prime state
                if len(self.prime_state)==0: self.statusbar.setText('Status: Stopped')# if this is the last one, show status=Stopped
            actual_rates = new_era.get_rates(self.ser,self.rates.keys())
            self.currflow[pump].setText(actual_rates[pump]+' ul/hr')
        else:
            self.commandbar.setText("Can't prime pump while running")
            self.prime_btns[pump].setChecked(0)

    def shutdown(self):
        self.stop_all()
        self.ser.close()

def isfloat(str):
    try: 
        float(str)
    except ValueError: 
        return False
    return True

def main():
    app = QtGui.QApplication(sys.argv)
    ex = PumpControl()
    ret = app.exec_()
    ex.shutdown()
    sys.exit(ret)

if __name__ == '__main__':
    main()
