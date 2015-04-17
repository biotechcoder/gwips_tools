#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Downloads annotations in MySQL table format (as mysql user). """
import os
import sys
import pwd
import argparse

import config
import gwips_tools

# path to the configuration file
CONFIG = config.ProductionConfig()


if __name__ == '__main__':
    log = gwips_tools.setup_logging(
        os.path.join(CONFIG.APP_DIR, 'log/annotations.log'))

    gwips_tools.check_config_json(CONFIG.CONFIG_FILE)
    usage = """Update annotations for genomes on GWIPS.

        To list available genomes, do:

            python update_annotations.py -l

        To update all annotations, do:

            sudo python update_annotations.py -a

        [OR]

        To update annotation for a specific genome, do:

            sudo python update_annotations.py -g genome

    """
    parser = argparse.ArgumentParser(
        description='All available options', usage=usage)

    down_type = parser.add_mutually_exclusive_group()
    down_type.add_argument(
        '-a', '--all',
        help='Download annotations for all genomes',
        action='store_true')
    down_type.add_argument(
        '-g', '--genome',
        help='Download annotations for a given genome')
    parser.add_argument(
        '-l', '--list', help='List available genomes from configuration file',
        action='store_true')

    args = parser.parse_args()
    if not (args.genome or args.list or args.all):
        parser.print_usage()

    vals = gwips_tools.read_config(CONFIG.CONFIG_FILE)
    if args.list:
        print 'Available genomes'
        for org in vals['genomes']:
            print org
        sys.exit()

    genomes = []
    wanted_genome = args.genome
    if wanted_genome:
        if wanted_genome not in vals['genomes']:
            log.critical('Genome "{}" does not exist in configuration '
                         'file'.format(wanted_genome))
            sys.exit()
        genomes.append(wanted_genome)

    if args.all:
        genomes.extend(key for key in vals['genomes'])

    if len(genomes):
        if not gwips_tools.is_sudo():
            log.critical(
                'To do the updates, please run this script using sudo')
            sys.exit()
        user = pwd.getpwnam(vals['annotations_user'])
        log.debug('Switching to user {0}, id {1}, group id {2}'.format(
            user.pw_name, user.pw_uid, user.pw_gid))
        os.setegid(user.pw_gid), os.seteuid(user.pw_uid)

        for one_genome in genomes:
            log.info('Processing genome {}'.format(one_genome))
            genome = vals['genomes'][one_genome]
            for dataset in genome['datasets']:
                gwips_tools.download_mysql_table(
                    genome['source_url'], genome['target_dir'], dataset)
                log.info('Synchronized {0}/{1}'.format(one_genome, dataset))
            log.info('Finished processing {}'.format(one_genome))
