import logging

loggers = []


def get_logger() -> logging:
    global loggers

    if loggers:
        return loggers[0]
    else:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())
        loggers.append(logger)
        return logger
