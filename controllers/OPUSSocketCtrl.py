import time
import socket

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description, DefaultValue


class OPUSSocketCtrl(CounterTimerController):
    MaxDevice = 1

    ctrl_properties = {
        "ds": {Type: str,
               Description: 'Opus Ds URI',
               DefaultValue: "bl01/ct/opus"
               },
    }

    axis_attributes = {
        "opus_cmd": {Type: str,
                    Description: 'OPUS MeasureSample cmd',
                    Access: DataAccess.ReadOnly
                    },
        "opus_exp": {Type: str,
                     Description: 'OPUS experiment',
                     Access: DataAccess.ReadWrite
                     },
        "opus_xpp": {Type: str,
                     Description: 'OPUS experiment path',
                     Access: DataAccess.ReadWrite
                     },
        "opus_nam": {Type: str,
                     Description: 'OPUS filename',
                     Access: DataAccess.ReadWrite
                     },
        "opus_pth": {Type: str,
                     Description: 'OPUS measurement path',
                     Access: DataAccess.ReadWrite
                     },
        "read_peak": {Type: bool,
                      Description: 'Read the scan PKA',
                      Access: DataAccess.ReadWrite
                      },
        "add_temp2filename": {Type: bool,
                      Description: 'Add linkam temp to filename',
                      Access: DataAccess.ReadWrite
                      },
    }

    ON = 1
    MOVING = 0

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._opus_macro_is_running = False
        # Create DS proxy
        try:
            self._opusds = PyTango.DeviceProxy(self.ds)
            self._state = State.On
        except PyTango.DevFailed:
            self._opusds = None
            self._state = State.Fault

        self._opus_pth = ""
        self._opus_nam = ""
        self._opus_cmd = "COMMAND_LINE MeasureSample"
        self._opus_exp = None
        self._opus_xpp = None
        self._add_temp2filename = False
        
        try:
            self.linkam = PyTango.DeviceProxy('bl01/ct/linkam')
        except:
            self.linkam = None

    def ReadOne(self, ind):
        self._log.debug("ReadOne... {0}, {1}".format(self._read_peak,
                                                     self._state == State.On))
        value = None
        if self._read_peak and self._opusds.state() is PyTango.DevState.ON:
            try:
                output = self._opusds.getLastOpusOutput()
                value = float(output)
            except:
                self._log.debug("Exception:", exc_info=True)
        return value

    def StateOne(self, ind):
        self._log.debug("StateOne...")
        state = self._opusds.state()
        if state is PyTango.DevState.ON:
            if self._opus_macro_is_running and self._read_peak:
                # Read PKA if macro has finished
                self._opusds.runOpusCMD("READ_PKA")
                state = State.Moving
            else:
                state = State.On
            self._opus_macro_is_running = False
        elif state is PyTango.DevState.RUNNING:
            state = State.Moving
        elif state is PyTango.DevState.ALARM:
            state = State.Fault
        status = self._opusds.status()
        self._log.debug("StateOne... {0}, {1}".format(state, status))
        return state, status

    def StartAll(self):
        self._log.debug("StartAll")

    def PreStartOne(self, axis, value=None):
        # self._log.debug('PreStartOne axis %s' % axis)
        self._opus_cmd = "COMMAND_LINE MeasureSample (0, {{EXP='{0}', XPP='{1}'"
        if self._opus_nam != '':
            temp_name = ''
            if self._add_temp2filename and self.linkam:
                temp_name = "_Temp{:+07.2f}".format(self.linkam.read_attribute("temperature").value).replace('.','_')
            self._opus_cmd += ", NAM='{0}{1}'".format(self._opus_nam, temp_name)
                
        if self._opus_pth != '':
            self._opus_cmd += ", PTH='{0}'".format(self._opus_pth)
        self._opus_cmd += "}});"
        self._opus_cmd = self._opus_cmd.format(self._opus_exp, self._opus_xpp)
        self._log.debug("PreStartOne... {}".format(self._opus_cmd))

        return True #self._opusds.connect()

    def StartOne(self, axis, value=None):
        self._log.debug("StartOne")
        self._opus_macro_is_running = True
        self._opusds.runOpusCMD(self._opus_cmd)

    def LoadOne(self, ind, value, repetitions, latency):
        pass

    def AbortOne(self, ind):
        self._opusds.stopOpusMacro()

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == "ds":
            return self._ds
        elif name.lower() == "opus_cmd":
            return self._opus_cmd
        elif name.lower() == "read_peak":
            return self._read_peak
        elif name.lower() == "opus_xpp":
            return self._opus_xpp
        elif name.lower() == "opus_exp":
            return self._opus_exp
        elif name.lower() == "opus_pth":
            return self._opus_pth
        elif name.lower() == "opus_nam":
            return self._opus_nam
        elif name.lower() == "add_temp2filename":
            return self._add_temp2filename

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == "ds":
            self._ds = value
        elif name.lower() == "read_peak":
            self._read_peak = value
        elif name.lower() == "opus_xpp":
            self._opus_xpp = value
        elif name.lower() == "opus_exp":
            self._opus_exp = value
        elif name.lower() == "opus_pth":
            self._opus_pth = value
        elif name.lower() == "opus_nam":
            self._opus_nam = value
        elif name.lower() == "add_temp2filename":
            self._add_temp2filename = value


