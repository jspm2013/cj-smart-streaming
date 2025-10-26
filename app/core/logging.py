import logging, sys
def setup_logging(level="INFO"):
    logging.basicConfig(level=level, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")