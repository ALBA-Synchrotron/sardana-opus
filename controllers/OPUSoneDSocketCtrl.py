import os
import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import (OneDController,
                                     Referable,
                                     Type,
                                     Access,
                                     Description,
                                     DefaultValue)


class OPUSoneDSocketCtrl(OneDController, Referable):
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
        "add_temp2filename": {Type: bool,
                      Description: 'Add linkam temp to filename',
                      Access: DataAccess.ReadWrite
                      },
    }

    ON = 1
    MOVING = 0

    def __init__(self, inst, props, *args, **kwargs):
        super().__init__(inst, props, *args, **kwargs)
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
        self._log.debug("ReadOne... {0}".format(self._state))
        value = None
        if self._opusds.state() is PyTango.DevState.ON:
            # TODO: try to return reference
            try:
                output = self._opusds.getLastOpusOutput()
                self._log.debug("cmd output: {0}".format(output))
            except:
                self._log.debug("Exception:", exc_info=True)
        return value

    def RefOne(self, axis):
        temp_name = ''
        if self._add_temp2filename and self.linkam:
            temp_name = "_Temp{:+07.2f}".format(self._linkam_temp).replace('.', '_')

        name = '{0}{1}'.format(self._opus_nam, temp_name)
        fullpath = os.path.join(self._opus_pth, name)
        scheme = 'file'
        return '{}://{}'.format(scheme, fullpath)

    def StateOne(self, ind):
        self._log.debug("StateOne...")
        state = self._opusds.state()
        if state is PyTango.DevState.ON:
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
                self._linkam_temp = self.linkam.read_attribute("temperature").value
                temp_name = "_Temp{:+07.2f}".format(self._linkam_temp).replace('.', '_')
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

    def LoadOne(self, ind, value):
        pass

    def AbortOne(self, ind):
        self._opusds.stopOpusMacro()

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == "ds":
            return self._ds
        elif name.lower() == "opus_cmd":
            return self._opus_cmd
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


