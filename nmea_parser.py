import csv
import datetime
from parse import parse
import time

from iivhw import Iivhw
from iivwr import Iivwr
from iimwd import Iimwd
from iivwt import Iivwt
from iihdg import Iihdg
from iivtg import Iivtg

class NmeaParser():

    TIME_SLOT = 2
    MIN_SPEED = 5

    def __init__(self, inputfile, queue_delta_heading, logger):
        self.__logger = logger
        self.__inputfile = inputfile
        self.__queue_delta_heading = queue_delta_heading
        self.__start_time = None
        self.__iivhw = None
        self.__iivwr = None
        self.__iimwd = None
        self.__iivwt = None
        self.__iihdg = None
        self.__iivtg = None
        self.__current_date = None
    
    def __assert_checksum(self, line):
        '''
        Check the checksum in line
        '''
        p = parse("{hours}:{minutes}:{seconds}:{ds} ${sentence}*{checksum}", line)
        if p:
            sentence = p["sentence"]
            checksum = p["checksum"]
            cs = 0
            for i, char in enumerate(sentence):
                cs = cs ^ ord(char)
            if cs != int(checksum, 16):
                raise Exception(f"expected checksum {int(checksum, 16)}, calculate {cs}")

    def __parse_sentence(self, line):
        '''
        '''
        try:
            self.__assert_checksum(line)
        except Exception as e:
            self.__logger.warn(f"Invalid checksum in {line}: {e}")
            return None, None, None, None

        p = parse("{hours}:{minutes}:{seconds}:{ds} ${sentence_id},{payload}*{checksum}", line)
        if p:
            hour = "%s:%s:%s" % (p["hours"],p["minutes"],p["seconds"])
            epoch_time = time.mktime(time.strptime("%s %s" % (self.__current_date, hour), "%d/%m/%Y %H:%M:%S"))
            current_second = p["seconds"]
            sentence_id = p["sentence_id"]
            payload = p["payload"].split(',')
            return hour, epoch_time, sentence_id, payload
  
        # 09/08/2021 16:13:06  - Debut\n
        p = parse("{day}/{month}/{year} {hours}:{minutes}:{seconds}  - Debut\n", line)
        if p:
            self.__current_date = "%s/%s/%s" % (p["day"],p["month"],p["year"])
            hour = "%s:%s:%s" % (p["hours"], p["minutes"], p["seconds"])
            epoch_time = time.mktime(time.strptime("%s %s" % (self.__current_date, hour), "%d/%m/%Y %H:%M:%S"))
            
            return hour, epoch_time, None, None
        
        return None, None, None, None

    def __get_delta_heading(self):
        '''
        Calculate the difference beetween true_bottom_heading and true_compass_heading
        When the speed is too low (< MIN_SPEED) return None
        '''
        if not self.__iivtg.bottom_speed_knots or not self.__iivtg.true_bottom_heading or not self.__iivhw.true_compass_heading:
            return None, None
        
        if self.__iivtg.bottom_speed_knots < self.MIN_SPEED:
            return None, None
        
        delta_heading = self.__iivtg.true_bottom_heading - self.__iivhw.true_compass_heading
        if delta_heading > 180:
            delta_heading = 360 - delta_heading
        if delta_heading < -180:
            delta_heading = 360 + delta_heading
        return delta_heading, self.__iivtg.true_bottom_heading


    def __get_declinaison(self):
        if self.__iivhw.true_compass_heading and self.__iivhw.magnetic_compass_heading:
            return self.__iivhw.true_compass_heading - self.__iivhw.magnetic_compass_heading
        return None
    
    def __get_delta_speed(self):
        '''
        Calculate the difference beetween bottom_speed_knots and surface_speed_knots
        When the speed is too low (< MIN_SPEED) return None
        '''
        if not self.__iivtg.bottom_speed_knots or not self.__iivtg.bottom_speed_knots or not self.__iivhw.surface_speed_knots:
            return None
        if self.__iivtg.bottom_speed_knots < self.MIN_SPEED:
            return None
        return self.__iivtg.bottom_speed_knots - self.__iivhw.surface_speed_knots

    def run(self):
        count = 0
        with open(self.__inputfile, "r") as fi:
            self.__queue_delta_heading.put(['Start', self.__inputfile, 'delta heading', 'heading'])
            for line in fi:
                hour, current_time, sentence_id, payload = self.__parse_sentence(line)

                if not hour or not current_time:
                    continue

                if not self.__start_time:
                    self.__start_time = current_time

                # Surface speed and compass heading:
                if sentence_id == "IIVHW":
                    self.__iivhw = Iivhw(self.__current_date, hour, payload, self.__logger)
                # Apparent wind angle and speed:
                elif sentence_id == "IIVWR":
                    self.__iivwr = Iivwr(self.__current_date, hour, payload, self.__logger)
                # True wind direction and speed
                elif sentence_id == "IIMWD":
                    self.__iimwd = Iimwd(self.__current_date, hour, payload, self.__logger)
                elif sentence_id == "IIVWT":
                    self.__iivwt = Iivwt(self.__current_date, hour, payload, self.__logger)
                # Heading magnetic:
                elif sentence_id == "IIHDG":   # compass 9X
                    self.__iihdg = Iihdg(self.__current_date, hour, payload, self.__logger)
                # Bottom heading and speed
                elif sentence_id == "IIVTG":   # gps HR
                    self.__iivtg = Iivtg(self.__current_date, hour, payload, self.__logger)

                # check all data are read
                if not self.__iivhw or not self.__iivtg:
                    if (current_time - self.__start_time) > self.TIME_SLOT:
                        self.__logger.warn("Time slot duration reached whereas data are not available at %s" % datetime.datetime.fromtimestamp(current_time))
                        self.__start_time = current_time
                        self.__iivhw = None
                        self.__iivwr = None
                        self.__iimwd = None
                        self.__iivwt = None
                        self.__iihdg = None
                        self.__iivtg = None
                    continue

                if (current_time - self.__start_time) > self.TIME_SLOT:
                    self.__start_time = current_time
                    declinaison = self.__get_declinaison()
                    # self.__logger.info("declinaison: %s at %s" % (declinaison, datetime.datetime.fromtimestamp(current_time)))
                    delta_heading, heading = self.__get_delta_heading()
                    if delta_heading:
                        self.__queue_delta_heading.put([delta_heading, heading])
                    delta_speed = self.__get_delta_speed()
                    # self.__logger.info("delta_speed: %s at %s" % (delta_speed, datetime.datetime.fromtimestamp(current_time)))
                    self.__iivhw = None
                    self.__iivwr = None
                    self.__iimwd = None
                    self.__iivwt = None
                    self.__iihdg = None
                    self.__iivtg = None

            self.__queue_delta_heading.put(['Stop',])


"""                 count = count + 1
                if count == 1000000:
                    raise Exception("Max reached") """
            