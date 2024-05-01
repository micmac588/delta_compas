#!/usr/bin/env python3
import argparse
import logging
import multiprocessing
import numpy as np
import os
import threading
import matplotlib.pyplot as plt
import pynmea2

from scatter_plotter import ScatterPlotter
from tqdm import *
from queue import Queue

MIN_SPEED = 6
INVALID_HEADING = 1000
INVALIDE_ROTATION_SPEED = 0
INTEGRATION_DURATION =  5

class Elem():
    def __init__(self, second, heading, bottom_heading, rotation_speed, sog):
        self._second = second
        self._heading = heading
        self._rotation_speed = rotation_speed
        self._bottom_heading = bottom_heading
        self._sog = sog

    def __str__(self):
        return f"heading {self._heading} / bottom heading {self._bottom_heading} / rotation speed {self._rotation_speed} at {self._second}"

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

def get_rotation_speed(heading_array):
    if len(heading_array) < INTEGRATION_DURATION:
        return INVALIDE_ROTATION_SPEED
    first = heading_array[0]
    last = heading_array[INTEGRATION_DURATION-1]
    if (last._second - first._second) == 0:
        return INVALIDE_ROTATION_SPEED

    return abs(get_delta_heading(last._heading, first._heading) / (last._second - first._second))

def plot_data(elems):
    heading = []
    time = []
    rotation_speed = []
    bottom_heading = []
    sog = []
    for elem in elems:
        time.append(elem._second)
        heading.append(elem._heading)
        rotation_speed.append(elem._rotation_speed)
        bottom_heading.append(elem._bottom_heading)
        sog.append(elem._sog)
    xpoints = np.array(time)
    ypoints = np.array(heading)
    y2points = np.array(rotation_speed)
    y3points = np.array(bottom_heading)
    y4points = np.array(sog)
    plt.plot(xpoints, ypoints, label = 'heading', color = 'purple')
    plt.plot(xpoints, y2points, label = 'rotation speed', color = 'red')
    plt.plot(xpoints, y3points, label = 'bottom heading', color = 'green')
    plt.plot(xpoints, y4points, label = 'speed over ground', color = 'blue')
    plt.legend()
    plt.show()

def parse_file(inputfile, queue_delta_heading):
    bottom_heading = INVALID_HEADING
    compass_heading = INVALID_HEADING
    line_counter = 0
    rotation_speed = 0
    sog = 0
    fail = 0
    seconds = 0
    elems = []
    max_rotation_speed = 0
    time_base = 0

    with tqdm(total=os.path.getsize(inputfile)) as pbar:
        with open(inputfile, "r") as fi:
            #queue_delta_heading.put(['Start', inputfile, 'delta heading', 'heading'])
            for line in fi:
                line_counter +=1
                pbar.update(len(line))
                try:
                    msg = pynmea2.parse(line[12:], check=True)
                    #msg = pynmea2.parse(line, check=True)
                    try:
                        if msg.sentence_type == 'VTG':
                            bottom_heading = msg.true_track
                            sog = msg.spd_over_grnd_kts
                        elif msg.sentence_type =='VHW':
                            compass_heading = msg.heading_true  # msg.heading_magnetic
                        elif msg.sentence_type == 'ZDA':
                            t = msg.timestamp
                            if time_base == 0:
                                time_base = (t.hour * 60 + t.minute) * 60 + t.second
                            if time_base > (t.hour * 60 + t.minute) * 60 + t.second:
                                continue  #  ZDA has wrong value sometime
                            seconds = (t.hour * 60 + t.minute) * 60 + t.second - time_base
                            rotation_speed = get_rotation_speed(elems) # TODO devrait être calculé avec les données courantes.
                            if compass_heading!=INVALID_HEADING and bottom_heading!=INVALID_HEADING:
                                elems.insert(0, Elem(seconds, compass_heading, bottom_heading, rotation_speed, sog))
                        else:
                            continue
                            
                    except Exception as e:
                        #print(e)
                        continue
                except pynmea2.ParseError as e:
                    #print('Parse error: {}'.format(e))
                    fail += 1
                    continue

            plot_data(elems)
        
            #queue_delta_heading.put(['Stop',])


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", help="the nmea log file.", required=True)
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase the verbosity", required=False)
    parser.add_argument("-l", "--logfile", help="log file name", required=False)

    args = parser.parse_args()

    logger = prepare_logger("nmea_parser", args.verbosity, args.logfile)
    queue_delta_heading = multiprocessing.Queue()
    #plotter_delta_heading = ScatterPlotter(queue_delta_heading, logger)

    #plotter_delta_heading.start()

    logger.info(f"Start parsing of {args.inputfile}")
    parse_file(args.inputfile, queue_delta_heading)
    # parser = threading.Thread(target=parse_file, args=(args.inputfile, queue_delta_heading))
    # parser.start()
    # parser.join()
    logger.info(f"End of parsing {args.inputfile}")
    #plotter_delta_heading.join()
    logger.info(f"End of plotting")


    

if __name__ == "__main__":
    main()
