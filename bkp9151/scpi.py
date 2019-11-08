#-*- coding: utf-8
''' SCPI 'driver' for the BK Precision 9151 Power Supply

Requires pyserial 2.6 (2.5 might work) and Python 2.6 or greater.
Compatible with Python 3.x as well.

MIT-Licensed: http://opensource.org/licenses/mit-license.html

Copyright 2019 William Stanislaus
wstanislaus@gmail.com
'''
from __future__ import print_function

import re
from time import sleep

import serial
from serial.serialutil import SerialException

BOOLSET       = frozenset([0, 1, 'ON', 'OFF'])
SOURCESET     = frozenset(['FIXED', 'LIST', 'DRM'])
AREASET       = frozenset([1, 2, 4, 8])
PORTFUNCSET   = frozenset(['TRIGGER', 'RIDFI', 'DIGITAL'])
RIMODESET     = frozenset(['OFF', 'LATCHING', 'LIVE'])
TRIGSOURCESET = frozenset(['IMMEDIATE', 'EXTERNAL', 'BUS'])

def connect(device, baud_rate, read_timeout=3, write_timeout=3, post_command_delay=50):
    '''Connects to a specified device and, if successful, returns a
    ScpiConnection object.'''

    try:
        con = serial.Serial(device, int(baud_rate), timeout=read_timeout, writeTimeout=write_timeout)
    except SerialException as ex:
        if ex.errno == 16:
            print('Cannot open {0} - device is busy.'.format(device))
        raise
    return ScpiConnection(con, post_command_delay=post_command_delay)

class ScpiConnection(object):
    ''' Object handling all SCPI and IEEE 488 command I/O. '''

    def __init__(self, con, post_command_delay):
        ''' Accepts a pyserial Serial object and wraps it with python-ish SCPI
        functionality. '''

        self.con = con
        self.post_command_delay = post_command_delay

    def close(self):
        ''' Closes the connectiont to the device '''
        self.con.close()
    
    def clear_register(self):
        ''' Clears all registers
        * Standard event status register
        * Quest condition register
        * Operation event register
        * Status byte register
        * Error code '''
        return self.sendcmd('*CLS')

    def sendcmd(self, command):
        ''' Sends a SCPI command to the device and returns the result in an
        appropriate python datatype.  Sleeps for the number of milliseconds
        specified by post_command_delay prior to reading the result.'''

        self.con.flushInput()
        self.con.flushOutput()

        result = None
        
        self.con.write('{0}{1}'.format(command, '\n'))

        sleep(float(self.post_command_delay / 1000.0))
        self.con.flush()
        if command.find('?') != -1:
            result = self.con.readline().decode('utf-8')
            if result != '':
                return result.strip()

        self.con.write('SYSTem:ERRor?\n')
        sleep(float(self.post_command_delay / 1000.0))
        self.con.flush()
        result = self.con.readline().decode('utf-8')
 
        return result.strip()

    def get_instrument(self):
        ''' Queries and returns the instrument ID
        containing the model, firmware version, and serial number. '''

        return self.sendcmd('*IDN?')

    def set_psc(self, value):
        '''This command control s whether or not the power supply send s when it is reset.
        1 OR ON: When power supply is reset, operation event enable register, query event
        enable register and standard event status register are all reset.
        0 OR OFF: The data of status byte regist er, operation event enable register, 
        quest event enable register and standard event status enable register is stored 
        in nonvolatile register, and is recalled when power supply is reset.'''

        if value not in BOOLSET:
            raise ScpiException('''Valid bool values are: 0, 1, 'ON', 'OFF'.''')

        return self.sendcmd('*PSC {0}'.format(value))
    
    def get_psc(self):
        '''Query PSC set value'''

        return self.sendcmd('*PSC?')

    def reset_to_default(self):
        '''Resets the power supply to its default setting. '''

        return self.sendcmd('*RST')

    def save_params(self, reference):
        '''Saves the operating parameters of the power supply to non volatile
        memory.The parameters include constant current, constant voltage,
        maximum voltage value and step voltage values.
        Input: Reference 1-50, example <3>'''

        reference = int(reference)
        if reference not in range(1,51):
            raise ScpiException('''Valid values are between 1 to 50''')

        return self.sendcmd('*SAV {0}'.format(reference))

    def recall_params(self, reference):
        '''Recalls saved parameters and sets the values. The parameters include 
        constant current, constant voltage, maximum voltage value and step voltage 
        values.
        Input: Reference 1-50, example <3>'''

        if reference not in range(1,51):
            raise ScpiException('''Valid values are between 1 to 50''')

        return self.sendcmd('*RCL {0}'.format(reference))
    
    def get_sys_error(self):
        '''Queries the error code and error information of the power supply.'''

        return self.sendcmd('SYST:ERR?')

    def get_sys_next_error(self):
        '''Queries next error code and error information of the power supply.'''

        return self.sendcmd('SYST:ERR:NEXT?')

    def get_sys_version(self):
        '''Query Software version'''

        return self.sendcmd('SYST:VERS?')

    def get_sys_address(self):
        '''Queries system address of the power supply.'''

        return self.sendcmd('SYST:ADDR?')

    def set_sys_remote(self):
        '''Puts the power supply in remote control mode.'''

        return self.sendcmd('SYST:REM')

    def set_sys_local(self):
        '''Configures the instrument for front panel operation.'''

        return self.sendcmd('SYST:LOC')

    def set_sys_remoteonly(self):
        '''Configures the instrument only for remote control mode. When using this 
        command, it is not possible to press LOCAL key on the front panel to revert 
        back to manual mode.'''

        return self.sendcmd('SYST:RWL')

    def get_quest_event_register(self):
        '''Queries the parameters of the quest event register. After execution, 
        the quest event register is reset.
        Bit Position LSB0:OV, LSB1:OT, LSB1: UNR
        OV - Over Voltage
        OT - Over Temperature
        UNR - Output of power supply is unregulated.'''

        return self.sendcmd('STAT:QUES:EVEN?')

    def get_quest_condition_register(self):
        '''Queries the parameters of the quest condition register. When a bit of 
        the quest condition changes, the corresponding bit value in the quest event 
        register will be set to 1.'''

        return self.sendcmd('STAT:QUES:COND?')

    def set_quest_event_enable_register(self, value):
        '''Sets the parameter of the quest event enable register. This parameter 
        determines which bit of the quest event register is set to 1. If a QUES 
        condition changes, the QUES bit of status byte register will be set to 1.
        Reset values, check get_psc command.'''

        value = int(value)
        if value not in range(0,256):
            raise ScpiException('''Valid values are between 0 to 255''')

        return self.sendcmd('STAT:QUES:ENAB {0}'.format(value))

    def get_quest_event_enable_register(self):
        '''Queries quest event enable regiter for set values.'''

        return self.sendcmd('STAT:QUES:ENAB?')

    def get_operation_event_register(self):
        '''Queries the parameters of the operation event register. After executing this 
        command the operation event register is reset.
        Bit Position LSB0:CAL, LSB1:WTG, LSB2:CV, LSB3:CC, LSB4:RI
        CAL - Calculating new calibration parameter
        WTG - Waiting for trigger Signal
        CV - In Constant Voltage Condition
        CC - In Constant Current Condition
        RI - Show input level condition for RI'''

        return self.sendcmd('STAT:OPER:EVEN?')

    def get_operatoin_condition_register(self):
        '''queries the parameters of the operation condition. When a parameter of the 
        operation condition register changes, the corresponding bit in the operation 
        event register will be set to 1.'''

        return self.sendcmd('STAT:OPER:COND?')

    def set_operation_event_enable_register(self, value):
        '''Sets the parameter of the operation event enable register. This parameter 
        determines which bit of the operation event register is set to 1. If a OPER 
        condition changes, the OPER bit of status byte register will be set to 1.
        Reset values, check get_psc command.'''

        value = int(value)
        if value not in range(0,256):
            raise ScpiException('''Valid values are between 0 to 255''')

        return self.sendcmd('STAT:OPER:ENAB {0}'.format(value))

    def get_operation_event_enable_register(self):
        '''Queries operation event enable regiter for set values.'''

        return self.sendcmd('STAT:OPER:ENAB?')

    def set_output_timer_state(self, value):
        '''Sets the output timer state of the power supply.
        Value:0|1|ON|OFF'''

        if value not in BOOLSET:
            raise ScpiException('''Valid bool values are: 0, 1, 'ON', 'OFF'.''')
    

        return self.sendcmd('OUTP:TIM {0}'.format(value))

    def get_output_timer_state(self):
        '''Query output timer state of the power supply.'''

        return self.sendcmd('OUTP:TIM?')

    def set_output_timer_data(self, value):
        '''Sets the time of the output timer. The unit is in SECOND and decimal fractions 
        cannot be used for this command.'''

        value = int(value)

        if value not in range(1,432000):
            raise ScpiException('''Valid values are between 1 to 432000(5 days) which is used to set timer value in seconds''')

        return self.sendcmd('OUTP:TIM:DATA {0}'.format(value)) 

    def get_output_timer_data(self):
        '''Query the time of the output timer, units are in seconds.'''

        return self.sendcmd('OUTP:TIM:DATA?')
        
    def set_output_state(self, value):
        '''Sets the power supply output on or off.
        Note: If output timer is required, set output timer state on and then set output state on.
        These two commands must be set in this order to function properly.'''

        if value not in BOOLSET:
            raise ScpiException('''Valid bool values are: 0, 1, 'ON', 'OFF'.''')
        

        return self.sendcmd('OUTP:STAT {0}'.format(value))

    def get_output_state(self):
        '''Query the power supply output on or off.'''
        
        return self.sendcmd('OUTP:STAT?')

    def set_source_mode(self, value):
        '''Configures power supply for command fixed mode, list mode or DVM mode.
        Note: MODE FIXED command can also be used to stop a list execution.'''

        if value not in SOURCESET:
            raise ScpiException('''Valid Source mode values are: 'FIXED', 'LIST', 'DRM'.''')

        return self.sendcmd('SOUR:MODE {0}'.format(value))

    def get_source_mode(self):
        '''Query Configured power supply for command fixed mode, list mode or DVM mode.'''

        return self.sendcmd('SOUR:MODE?')

    def get_max_current(self):
        '''Get maximum supported current in power supply.'''

        return self.sendcmd('SOUR:CURR? MAX')

    def get_max_voltage(self):
        '''Get maximum supported voltage in power supply.'''

        return self.sendcmd('SOUR:VOLT? MAX')

    def get_current(self):
        '''Get maximum supported current in power supply.'''

        return self.sendcmd('SOUR:CURR?')

    def get_voltage(self):
        '''Get maximum supported voltage in power supply.'''

        return self.sendcmd('SOUR:VOLT?')

    def set_max_current(self):
        '''Set to maximum supported current in power supply.'''

        return self.sendcmd('SOUR:CURR MAX')

    def set_max_voltage(self):
        '''Set to maximum supported voltage in power supply.'''

        return self.sendcmd('SOUR:VOLT MAX')

    def set_current_mA(self, value):
        '''Set current value of the power supply in milliamps.
        Parameters: MIN to MAX|MIN|MAX
        MIN = 0, MAX = 27100mA'''

        if value == 'MIN' or value == 'MAX':
            return self.sendcmd('CURR {0}'.format(value))
        
        value = int(value)

        if value not in range(0,27101):
            raise ScpiException('''Valid values are between 0 to 27100''')
        

        return self.sendcmd('CURR {0}mA'.format(value))

    def set_voltage_mV(self, value):
        '''Set voltage value of the power supply in millivolts.
        Parameters: MIN to MAX|MIN|MAX
        MIN = 0, MAX = 21000mV'''

        if value == 'MIN' or value == 'MAX':
            return self.sendcmd('CURR {0}'.format(value))
        
        value = int(value)

        if value not in range(0,21001):
            raise ScpiException('''Valid values are between 0 to 21000''')

        return self.sendcmd('VOLT {0}mV'.format(value))

    def set_list_mode(self, value):
        '''Sets trigger condition for executing the list file.
        Parameter: CONTINIOUS|STEP'''

        if value != 'CONTINIOUS' and value != 'STEP':
            raise ScpiException('''Valid values are CONTINIOUS or STEP''')

        return self.sendcmd('LIST:MODE {0}'.format(value))
    
    def get_list_mode(self):
        '''Get trigger condition mode.'''
        return self.sendcmd('LIST:MODE?')

    def set_list_step(self, value):
        '''Sets the operation mode of the list file.
        Values: 
        ONCE - List Operate Once
        REPEAT - Repeat list operation indefinitely.'''

        if value != 'ONCE' and value != 'REPEAT':
            raise ScpiException('''Valid values are ONCE or REPEAT''')

        return self.sendcmd('LIST:STEP {0}'.format(value))

    def get_list_step(self):
        '''Gets list operation mode.'''
        return self.sendcmd('LIST:STEP?')
    
    def set_list_count(self, value):
        '''Sets number of steps for the list operation.
        Values between 2 to 400'''

        if value not in range(2,401):
            raise ScpiException('''Valid values are between 2 and 400''')

        return self.sendcmd('LIST:COUNT {0}'.format(value))

    def get_list_count(self):
        '''Gets number of steps set for list operations.'''
        return self.sendcmd('LIST:COUNT?')

    def set_list_current_mA(self, level, value):
        '''Sets the current step.
        Level between 1 to 25
        Current values between 0 to 27100'''

        if level not in range(1,26):
            raise ScpiException('''Valid level values are between 1 and 25''')

        if value not in range(0,27101):
            raise ScpiException('''Valid current values are between 0 and 27100 in mA''')

        return self.sendcmd('LIST:CURR {0},{1}mA'.format(level,value))

    def get_list_current(self, level):
        '''Gets list current step based on level input.
        Level between 1 to 25'''

        if level not in range(1,26):
            raise ScpiException('''Valid level values are between 1 and 25''')

        return self.sendcmd('LIST:CURR? {0}'.format(level))

    def set_list_voltage_mV(self, level, value):
        '''Sets the voltage step.
        Level between 1 to 25
        Voltage values between 0 to 21000'''

        if level not in range(1,26):
            raise ScpiException('''Valid level values are between 1 and 25''')

        if value not in range(0,21001):
            raise ScpiException('''Valid voltage values are between 0 and 21000 in mV''')

        return self.sendcmd('LIST:VOLT {0},{1}mV'.format(level,value))

    def get_list_voltage(self, level):
        '''Gets list voltage step based on level input.
        Level between 1 to 25'''

        if level not in range(1,26):
            raise ScpiException('''Valid level values are between 1 and 25''')

        return self.sendcmd('LIST:VOLT? {0}'.format(level))

    def set_list_unit(self, value):
        '''This command sets the unit for the list width in either seconds (SECOND) or 
        milliseconds (MSECOND).'''

        if value != 'SECOND' and value != 'MSECOND':
            raise ScpiException('''Valid values are 'SECOND' and 'MSECOND'.''')

        return self.sendcmd('LIST:UNIT {0}'.format(value))

    def get_list_unit(self):
        '''Query configured list unit'''
        return self.sendcmd('LIST:UNIT?')

    def set_list_width(self, level, value):
        '''sets the minimum step time. Decimal fractions are not allowed for this command. 
        Units are in seconds or milliseconds, which are set using set_list_unit command 
        (see get_list_unit, units are SECOND or MSECOND). Set units first before using 
        this command.
        Level between 1 to 25
        Voltage values between 0 to 60000'''

        if level not in range(1,26):
            raise ScpiException('''Valid level values are between 1 and 25''')

        if value not in range(0,60001):
            raise ScpiException('''Valid width values are between 0 and 60000 in defined units''')

        return self.sendcmd('LIST:WID {0},{1}'.format(level,value))

    def get_list_width(self, level):
        '''Gets list width based on level input.
        Level between 1 to 25'''

        if level not in range(1,26):
            raise ScpiException('''Valid level values are between 1 and 25''')

        return self.sendcmd('LIST:WID? {0}'.format(level))

    def set_list_name(self, name):
        '''Sets the name for the list file. Make sure the file name does not exceed 8 characters.'''

        if len(name) > 8:
           raise ScpiException('''Valid name value cannot exceed 8 characters''')

        return self.sendcmd('LIST:NAME \'{0}\''.format(name))

    def get_list_name(self):
        '''Get list configured name.'''
        return self.sendcmd('LIST:NAME?') 

    def set_list_area(self, area):
        '''This command divides up the storage area for the list file in one of the 4 ways listed below.
        1 group per store area, 400 steps
        2 groups per stor age area, each group contains 200 steps.
        4 groups per stor age area, each group has 100 steps.
        8 groups of stor age area, each group has 50 steps.'''

        if area not in AREASET:
            raise ScpiException('''Valid values are: 1, 2, 4, 8.''')

        return self.sendcmd('LIST:AREA {0}'.format(area))

    def get_list_area(self):
        '''Get list configured area.'''
        return self.sendcmd('LIST:AREA?') 

    def list_save(self, location):
        '''Saves the list file to a register (non volatile memory) The memory can be written
        approximately 0.1 million times.'''

        if location not in range(1,9):
            raise ScpiException('''Valid values are between 1 and 8.''')
    
        return self.sendcmd('LIST:SAV {0}'.format(location))
    
    def list_recall_saved(self, location):
        '''Recall Saved the list file from a register (non volatile memory).'''

        if location not in range(1,9):
            raise ScpiException('''Valid values are between 1 and 8.''')
    
        return self.sendcmd('LIST:RCL {0}'.format(location))

    def get_input_voltage(self):
        '''Queries input voltage of the power supply. return in V'''
        return self.sendcmd('MEAS:VOLT?')

    def get_input_current(self):
        '''Queries input current of the power supply. return in A'''
        return self.sendcmd('MEAS:CURR?')
    
    def get_input_power(self):
        '''Queries input power of the power supply. return in W'''
        return self.sendcmd('MEAS:POW?')

    def get_dvm_voltage_reading(self):
        '''Queries voltage reading of the digital volt meter.'''
        return self.sendcmd('MEAS:DVM?')

    def set_system_remote_sense(self, value):
        '''Enables or Disables power supply remote sense function.'''

        if value not in BOOLSET:
            raise ScpiException('''Valid bool values are: 0, 1, 'ON', 'OFF'.''')

        return self.sendcmd('SYST:SENS {0}'.format(value))

    def get_system_remote_sense(self):
        '''Queries power supply remote sense function.'''

        return self.sendcmd('SYST:SENS?')

    def set_port_function(self, value):
        '''This command sets the mode of the port in the rear panel.
        TRIGGER function: Pin1 , pin2 are configured as external trigger 
        source for the power supply and to control the list operation.
        RI/DFI function: Inhibit Input c ontrol s the output state of 
        the power supply. The Fault Output can indicate the reason for 
        internal failure
        DIGITAL I/O function: Read and control the state of the digital port.'''

        if value not in PORTFUNCSET:
            raise ScpiException('''Valid  values are: 'TRIGGER', 'RIDFI', 'DIGITAL'.''')

        return self.sendcmd('PORT:FUNC {0}'.format(value))

    def get_port_function(self):
        '''Get configured port mode in rear panel.'''

        return self.sendcmd('PORT:FUNC?')

    def set_ri_mode(self, value):
        '''Sets the input mode for RI input pin.'''

        if value not in RIMODESET:
            raise ScpiException('''Valid  values are: 'OFF', 'LATCHING', 'LIVE'.''')

        return self.sendcmd('RI:MODE {0}'.format(value))

    def get_ri_mode(self):
        '''Get configured input mode for RI input pin.'''
        return self.sendcmd('RI:MODE?')

    def send_trigger(self):
        '''When trigger source is command mode, this command will give a trigger signal.'''
        return self.sendcmd('TRIG')

    def set_trigger_source(self, value):
        '''sets the trigger mode of the power supply.
        IMMediate: When this function is enabled, you can generate an immediate 
        trigger pulse by pressing Shift plus Trigger.
        EXTernal trigger signal (TTL): When this function is enabled, the power 
        supply can be triggered with a TTL pulse applied to pin 1 of the terminal 
        connector in the rear. The TTL on pulse width should be at least 5 ms.
        BUS Command: When this function is enabled, you can trigger the power 
        supply by sending a *TRG or TRIgger command to the power supply.'''

        if value not in TRIGSOURCESET:
            raise ScpiException('''Valid  values are: 'IMMEDIATE', 'EXTERNAL', 'BUS'.''')

        return self.sendcmd('TRIG:SOUR {0}'.format(value))

    def get_trigger_source(self):
        '''Get configured trigger mode of the power supply.'''
        return self.sendcmd('TRIG:SOUR?')
    
class ScpiException(Exception):
    ''' Exception class for SCPI Commands. Raised when a bounded
    parameter is invalid '''

    pass

