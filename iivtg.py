from nmea_payload import NmeaPayload

class Iivtg(NmeaPayload):

    def __init__(self,date, hour, payload, logger):
        NmeaPayload.__init__(self, date, hour, logger)
        self.__process_iivtg(payload)

    def __process_iivtg(self, payload):
        # IIVTG 20,T,,M,5.43,N,10.06,K,A*03

        self.__true_bottom_heading = None
        self.__magnetic_bottom_heading = None
        self.__bottom_speed_knots = None
        self.__bottom_speed_kph = None
        try:
            self.__true_bottom_heading = float(payload[payload.index("T")-1])
        except ValueError:
            try:
                self.__true_bottom_heading = float(payload[payload.index("T")-1])  # it is a float on Tahuret
            except ValueError:
                self._logger.warning("true_bottom_heading not available in sentence %s" % payload)
        try:
            self.__magnetic_bottom_heading = float(payload[payload.index("M")-1])
        except ValueError:
            pass
            #self._logger.debug("magnetic_bottom_heading not available in sentence %s" % payload)
        try:
            self.__bottom_speed_knots = float(payload[payload.index("N")-1])
        except ValueError:
            self._logger.warning("bottom_speed_knots not available in sentence %s" % payload)
        try:
            self.__bottom_speed_kph = float(payload[payload.index("K")-1])
        except ValueError:
            self._logger.warning("bottom_speed_kph not available in sentence %s" % payload)

    @property
    def true_bottom_heading(self):
        return self.__true_bottom_heading
    
    @property
    def magnetic_bottom_heading(self):
        return self.__magnetic_bottom_heading
    
    @property
    def bottom_speed_knots(self):
        return self.__bottom_speed_knots
    
    @property
    def bottom_speed_kph(self):
        return self.__bottom_speed_kph
