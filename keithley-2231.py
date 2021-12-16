import pyvisa
import math

class Keithley_2231():
    MAX_VOLTAGE = 30
    MIN_VOLTAGE = 0
    MAX_CURRENT = 3
    MIN_CURRENT = 0

    def __init__(self,direction: str,voltage_limits = [MAX_VOLTAGE,MAX_VOLTAGE,5],current_limits = [MAX_CURRENT,MAX_CURRENT,MAX_CURRENT]) -> None:
        self.inst_dir = direction
        #Checks for limits
        if len(voltage_limits) != 3:
            raise ValueError("Voltage limits more or less than 3 values for voltage limits")
        if len(current_limits) != 3:
            raise ValueError("Current limits more or less than 3 values for current limits")
        for ch,val in enumerate(voltage_limits):
            if (ch+1 in [1,2]) and (val > self.MAX_VOLTAGE or val < self.MIN_VOLTAGE):
                raise ValueError("Invalid voltage limit for channel {}".format(ch+1))
            elif (ch+1 == 3) and (val > 5 or val < self.MIN_VOLTAGE):
                raise ValueError("Invalid voltage limit for channel {}".format(ch+1))

        for ch,val in enumerate(current_limits):
            if val > self.MAX_CURRENT or val < self.MIN_CURRENT:
                raise ValueError("Invalid current limit for channel {}".format(ch+1))
        #Rounding to PSU format limits   
        self.voltage_limits = [round(volt,2) for volt in voltage_limits]
        self.current_limits = [round(curr,3) for curr in current_limits]
        try:
            self.inst = pyvisa.ResourceManager().open_resource(direction)
        except:
            raise ConnectionError("Unable to connect to the specified direction")
        print("PSU Initialization")
        print(self.inst.query("*IDN?"))
        print("Software voltage limits are: CH1 -> {}V;CH2 -> {}V;CH3 -> {}V; ".format(self.voltage_limits[0],self.voltage_limits[1],self.voltage_limits[2]))
        print("Software current limits are: CH1 -> {}A;CH2 -> {}A;CH3 -> {}A; ".format(self.current_limits[0],self.current_limits[1],self.current_limits[2]))
        self.set_remote_operation()

    def __voltage_current_within_limits(self, channel: int, voltage: float, current: float) -> bool:
        return voltage <= self.voltage_limits[channel-1] and current <= self.current_limits[channel-1]

    def close(self) -> None:
        self.set_local_operation()
        self.inst.close()

    def set_remote_operation(self) -> None:
        self.inst.write("SYSTem:REMote")
    
    def set_local_operation(self) -> None:
        self.inst.write("SYSTem:LOCal")

    def enable_all_chanlles_output(self) -> None:
        self.inst.write("OUTP ON")
    
    def disable_all_channels_output(self) -> None:
        self.inst.write("OUTP OFF")

    def check_all_channels_output(self) -> bool:
        return bool(self.inst.query("OUTP:STAT?"))
    
    def __select_channel(self, channel: int) -> None:
        self.inst.write("INST:NSEL {}".format(channel))


    def set_voltage_and_current(self, channel: int, voltage: float, current:float) -> None:
        #Check if channel is valid
        if channel < 1 or channel > 3:
            raise ValueError("Invalid channel, must be 1,2 or 3")
        #Adecuate to format
        voltage = round(voltage,2)
        current = round(current,3)
        #Check if voltage is within software limits
        if not self.__voltage_current_within_limits(channel,voltage,current):
            raise ValueError("Voltage or Current is outbounds")
        #write to instrument
        self.inst.write("APPLy CH{},{},{}".format(channel,voltage,current))

    def read_voltage(self, channel: int) -> float:
        if channel < 1 or channel > 3:
            raise ValueError("Invalid channel, must be 1,2 or 3")
        self.__select_channel(channel)
        print("CH{} {}V".format(channel,str(self.inst.query("MEAS:VOLT?")).rstrip()))
        return float(self.inst.query("FETC?"))

    def read_current(self, channel: int): 
        if channel < 1 or channel > 3:
            raise ValueError("Invalid channel, must be 1,2 or 3")
        self.__select_channel(channel)
        print("CH{} {}A".format(channel,str(self.inst.query("MEAS:CURR?")).rstrip()))
        return float(self.inst.query("FETC:CURR?"))

    

if __name__ == "__main__":
    psu = Keithley("ASRL7::INSTR")
    psu.set_voltage_and_current(1,5,1.2)
    psu.enable_all_chanlles_output()
    psu.read_voltage(2)
    psu.read_current(1)
    psu.close()
