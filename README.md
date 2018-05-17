# Pump-Control-Program
Program for controlling New Era syringe pumps at drop stations

### new_era.py
Provides initial functions to be used later in pump_control.py. These include:
  - "run" (for ALL pumps) and "stop" (for ALL and specific pumps) functions for running, stopping syringe pumps
  - "set rate" function for setting flow rate of individual syringe pumps
  - "prime" function for priming liquid through PE/2 tubing prior to use

### pump_control.py
Sets up the interface for the pump control system, which includes:
  - Pump numbers
  - Syringe pulldown menu
  - Text boxes for syringe contents
  - Flow rate boxes (in uL/hr)
  - Prime button
  - Status bar (running vs. stopped)

Defines "run update" function that enables adjustment of flow rates while currently running

Defines "syringe update" function that enables adjustment of syringe parameters if flow rates are stopped

Defines "prime pumps" function that allows for initialization, termination of priming syringes

Defines shutdown paramaters

### pump_control_timer.py

Same as pump_control.py, with an additional timer feature, where all pumps stop after expiration of the set time

### set_pump_number.py

Links pump number to a particular syringe pump; prints that number on interface
