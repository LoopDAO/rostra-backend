#日志系统初始化
import logging


def logInit(logfile):
    logger = logging.getLogger()  # 不加名称设置root logger
    logger.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(message)s-%(asctime)s.%(name)s.%(levelname)s', datefmt='%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('%(asctime)s.%(levelname)s: %(message)s', datefmt='%Y%m%d %H:%M:%S')

    # 使用FileHandler输出到文件
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.ERROR)
    fh.setFormatter(formatter)

    # 使用StreamHandler输出到屏幕
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    # 添加两个Handler
    logger.addHandler(ch)
    logger.addHandler(fh)
    #logger.info('this is info message')
    #logger.warning('this is warn message')
