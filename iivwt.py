from nmea_payload import NmeaPayload

class Iivwt(NmeaPayload):

    def __init__(self,date, hour, payload, logger):
        NmeaPayload.__init__(self, date, hour, logger)
        self.__process_iivwt(payload)

    def __process_iivwt(self, payload):
        '''
        Return twa, tws from IIVWT sentence

        $IIVWT,x.x,a,x.x,N,x.x,M,x.x,K*hh
        '''
        self.__twa = None
        self.__tws = None
        try:
            self.__twa = payload[payload.index("R")-1]
        except ValueError:
            try:
                self.__twa = payload[payload.index("L")-1]
            except ValueError:
                self._logger.warning("twa not available in sentence %s" % payload)
        try:
            self.__tws = payload[payload.index("N")-1]
        except ValueError:
            self._logger.warning("tws not available in sentence %s" % payload)

    @property
    def twa(self):
        return self.__twa
    
    @property
    def tws(self):
        return self.__tws
