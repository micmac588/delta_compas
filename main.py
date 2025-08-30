#!/usr/bin/env python3
import argparse
import datetime
import logging
import numpy as np
import os
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pynmea2

from tqdm import *
from queue import Queue

MIN_SPEED = 6
INVALID_HEADING = 1000
INVALIDE_ROTATION_SPEED = 0
INTEGRATION_DURATION = 1

class Elem():
    def __init__(self, date, second, heading, bottom_heading, rotation_speed, sog):
        self._date = date
        self._second = second    # TODO not necessary to store this.
        self._heading = heading
        self._rotation_speed = rotation_speed
        self._bottom_heading = bottom_heading
        self._sog = sog

    def __str__(self):
        return f"heading {self._heading} / bottom heading {self._bottom_heading} / rotation speed {self._rotation_speed} at {self._date}"

def prepare_logger(logger_name, verbosity, log_file=None):
    """Initialize and set the logger.

    :param logger_name: the name of the logger to create
    :type logger_name: string
    :param verbosity: verbosity level: 0 -> default, 1 -> info, 2 -> debug
    :type  verbosity: int
    :param log_file: if not None, file where to save the logs.
    :type  log_file: string (path)
    :return: a configured logger
    :rtype: logging.Logger
    """

    logging.getLogger('parse').setLevel(logging.ERROR)

    logger = logging.getLogger(logger_name)

    log_level = logging.WARNING - (verbosity * 10)
    log_format = "[%(filename)-30s:%(lineno)-4d][%(levelname)-7s] %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    # create and add file logger
    if log_file:
        formatter = logging.Formatter(log_format)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

def get_delta_heading(bottom_heading, compass_heading):
    '''
    Calculate the difference beetween bottom_heading and compass_heading
    '''
    
    delta_heading = bottom_heading - compass_heading
    if delta_heading > 180:
        delta_heading = 360 - delta_heading
    if delta_heading < -180:
        delta_heading = 360 + delta_heading
    return delta_heading

def get_rotation_speed(elems, current_heading, current_second):
    for elem in elems:
        if (current_second - elem._second) >= INTEGRATION_DURATION:
            return abs(get_delta_heading(current_heading, elem._heading) / (current_second - elem._second))
    return INVALIDE_ROTATION_SPEED

def plot_data(elems, logger):
    heading = []
    time = []
    rotation_speed = []
    bottom_heading = []
    sog = []
    for elem in elems:
        time.append(elem._date)
        heading.append(elem._heading)
        rotation_speed.append(elem._rotation_speed)
        bottom_heading.append(elem._bottom_heading)
        sog.append(elem._sog)
    xpoints = np.array(time)
    ypoints = np.array(heading)
    y2points = np.array(rotation_speed)
    y3points = np.array(bottom_heading)
    y4points = np.array(sog)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gca().plot(xpoints, ypoints, label = 'heading', color = 'purple')
    plt.gca().plot(xpoints, y2points, label = 'rotation speed', color = 'red')
    plt.gca().plot(xpoints, y3points, label = 'bottom heading', color = 'green')
    # plt.plot(xpoints, y4points, label = 'speed over ground', color = 'blue')
    plt.legend()
    plt.show()

def parse_file(inputfile, logger):
    bottom_heading = INVALID_HEADING
    compass_heading = INVALID_HEADING
    line_counter = 0
    rotation_speed = 0
    sog = 0
    fail = 0
    elems = []

    with tqdm(total=os.path.getsize(inputfile)) as pbar:
        with open(inputfile, "r") as fi:
            for line in fi:
                line_counter +=1
                pbar.update(len(line))
                try:
                    msg = pynmea2.parse(line[12:], check=True)
                    #msg = pynmea2.parse(line, check=True)
                    try:
                        if not hasattr(msg, 'sentence_type'):
                            # $PNKEP (proprietary sentence has no attribute sentence_type)
                            # see https://www.hisse-et-oh.com/sailing/canaux-performances-de-maxsea-sur-tl-25-nke
                            fail += 1
                            continue
                        if msg.sentence_type == 'VTG':
                            try:
                                int(msg.true_track)
                            except Exception as e:
                                fail += 1
                                continue
                            try:
                                float(msg.spd_over_grnd_kts)
                            except Exception as e:
                                fail += 1
                                continue
                            bottom_heading = msg.true_track
                            if bottom_heading > 360:
                                fail += 1
                                continue
                            sog = msg.spd_over_grnd_kts
                            logger.info(f"bottom_heading {bottom_heading}")
                        elif msg.sentence_type =='VHW':
                            compass_heading = msg.heading_true  # msg.heading_magnetic
                            if compass_heading > 360:
                                compass_heading=INVALID_HEADING 
                                fail += 1
                                continue
                            logger.info(f"compass_heading {compass_heading}")
                        elif msg.sentence_type == 'ZDA':
                            logger.info(f"ZDA {repr(msg)}")
                            if msg.talker == 'GP':
                                # do not use GPZDA, use IIZDA instead
                                continue
                            try:
                                date = datetime.datetime(msg.year, msg.month, msg.day,
                                                        msg.timestamp.hour,
                                                        msg.timestamp.minute,
                                                        msg.timestamp.second)
                            except Exception as e:
                                logger.error(f'Wrong date/time is {repr(msg)} : {e}')
                                fail += 1
                                continue
                            logger.info(f"{date} at {line_counter}")
                            current_second = int(date.timestamp()) # epoch time
                            if len(elems) and date < elems[len(elems)-1]._date:
                                #  ZDA has wrong value sometime
                                logger.error(f'Current date < previous date in {repr(msg)}')
                                fail += 1
                                continue
                            rotation_speed = get_rotation_speed(elems, compass_heading, current_second)
                            if compass_heading!=INVALID_HEADING and bottom_heading!=INVALID_HEADING:
                                elems.insert(0, Elem(date, current_second, compass_heading, bottom_heading, rotation_speed, sog))
                        else:
                            continue
                            
                    except Exception as e:
                        logger.error(f'{e} for {line}, {repr(msg)}')
                        fail += 1
                        continue
                except pynmea2.ParseError as e:
                    fail += 1
                    continue
    logger.info(f"failures: {fail/line_counter*100}%")
    return elems

def open_output_file(inputfile, line, previous_fo):
    # look for something like 04/02/2024 07:23:58  - Debut
    pattern = r'(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2}):(\d{2})  - Debut'
    result = re.search(pattern, line)
    if result is None:
        # return the previous file descriptor
        return previous_fo
    if previous_fo:
        previous_fo.close()  # close the previous
    result = re.search(pattern, line)
    day = result.group(1)
    month = result.group(2)
    year = result.group(3)
    hour = result.group(4)
    minute = result.group(5)
    second = result.group(6)
    outputfile = inputfile.split('.')[0] + day + month + year + hour + minute + second + '.log'
    fo = open(outputfile, 'x') # open the new one
    return fo
                
def split(inputfile, logger):
    # Split the log file when it has several 'Debut'
    line_counter = 0
    fail = 0
    fo = None
    with tqdm(total=os.path.getsize(inputfile)) as pbar:
        with open(inputfile, "r") as fi:
            try:
                for line in fi:
                    line_counter +=1
                    pbar.update(len(line))

                    fo = open_output_file(inputfile, line, fo)
                    if fo:
                        fo.write(line)
                    
            except Exception as e:
                print(e)
                fail +=1

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", help="the nmea log file.", required=True)
    parser.add_argument("-s", "--split", action="store_true", help="split input file", required=False)
    parser.add_argument("-d", "--deltacompas", action="store_true", help="plot bottom heading and compas heading", required=False)
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase the verbosity", required=False)
    parser.add_argument("-l", "--logfile", help="log file name", required=False)

    args = parser.parse_args()

    logger = prepare_logger("nmea_parser", args.verbosity, args.logfile)

    if args.split:
        logger.info(f"Start splitting of {args.inputfile}")
        split(args.inputfile, logger)

    elif args.deltacompas:
        logger.info(f"Start parsing of {args.inputfile}")
        elems = parse_file(args.inputfile,logger)
        logger.info(f"End of parsing {args.inputfile}")

        logger.info(f"Start plotting")
        if elems is None or len(elems) == 0:
            logger.warning("Nothing to plot")
            exit(-1)
        plot_data(elems, logger)
        logger.info(f"End of plotting")


if __name__ == "__main__":
    main()
