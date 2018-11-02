import logging
import sys


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    class NoParsingFilter(logging.Filter):
        def filter(self, record):
            return record.name.startswith('zfssnaps')

    logger = logging.getLogger('zfssnaps')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    ch.addFilter(NoParsingFilter())
    root.addHandler(ch)
