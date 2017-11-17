import time
import socket

from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description, DefaultValue


class OPUSSocketCtrl(CounterTimerController):

    MaxDevice = 1

    ctrl_properties = {
                       "ip": {Type: str,
                              Description: 'IP where the OPUS server is run',
                              DefaultValue: "bl01bruker"
                              },
    }

    axis_attributes = {
                       "opus_macro_name": {Type: str,
                                           Description: 'OPUS macro',
                                           Access: DataAccess.ReadWrite
                                           },
                      "read_peak": {Type: bool,
                                    Description: 'Read the scan PKA',
                                    Access: DataAccess.ReadWrite
                                    },
                       }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        # id of the current macro
        self._macro_id = None
        self.server_address = (self.ip, 5000)
        # Connect socket
        self.sock = None
        self._connectSocket()

    def _connectSocket(self):
        if self.sock is None:
            # create socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1)
        try:
            self.sock.connect(self.server_address)
            self.isConnected = True
            self._state = State.On
        except:
            self.isConnected = False
            self._log.debug("There is any problem to connect with the server")

    def _reconnectSocket(self):
        self.sock.close()
        self.sock = None
        self._connectSocket()

    def _runOPUScmd(self, cmd):
        self.sock.sendall(cmd + '\n')
        ans = self.sock.recv(4096)
        return ans

    def ReadOne(self, ind):
        self._log.debug("ReadOne...")
        value = None
        if self._read_peak:
            # TODO
            value = None
        return value

    def StateOne(self, ind):
        status = "On"
        if self._state == State.Moving and self._macro_id is not None:
            status = "Acquiring"
            cmd = "MACRO_RESULTS {0}".format(self._macro_id)
            ans = self._runOPUScmd(cmd)
            if 'OK\n' in ans.upper():
                if int(ans.split('\n')[1]) == 1:
                    self._state = State.On
                    status = "On"
            else:
                self._state = State.Fault
                status = "Error reading macro status"
        elif self._state == State.Fault:
            status = 'Can not connect with the server'
        return self._state, status

    def StartAll(self):
        self._log.debug("StartAll")

    def PreStartOne(self, axis, value=None):
        try:
            # Evaluate the connection
            self._runOPUScmd('s_pipe\n')
        except:
            # Try to reconnect the socket
            self._reconnectSocket()
        return self.isConnected

    def StartOne(self, axis, value=None):
        self._log.debug("StartOne")
        if self.isConnected:
            cmd = "RUN_MACRO {0}".format(self._opus_macro_name)
            ans = self._runOPUScmd(cmd)
            if "OK\n" in ans.upper():
                self._macro_id = ans.split('\n')[1]
                self._state = State.Moving
            else:
                self._state = State.Fault
                self._macro_id = None
        else:
            self._state = State.Fault

    def LoadOne(self, ind, value):
        pass

    def AbortOne(self, ind):
        if self._macro_id and self._state == State.Running:
            cmd = "KILL_MACRO {0}".format(self._macro_id)
            self._runOPUScmd(cmd)
        self._macro_id = None
        self._state = State.On

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == "ip":
            return self._ip
        elif name.lower() == "opus_macro_name":
            return self._opus_macro_name
        elif name.lower() == "read_peak":
            return self._read_peak

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == "ip":
            self._ip = value
        elif name.lower() == "opus_macro_name":
            self._opus_macro_name = value
        elif name.lower() == "read_peak":
            self._read_peak = value