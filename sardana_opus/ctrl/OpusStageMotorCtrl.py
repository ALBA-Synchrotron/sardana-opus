import time
import PyTango
from sardana.pool.controller import (MotorController,
                                     Type,
                                     Access,
                                     Description,
                                     DefaultValue)
from sardana import State, DataAccess

class OpusStageMotorController(MotorController):
    """The most basic controller to manage the Opus Tango Stage motors
    """

    ctrl_properties = {
        "ds": {Type: str,
               Description: 'Opus Ds URI',
               DefaultValue: "bl01/ct/opus"
               },
    }

    axis_attributes = {
        "axis_name": {Type: str,
                      Description: 'Axis name (x, y, or z)',
                      #Access: DataAccess.ReadWrite
                      },
    }

    MaxDevice = 3

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        super(OpusStageMotorController, self).__init__(inst, props, *args,
                                                       **kwargs)
        # Create DS proxy
        try:
            self._opusds = PyTango.DeviceProxy(self.ds)
            self._state = State.On
        except PyTango.DevFailed:
            self._opusds = None
            self._state = State.Fault
        self.attributes = {}

    def AddDevice(self, axis):
        self._log.debug('AddDevice entering...')
        self.attributes[axis] = {'step_per_unit': 1.0,
                                 'base_rate': 0,
                                 'acceleration': 0,
                                 'velocity': 1}
    def DeleteDevice(self, axis):
        self.attributes[axis] = None


    def ReadOne(self, axis):
        self._log.debug("In ReadOne axis %d" % axis)
        """Get the motor position"""
        try:
            state = self._opusds.state()
            while state is not PyTango.DevState.ON:
                time.sleep(0.1)
                state = self._opusds.state()
            self._log.debug("Opus state %s" % str(state))
            if state is PyTango.DevState.ON:
                cmd = "send_serial_cmd ?pos {0}".format(self.attributes[axis]["axis_name"])
                ans = self._opusds.runOpusCMDSync(cmd)
                #while self._opusds.state() is PyTango.DevState.ON:
                #    time.sleep(0.05)
                #pos = float(self._opusds.getLastOpusOutput())
                pos = float(ans)
        except Exception as e:
            self._log.debug("Error in ReadOne: %s" % e)
            pos = float('INF')
        self._log.debug("Out ReadOne axis %d [%s]" % (axis, str(pos)))
        return pos

    def StateOne(self, axis):
        """Get the specified motor state"""
        self._log.debug("StateOne...")
        state = self._opusds.state()
        if state is PyTango.DevState.ON:
            cmd = "send_serial_cmd ?statusaxis {0}".format(
                self.attributes[axis]["axis_name"])
            try:
                ans = self._opusds.runOpusCMDSync(cmd)
                # @ => Axis is not moving and ready
                # M => Axis is moving
                # J => Axis is ready and may also be controlled manually (by joystick)
                # S => Limit switches are actuated and prevent further automatic move
                # A => ok response after cal instruction
                # D => ok response after rm instruction
                # E => error response, move aborted or not executed (e.g. cal or rm error, or stop input active)
                # T => Timeout occurred (refer to 'caltimeout' instruction)
                # - => Axis is not enabled, not available in hardware
                if 'M' in ans:
                    state = State.Moving
                elif 'E' in ans:
                    state = State.Fault
                elif 'T' in ans:
                    state = State.Fault
                elif '-' in ans:
                    state = State.Fault
                else:
                    state = State.On
            except:
                state = State.Fault
        elif state is PyTango.DevState.RUNNING:
            state = State.Moving
        elif state is PyTango.DevState.ALARM:
            state = State.Fault
        status = self._opusds.status()
        self._log.debug("StateOne... {0}, {1}".format(state, status))
        return state, status

    def StartOne(self, axis, position):
        """Move the motor to the specified position"""
        self._opusds.runOpusCMDSync("send_serial_cmd !go {0} {1}".format(
            self.attributes[axis]["axis_name"], position))

    def StopOne(self, axis):
        """Stop the specified motor"""
        self._opusds.runOpusCMDSync("send_serial_cmd ?abort {0}".format(
            self.attributes[axis]["axis_name"]))


    def SetAxisExtraPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        name = name.lower()
        if name == "velocity":
            self.attributes[axis]["velocity"] = float(value)
        elif name == "acceleration":
            self.attributes[axis]["acceleration"] = float(value)
        elif name == "deceleration":
            self.attributes[axis]["deceleration"] = float(value)
        elif name == "step_per_unit":
            self.attributes[axis]["step_per_unit"] = float(value)
        elif name == "base_rate":
            self.attributes[axis]["base_rate"] = float(value)
        elif name.lower() == "axis_name":
            self.attributes[axis]["axis_name"] = value

    def GetAxisExtraPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        name = name.lower()
        if name == 'velocity':
            value = self.attributes[axis]['velocity'] / self.attributes[
                axis]['step_per_unit']

        elif name in ['acceleration', 'deceleration']:
            value = self.attributes[axis]['acceleration']

        elif name == "step_per_unit":
            value = self.attributes[axis]["step_per_unit"]
        elif name == "base_rate":
            value = self.attributes[axis]["base_rate"]
        elif name.lower() == "axis_name":
            value = self.attributes[axis]["axis_name"]


        return value

