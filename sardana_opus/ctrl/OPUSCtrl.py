#!/usr/bin/env python

import time
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description

class OPUSCtrl(CounterTimerController):

    MaxDevice = 1

    axis_attributes = {"file": {Type: str,
                                Description: 'File',
                                Access: DataAccess.ReadWrite
                                },
                       }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._integ_time = self._start_time = time.time()
        self._file = None

    def ReadOne(self, axis):
        self._log.debug("ReadOne... (%s) ", self._file)
        with open(self._file, 'r') as f:
            value = f.readline()
        return int(value)

    def StateOne(self, ind):
        now = time.time()
        elapsed_time = now - self._start_time
        if self._integ_time and elapsed_time < self._integ_time:
            sta = State.Moving
            status = "Acquiring"
        else:
            sta = State.On
            status = "On"
        return sta, status

    def StartAll(self):
        self._log.debug("StartAll")
        self._start_time = time.time()

    def LoadOne(self, ind, value, repetitions, latency):
        self._integ_time = value

    def AbortOne(self, ind):
        self._integ_time = None

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == "file":
            return self._file

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == "file":
            self._file = value
