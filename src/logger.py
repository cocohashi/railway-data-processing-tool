import os
import logging


def load_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    handler = logging.StreamHandler() if os.environ['ENVIRONMENT'] == 'develop' else logging.FileHandler('main.log')
    logger.setLevel(logging.DEBUG) if os.environ['LEVEL'] == 'debug' else logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                                  datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
