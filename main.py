#!/usr/bin/env python3
import argparse
import logging
import multiprocessing
import threading

from nmea_parser import NmeaParser
from scatter_plotter import ScatterPlotter

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


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", help="the nmea log file.", required=True)
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase the verbosity", required=False)
    parser.add_argument("-l", "--logfile", help="log file name", required=False)

    args = parser.parse_args()

    logger = prepare_logger("nmea_parser", args.verbosity, args.logfile)

    queue_delta_heading = multiprocessing.Queue()
    plotter_delta_heading = ScatterPlotter(queue_delta_heading)
    np = NmeaParser(args.inputfile, queue_delta_heading, logger)

    plotter_delta_heading.start()

    parser = threading.Thread(target=np.run)
    parser.start()
    parser.join()
    logger.info("End of parsing %s", args.inputfile)
    plotter_delta_heading.join()
    

if __name__ == "__main__":
    main()
