from nmea_payload import NmeaPayload

class Iivwr(NmeaPayload):

    def __init__(self,date, hour, payload, logger):
        NmeaPayload.__init__(self, date, hour, logger)
        self.__process_iivwr(payload)

    def __process_iivwr(self, payload):
        '''
        Return awa aws from IIVWR sentence

        $IIVWR,x.x,a,x.x,N,x.x,M,x.x,K*hh
        '''
        self.__awa = None
        self.__aws = None
        try:
            self.__awa = -float(payload[payload.index("R")-1])
        except ValueError:
            try:
                self.__awa = float(payload[payload.index("L")-1])
            except ValueError:
                self._logger.warning("awa not available in sentence %s" % payload)
        try:
            self.__aws = float(payload[payload.index("N")-1])
        except ValueError:
            self._logger.warning("aws not available in sentence %s" % payload)

    @property
    def awa(self):
        return self.__awa
    
    @property
    def aws(self):
        return self.__aws
