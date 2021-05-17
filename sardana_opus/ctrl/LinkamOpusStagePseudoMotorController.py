from sardana.pool.controller import (PseudoMotorController,
                                     Type,
                                     Access,
                                     Description,
                                     DefaultValue)
from sardana import State, DataAccess

class LinkamOpusStagePseudoMotorController(PseudoMotorController):

    motor_roles = "linkam", "opus_x", "opus_y", "opus_z"

    axis_attributes = {'x_factor': {Type: float,
                                   Access: DataAccess.ReadWrite,
                                   Description: ''},
                       'y_factor': {Type: float,
                                   Access: DataAccess.ReadWrite,
                                   Description: ''},
                       'z_factor': {Type: float,
                                   Access: DataAccess.ReadWrite,
                                   Description: ''},
                       }

    factors = {1: 0.34743,
               2: 0.12602,
               3: 0.43009
               }

    def CalcPhysical(self, index, pseudo_pos, curr_physical_pos):
        if index == 1:
            return pseudo_pos[0]

        temp_variation = abs(curr_physical_pos[0] - pseudo_pos[0])
        sign = 1
        if pseudo_pos[0] < curr_physical_pos[0]:
            sign = -1
        curr_pos = curr_physical_pos[index - 1]
        return curr_pos + self.factors[index - 1] * temp_variation * sign

    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
        return physical_pos[0]

    def SetAxisExtraPar(self, axis, parameter, value):
        if parameter == 'x_factor':
            index = 1
        elif parameter == 'y_factor':
            index = 2
        elif parameter == 'z_factor':
            index = 3
        self.factors[index] = value

    def GetAxisExtraPar(self, axis, parameter):
        if parameter == 'x_factor':
            index = 1
        elif parameter == 'y_factor':
            index = 2
        elif parameter == 'z_factor':
            index = 3

        return self.factors[index]
