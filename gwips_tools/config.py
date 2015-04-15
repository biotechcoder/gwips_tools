# -*- coding: utf-8 -*-
import os


class Config(object):
    # get the running directory of this file, move one level up to get the
    # application directory
    APP_DIR = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]


class TestingConfig(Config):
    """Testing configuration"""
    CONFIG_FILE = os.path.join(Config.APP_DIR, u'tests/data/config.json')
    DATA_DIR = os.path.join(Config.APP_DIR, u'tests/data')
    GENOME = u'hg19'


class ProductionConfig(Config):
    """Testing configuration"""
    CONFIG_FILE = os.path.join(Config.APP_DIR, u'config.json')
