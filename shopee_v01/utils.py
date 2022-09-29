import logging

def schedular_log(msg):
    logger  = logging.getLogger()
    # logging.basicConfig(filename='example.log', encoding='UTF-8', level=logging.INFO)
    logging.basicConfig(handlers=[logging.FileHandler(filename="../logs/schedular_log.txt",
                                                 encoding='utf-8', mode='a+')],
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%F %A %T",
                    level=logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logging.info(msg)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

