"""This module contains the logic used for launching expert from the command line."""

import argparse
import json
import sys
import time
from datetime import timedelta

from expert.drift import detect_drift
from expert.input import EventMapping
from expert.utils.logger import LOGGER, Level, setup_logger

__NOTICE = 0
__INFO = __NOTICE + 1
__VERBOSE = __INFO + 1
__DEBUG = __VERBOSE + 1
__SPAM = __DEBUG + 1
__QUIET = 1000


def __parse_arg() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""expert (Explainable Performance Drift) is an algorithm for finding actionable causes for drifts
                       in the performance of a process execution. For this, the cycle time of the process is monitored,
                       and, if a change is detected in the process performance, the algorithm finds the actionable
                       causes for the change.""",
        epilog="expert is licensed under the Apache License, Version 2.0",
    )

    parser.add_argument("log_file", metavar="LOG_FILE", type=str, nargs=1, help="The event log, in CSV or JSON format")
    parser.add_argument("-f", "--format", metavar="FORMAT", choices=["csv", "json"], default="csv",
                        help="specify the event log format")
    parser.add_argument("-m", "--mapping", metavar="MAPPING_FILE", type=str, nargs=1,
                        help="provide a custom mapping file")
    parser.add_argument("-t", "--timeframe", metavar="TIMEFRAME", type=int, nargs=1, default=5,
                        help="provide a timeframe size, in days, used to define the reference and running models")
    parser.add_argument("-u", "--warmup", metavar="WARMUP", type=int, nargs=1, default=5,
                        help="provide the number of days used as a warm-up")
    parser.add_argument("-o", "--overlap", metavar="OVERLAP", type=int, nargs=1, default=2,
                        help="provide the overlapping between running models, in days")
    parser.add_argument("-a", "--alpha", metavar="ALPHA", type=float, nargs=1, default=0.05,
                        help="specify the confidence for the statistical tests")
    parser.add_argument("-w", "--warnings", metavar="WARNINGS", type=int, nargs=1, default=3,
                        help="provide a number of warnings to wait after confirming a drift")
    parser.add_argument("-v", "--verbose", action="count", type=int, default=0,
                        help="enable verbose output. High verbosity levels can drastically decrease performance")
    parser.add_argument("-q", "--quiet", action="store_true", type=bool, default=False,
                        help="disable all output")

    return parser.parse_args()


def __parse_mapping(path: str) -> EventMapping:
    with open(path) as file:
        source = json.load(file)

    return EventMapping(
        start=source["start"],
        end=source["end"],
        resource=source["resource"],
        activity=source["activity"],
        case=source["case"],
    )


def run() -> None:
    args = __parse_arg()

    if args.quiet:
        setup_logger(Level.DISABLED)
    elif args.verbose >= __SPAM:
        setup_logger(Level.SPAM)
    elif args.verbose == __DEBUG:
        setup_logger(Level.DEBUG)
    elif args.verbose == __VERBOSE:
        setup_logger(Level.VERBOSE)
    elif args.verbose == __INFO:
        setup_logger(Level.INFO)
    else:
        setup_logger(Level.NOTICE)

    if args.format == "csv":
        from expert.input.csv import read_csv_log as parser
        if args.mapping is None:
            from expert.input.csv import DEFAULT_CSV_MAPPING as MAPPING
        else:
            MAPPING = __parse_mapping(args.mapping)
    else:
        LOGGER.critical("log file format not supported!")
        sys.exit(-1)

    LOGGER.notice("applying expert drift detector to file %s", args.log_file)

    start = time.perf_counter_ns()

    log = list(parser(args.log_file, attribute_mapping=MAPPING))

    detector = detect_drift(
        log=(event for event in log),
        timeframe_size=timedelta(days=args.timeframe),
        warm_up=timedelta(days=args.warmup),
        warnings_to_confirm=args.warnings,
        overlap_between_models=timedelta(days=args.overlap),
    )

    for index, drift in enumerate(detector):
        metrics = TimesPerCase(drift)
        plots = plot_features(metrics)
        plots.savefig(f"causes-drift-{index}.svg")

    end = time.perf_counter_ns()

    LOGGER.success("drift detection finished")
    LOGGER.success("execution took %s", timedelta(microseconds=(end - start) / 1000))
