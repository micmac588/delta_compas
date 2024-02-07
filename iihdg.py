from nmea_payload import NmeaPayload

class Iihdg(NmeaPayload):

    def __init__(self,date, hour, payload, logger):
        NmeaPayload.__init__(self, date, hour, logger)
        self.__process_iihdg(payload)

    def __process_iihdg(self, payload):
        # IIHDG,32,,,,*66
        self.__heading_magnetic = None
        try:
            self.__heading_magnetic = int(payload[0])
        except ValueError:
            try:
                self.__heading_magnetic = float(payload[0])    # it is a float on Tahuret
            except ValueError:
                self._logger.warning("heading_magnetic not available in sentence %s" % payload)
        return self.__heading_magnetic

    @property
    def heading_magnetic(self):
        return self.__heading_magnetic
    
    def __str__(self):
        return self.heading_magnetic
