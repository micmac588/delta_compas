from nmea_payload import NmeaPayload

class Iivhw(NmeaPayload):

    def __init__(self,date, hour, payload, logger):
        NmeaPayload.__init__(self, date, hour, logger)
        self.__process_iivhw(payload)

    def __process_iivhw(self, payload):
        '''
        Return true_compass_heading, magnetic_compass_heading, 
        surface_speed_knots, surface_speed_kph from IIVHW sentence

        IIVHW 109.2,T,101,M,2.01,N,3.73,K*45
        '''
        self.__true_compass_heading = None
        self.__magnetic_compass_heading = None
        self.__surface_speed_knots = None
        self.__surface_speed_kph = None
        try:
            self.__true_compass_heading = float(payload[payload.index("T")-1])
        except ValueError as e:
            self._logger.warning("true_compass_heading not available in sentence %s" % payload)
        try:
            self.__magnetic_compass_heading = float(payload[payload.index("M")-1])
        except ValueError as e:
            self._logger.warning("magnetic_compass_heading not available in sentence %s" % payload)
        try:
            self.__surface_speed_knots = float(payload[payload.index("N")-1])
        except ValueError:
            self._logger.warning("surface_speed_knots not available in sentence %s" % payload)
        try:
            self.__surface_speed_kph = float(payload[payload.index("K")-1])
        except ValueError:
            pass

    @property
    def true_compass_heading(self):
        return self.__true_compass_heading
    
    @property
    def magnetic_compass_heading(self):
        return self.__magnetic_compass_heading
    
    @property
    def surface_speed_knots(self):
        return self.__surface_speed_knots
    
    @property
    def surface_speed_kph(self):
        return self.__surface_speed_kph
