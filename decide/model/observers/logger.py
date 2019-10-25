import logging
import sys

from ..observers.observer import Observer, Observable


class Logger(Observer):
    LOG_LEVEL = 2

    def update(self, observable, notification_type, **kwargs):
        if notification_type == Observable.LOG and Logger.LOG_LEVEL > 1:
            logging.info("LOG:", kwargs["message"])
        elif notification_type == Observable.EXECUTED and Logger.LOG_LEVEL > 2:
            logging.info("LOG: Executed exchange")
        elif notification_type == Observable.REMOVED and Logger.LOG_LEVEL > 2:
            logging.info("LOG: Removed {0} exchange(s)".format(len(kwargs["removed"])))
        elif notification_type == Observable.FINISHED_ROUND and Logger.LOG_LEVEL > 1:

            sys.stdout.write(
                "\rLOG: Finished round {0} with {1} exchanges".format(
                    kwargs["iteration"], len(kwargs["realized"])
                )
            )
        elif notification_type == Observable.CLOSE and Logger.LOG_LEVEL > 1:
            sys.stdout.write("\n")
