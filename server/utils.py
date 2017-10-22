import logging


def configure_log(level=None, name=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_handler = logging.FileHandler('server.log', 'w')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s: %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger
