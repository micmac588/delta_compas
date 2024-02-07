from nmea_payload import NmeaPayload

class Iimwd(NmeaPayload):

    def __init__(self,date, hour, payload, logger):
        NmeaPayload.__init__(self, date, hour, logger)
        self.__process_iimwd(payload)

    def __process_iimwd(self, payload):
        '''
        Return twd, twd_mag, tws from IIMWD sentence

        $IIMWD,x.x,T,x.x,M,x.x,N,x.x,M*hh
        '''
        self.__twd = None
        self.__twd_mag = None
        self.__tws = None
        try:
            self.__twd = payload[payload.index("T")-1]
        except:
            # not always present on Tahuret
            pass
        try:
            self.__twd_mag = payload[payload.index("M")-1]
        except ValueError:
            self._logger.warning("twd_mag not available in sentence %s" % payload)
        try:
            self.__tws = payload[payload.index("N")-1]
        except ValueError:
            self._logger.warning("tws not available in sentence %s" % payload)

    @property
    def twd(self):
        return self.__twd
    
    @property
    def twd_mag(self):
        return self.__twd_mag
    
    @property
    def tws(self):
        return self.__tws
