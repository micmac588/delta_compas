#!/usr/bin/env python3
import argparse
import csv
import logging
from parse import parse

bottom_speed_knots = 0
heading_magnetic = 0
true_bottom_heading = 0
magnetic_bottom_heading = 0
true_compass_heading = 0
magnetic_compass_heading = 0
surface_speed_knots = 0

def str2int(value):
    if not value:
        return 0
    else:
        return int(value)

def str2float(value):
    if not value:
        return "0"
    else:
        return value

def reset_measures():
    global bottom_speed_knots
    global heading_magnetic
    global true_bottom_heading
    global magnetic_bottom_heading
    global true_compass_heading
    global magnetic_compass_heading
    global surface_speed_knots

    bottom_speed_knots = 0
    heading_magnetic = 0
    true_bottom_heading = 0
    magnetic_bottom_heading = 0
    true_compass_heading = 0
    magnetic_compass_heading = 0
    surface_speed_knots = 0


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

    global bottom_speed_knots
    global heading_magnetic
    global true_bottom_heading
    global magnetic_bottom_heading
    global true_compass_heading
    global magnetic_compass_heading
    global surface_speed_knots

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", help="your bank account historic csv file.", required=True)
    parser.add_argument("-o", "--outputfile", help="The HomeBank csv file.", required=False, default="homebank.csv")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase the verbosity", required=False)
    parser.add_argument("-l", "--logfile", help="log file name", required=False)

    args = parser.parse_args()

    logger = prepare_logger("nmea_parser", args.verbosity, args.logfile)

    with open(args.inputfile, "r") as fi:
        with open(args.outputfile, "w") as fo:
            
            ocsv = csv.writer(fo, delimiter=';')

            ocsv.writerow(("date","true_bottom_heading","delta_heading","bottom_speed_knots", "delta_speed"))

            true_bottom_heading_measures = 0
            true_bottom_heading_error_count = 0
            heading_magnetic_measures = 0
            heading_magnetic_error_count = 0

            reset_measures()

            for line in fi:
                logger.debug(line)
                p = parse("{hours}:{minutes}:{seconds}:{ds} ${sentence_id},{payload}", line)
                if not p:
                    logger.warning("unexpected sentence %s" % line)
                    continue
                else:
                    logger.debug(p)
                date = "%s:%s:%s" % (p["hours"],p["minutes"],p["seconds"])
                sentence_id = p["sentence_id"]
                payload = p["payload"].split(',')

                if sentence_id == "IIVHW":
                    # IIVHW 109.2,T,101,M,2.01,N,3.73,K*45
                    
                    try:
                        true_compass_heading = str2int(payload[payload.index("T")-1])
                    except ValueError:
                        pass
                    try:
                        magnetic_compass_heading = str2int(payload[payload.index("M")-1])
                    except ValueError:
                        pass
                    surface_speed_knots = str2float(payload[payload.index("N")-1])
                    surface_speed_kph = str2float(payload[payload.index("N")-1])
                    declinaison = true_compass_heading - magnetic_compass_heading
                    if declinaison > 5:
                        logger.debug("Declinaison %s" % declinaison)
                elif sentence_id == "IIVLW":
                    continue
                elif sentence_id == "IIDPT":
                    continue
                elif sentence_id == "IIDBT":
                    continue
                elif sentence_id == "IIMTW":
                    continue
                # $IIVWR,x.x,a,x.x,N,x.x,M,x.x,K*hh
                elif sentence_id == "IIVWR":
                    try:
                        awa = str2float(payload[payload.index("R")-1])
                    except ValueError:
                        awa = str2float(payload[payload.index("L")-1])
                    aws = payload[payload.index("N")-1]
                # $IIMWD,x.x,T,x.x,M,x.x,N,x.x,M*hh
                elif sentence_id == "IIMWD":
                    twd = payload[payload.index("T")-1]
                    twd_mag = payload[payload.index("M")-1]
                    tws = payload[payload.index("N")-1]
                # $IIVWT,x.x,a,x.x,N,x.x,M,x.x,K*hh
                elif sentence_id == "IIVWT":
                    try:
                        twa = str2float(payload[payload.index("R")-1])
                    except ValueError:
                        try:
                            twa = str2float(payload[payload.index("L")-1])
                        except ValueError:
                            logger.warning(line)
                    tws = payload[payload.index("N")-1]
                elif sentence_id == "IIMTA":
                    continue
                # compass 9X
                elif sentence_id == "IIHDG":
                    # IIHDG,32,,,,*66
                    heading_magnetic = str2int(payload[0])
                    if not heading_magnetic:
                        continue
                    if heading_magnetic < 0 or heading_magnetic > 359:
                        heading_magnetic_error_count = heading_magnetic_error_count + 1
                        reset_measures()
                        continue
                    heading_magnetic_measures = heading_magnetic_measures + 1
                elif sentence_id == "IIHDM":
                    continue
                elif sentence_id == "IIHDT":
                    continue
                elif sentence_id == "IIMMB":
                    continue
                elif sentence_id == "IIXDR":
                    continue
                elif sentence_id == "IIZDA":
                    continue
                elif sentence_id == "IIGLL":
                    continue
                # GPS HR
                elif sentence_id == "IIVTG":
                    # IIVTG 20,T,,M,5.43,N,10.06,K,A*03
                    true_bottom_heading = str2int(payload[payload.index("T")-1])
                    magnetic_bottom_heading = str2int(payload[payload.index("M")-1])
                    bottom_speed_knots = str2float(payload[payload.index("N")-1])
                    bottom_speed_kph = str2float(payload[payload.index("K")-1])
                    if not true_bottom_heading:
                        reset_measures()
                        continue
                    if not magnetic_bottom_heading:
                        # never provided on Moustache
                        pass
                    if true_bottom_heading < 0 or true_bottom_heading > 359:
                        true_bottom_heading_error_count = true_bottom_heading_error_count + 1
                        reset_measures()
                        continue
                    if not bottom_speed_knots or float(bottom_speed_knots) <= 1.0:
                        reset_measures()
                        continue
                    true_bottom_heading_measures = true_bottom_heading_measures + 1
                elif sentence_id == "IIXTE":
                    continue
                elif sentence_id == "IIRMB":
                    continue
                elif sentence_id == "TRWPL":
                    continue
                elif sentence_id == "PMLR":
                    continue
                else:
                    logger.debug('Unexpected sentence %s' % line)

                if not true_bottom_heading or not heading_magnetic:
                    continue

                delta_heading = true_bottom_heading-heading_magnetic
                if delta_heading > 180:
                    delta_heading = 360 - delta_heading
                if delta_heading < -180:
                    delta_heading = 360 + delta_heading

                if float(surface_speed_knots):
                    delta_speed = str(round(100*(float(bottom_speed_knots) - float(surface_speed_knots))/float(bottom_speed_knots),2))
                else:
                    delta_speed = "0"

                ocsv.writerow((date,
                               (true_bottom_heading),
                               (delta_heading),
                               bottom_speed_knots.replace('.',','), 
                               delta_speed.replace('.',',')))
                reset_measures()

                bottom_speed_knots=""

            logger.info('Error true bottom heading: %f percent (%s/%s)' % (round((100*true_bottom_heading_error_count/true_bottom_heading_measures),2),
                                                                           true_bottom_heading_error_count, 
                                                                           true_bottom_heading_measures))
            logger.info('Error heading magnetic: %f percent (%s/%s)' % (round(100*heading_magnetic_error_count/heading_magnetic_measures,2),
                                                                              heading_magnetic_error_count,
                                                                              heading_magnetic_measures))

if __name__ == "__main__":
    main()
