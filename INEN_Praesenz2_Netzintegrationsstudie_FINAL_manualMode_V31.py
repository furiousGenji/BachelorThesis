# -*- coding: utf-8 -*-
"""
Created on Fri May  6 10:13:15 2022

@author: toebermannc
"""

#########################################################
# IEN Praktikum / INEN Präsenz / REN Practical Training #
# Netzintegration / Grid Integration - Version V3.0     #
#########################################################

##############################
### Import required modules
import numpy
import pandapower as pp
import pandapower.networks as nw
import pandapower.plotting as plot
import plotly.offline as plot2Browser
import math
import matlab.engine


### Define standard/constant values
# cosphi=0.95
import scipy.io

Q_TO_P_RATIO = -math.tan(math.acos(0.95))

# grid constraints
MAX_TRANSFORMER_LOADING = 60.0
MAX_LINE_LOADING = 60.0
MAX_BUS_VOLTAGE = 1.06
MIN_BUS_VOLTAGE = 0.97
out = " "
activePowerDataArray_int = []


##############################
# function to plot and report core data of grid
def grid_status_report(net, tempFilename):
    # interactive plot with net and results visualization in browser-window
    plot2Browser.plot(plot.pf_res_plotly(net, auto_open=False), filename=tempFilename)

    # plot voltage profile in spyder-plot-window
    plot.plot_voltage_profile(net)

    # report core data
    print("Max.  line loading \t\t\t %.3f %%" % (net.res_line.loading_percent.max()))
    print("Max.  transformer loading \t %.3f %%" % (net.res_trafo.loading_percent.max()))
    print("Max.  bus voltage \t\t\t %.3f p.u." % (net.res_bus.vm_pu.max()))
    print("Min.  bus voltage \t\t\t %.3f p.u." % (net.res_bus.vm_pu.min()))
    print("Total generation capacity \t %.3f MW" % (net.sgen.p_mw.sum()))
    print(" ")

    ## more detailled reporting
    # Maximum Line Loading
    max_loading_line_value = net.res_line.loading_percent.max()
    # Index of line with maximum loading or minimal index of lines with maximum loading (if more than 1 line)
    max_loaded_line_index = net.res_line.index[net.res_line.loading_percent == max_loading_line_value][0]
    # Constraint Violation?
    if max_loading_line_value > MAX_LINE_LOADING:
        stringConstraintViolation = "NOT OK!"
    else:
        stringConstraintViolation = ""
    # Report
    print("Line        with index %i has maximum loading of \t%.3f%% \t%s" % (
    max_loaded_line_index, max_loading_line_value, stringConstraintViolation))

    # Maximum Transformer Loading
    max_loading_trafo_value = net.res_trafo.loading_percent.max()
    # Index of transformer with maximum loading or minimal index of transformers with maximum loading (if more than 1 transformer)
    max_loaded_trafo_index = net.res_trafo.index[net.res_trafo.loading_percent == max_loading_trafo_value][0]
    # Constraint Violation?
    if max_loading_trafo_value > MAX_TRANSFORMER_LOADING:
        stringConstraintViolation = "NOT OK!"
    else:
        stringConstraintViolation = ""
    # Report
    print("Transformer with index %i has maximum loading of \t%.3f%% \t%s" % (
    max_loaded_trafo_index, max_loading_trafo_value, stringConstraintViolation))

    # Maximum Bus Voltage
    max_voltage_bus_value = net.res_bus.vm_pu.max()
    # Index of bus with maximum voltage or minimal index of busses with maximum voltage (if more than 1 bus)
    max_voltage_bus_index = net.res_bus.index[net.res_bus.vm_pu == max_voltage_bus_value][0]
    # Constraint Violation?
    if max_voltage_bus_value > MAX_BUS_VOLTAGE:
        stringConstraintViolation = "NOT OK!"
    else:
        stringConstraintViolation = ""
    # Report
    print("Bus         with index %i has maximum voltage of \t%.3f%% \t%s" % (
    max_voltage_bus_index, max_voltage_bus_value, stringConstraintViolation))

    # Minimum Bus Voltage
    min_voltage_bus_value = net.res_bus.vm_pu.min()
    # Index of bus with minimum voltage or minimal index of busses with minimum voltage (if more than 1 bus)
    min_voltage_bus_index = net.res_bus.index[net.res_bus.vm_pu == min_voltage_bus_value][0]
    # Constraint Violation?
    if min_voltage_bus_value < MIN_BUS_VOLTAGE:
        stringConstraintViolation = "NOT OK!"
    else:
        stringConstraintViolation = ""
    # Report
    print("Bus         with index %i has minimum voltage of \t%.3f%% \t%s" % (
    min_voltage_bus_index, min_voltage_bus_value, stringConstraintViolation))

    print("\n\n\n")

    return max_loaded_line_index, max_loaded_trafo_index, max_voltage_bus_index, min_voltage_bus_index


##############################
# Load grid ...
net = nw.create_synthetic_voltage_control_lv_network(network_class='rural_1')
# ... add some information to be shown during plotting ...
for i in net.line.index:
    net.line.loc[i , 'name'] = "line from " + str(net.line.from_bus[i]) + " to " + str(
        net.line.to_bus[i]) + " (Line index = " + str(net.line.index[i]) + ")"
for i in net.bus.index:
    net.bus.loc[i , 'name'] = str(net.bus.name[i]) + " (Bus ID = " + str(net.bus.index[i]) + ")" + " (Bus AP = " + str(out) +  ")" #!!!!!!!!!
# ... and add some information shown in tabular view ...
for i in net.sgen.index:
    net.sgen.loc[i , 'name'] = "Old Sgen at bus " + str(net.sgen.bus[i])
# ... and exchange transformer ...
pp.change_std_type(net, net.trafo.index[0], "0.63 MVA 20/0.4 kV", "trafo")
# ... and change line length ...
net.line.length_km *= 3.0
# ... and create new (potential) sgen at each feeder end point with P=0 MW and Q=0 MVar - if no sgen already exists
for i in net.bus.index:
    if (i not in net.sgen.bus.tolist()  # exclude busses with already existing sgen
            and i not in net.trafo.hv_bus.tolist()  # exclude transformer hv-bus
            and i not in net.trafo.lv_bus.tolist()  # exclude transformer lv-bus
            and (
                    i not in net.line.from_bus.tolist() or i not in net.line.to_bus.tolist())):  # exclude busses with ingoing AND outgoing line, so not a feeder end point bus
        pp.create_sgen(net, i, p_mw=0.0, q_mvar=0.0, name="NewGen at bus " + str(i))

##############################
# power flow calculation and results for unmodified grid
pp.runpp(net)

# grid status report
print("---------------\nUnmodified Grid\n---------------\n")
grid_status_report(net, 'UnmodifiedGrid.html')

##############################
# add your code / modifications here ...

# Initialize the connection between Matlab and Python
eng = matlab.engine.start_matlab()

# Calls ini_PVArrayGridAverageModel_new_sim.m
eng.ini_PVArrayGridAverageModel_new_sim(nargout = 0)

# Obtain value of activePower in Matlab
activePowerData = scipy.io.loadmat('activePowerData.mat')
activePowerDataArray = activePowerData['activePower']

for element in activePowerDataArray:
    for array in element:
        subarray = array[0]
        value = subarray[0]
        print("Active power is \n", value)
        activepower_int = int(value)/1000
        activePowerDataArray_int.append(activepower_int)
# out = eng.eval('activePower1')
# out = int(out)/1000
#
# # @Test!!!!!!!!!!!!!!!
# print("有功功率为： "+str(out))

# Left feeder
#net.sgen.loc[net.sgen.bus == 3, 'p_mw'] = activePowerDataArray_int[0] # PV @ bus_index 3
net.sgen.loc[net.sgen.bus == 3, 'p_mw'] = 0.065 # PV @ bus_index 3
net.sgen.loc[net.sgen.bus == 3, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 3, 'p_mw']
print("Active Power is "+str(net.sgen.loc[net.sgen.bus == 3, 'p_mw']) + "\t Reactive Power is " + str(net.sgen.loc[net.sgen.bus == 3, 'q_mvar']))

# middle feeder from start to end
#net.sgen.loc[net.sgen.bus == 8, 'p_mw'] = activePowerDataArray_int[1]  # PV @ bus_index 8
net.sgen.loc[net.sgen.bus == 8, 'p_mw'] = 0.065  # PV @ bus_index 8
net.sgen.loc[net.sgen.bus == 8, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 8, 'p_mw']
#net.sgen.loc[net.sgen.bus == 9, 'p_mw'] = activePowerDataArray_int[2]  # PV @ bus_index 9
net.sgen.loc[net.sgen.bus == 9, 'p_mw'] = 0.055  # PV @ bus_index 8
net.sgen.loc[net.sgen.bus == 9, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 9, 'p_mw']
net.sgen.loc[net.sgen.bus == 10, 'p_mw'] = 0.055  # PV @ bus_index 10
net.sgen.loc[net.sgen.bus == 10, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 10, 'p_mw']
net.sgen.loc[net.sgen.bus == 11, 'p_mw'] = 0.045  # PV @ bus_index 11
net.sgen.loc[net.sgen.bus == 11, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus ==11, 'p_mw']

# right feeder from start to end
net.sgen.loc[net.sgen.bus == 19, 'p_mw'] = 0.045  # PV @ bus_index 19
net.sgen.loc[net.sgen.bus == 19, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 19, 'p_mw']
net.sgen.loc[net.sgen.bus == 20, 'p_mw'] = 0.045  # PV @ bus_index 20
net.sgen.loc[net.sgen.bus == 20, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 20, 'p_mw']
net.sgen.loc[net.sgen.bus == 21, 'p_mw'] = 0.045  # PV @ bus_index 21
net.sgen.loc[net.sgen.bus == 21, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 21, 'p_mw']
net.sgen.loc[net.sgen.bus == 22, 'p_mw'] = 0.045  # PV @ bus_index 22
net.sgen.loc[net.sgen.bus == 22, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 22, 'p_mw']
net.sgen.loc[net.sgen.bus == 23, 'p_mw'] = 0.040  # PV @ bus_index 23
net.sgen.loc[net.sgen.bus == 23, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 23, 'p_mw']
net.sgen.loc[net.sgen.bus == 24, 'p_mw'] = 0.030  # PV @ bus_index 24
net.sgen.loc[net.sgen.bus == 24, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 24, 'p_mw']
net.sgen.loc[net.sgen.bus == 25, 'p_mw'] = 0.030  # PV @ bus_index 25
net.sgen.loc[net.sgen.bus == 25, 'q_mvar'] = Q_TO_P_RATIO * net.sgen.loc[net.sgen.bus == 25, 'p_mw']

### add storage
# in middle feeder at bus 6
pp.create_load(net, 6, p_mw=0.08, name="storage1")

# in right feeder at bus 16
pp.create_load(net, 16, p_mw=0.12, name="storage2")

### change transformer tap position
net.trafo.loc[0, 'tap_pos'] = 1

##############################
# power flow calculation and results for modified grid
pp.runpp(net)


# grid status report
print("--------------\nModified Grid\n--------------\n")
grid_status_report(net, 'ModifiedGrid.html')
