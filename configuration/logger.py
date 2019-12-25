import logging

loggers = []


def get_logger() -> logging:
    global loggers

    if loggers:
        return loggers[0]
    else:
        logger = logging.getLogger()
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        loggers.append(logger)
        return logger
