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
    log = gwips_tools.setup_logging(CONFIG, file_name='annotations.log')

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
    parser.add_argument(
        '-n', '--dry_run', help='Dry run. No files are downloaded (rsync -n)',
        action='store_true')

    args = parser.parse_args()
    if not (args.genome or args.list or args.all):
        parser.print_usage()

    vals = gwips_tools.read_config(CONFIG.CONFIG_FILE)
    if args.list:
        gwips_tools.list_genomes(vals)

    genomes = []
    wanted_genome = args.genome
    if wanted_genome:
        if gwips_tools.is_genome_in_config(vals, wanted_genome):
            genomes.append(wanted_genome)
        else:
            sys.exit()

    if args.all:
        genomes.extend(key for key in vals['genomes'])

    if len(genomes):
        gwips_tools.check_sudo()
        user = pwd.getpwnam(vals['annotations_user'])
        gwips_tools.switch_user(user)

        for one_genome in genomes:
            log.info('Processing genome {}'.format(one_genome))
            genome = vals['genomes'][one_genome]

            for dataset in genome['datasets']:
                files = ['{0}.{1}'.format(dataset, item) for item in ('MYD', 'MYI', 'frm')]

                for mysql_file in files:
                    source_file = '{0}{1}'.format(genome['source_url'], mysql_file)
                    target_file = os.path.join(genome['target_dir'], mysql_file)

                    # take a backup first
                    log.info('Backup {}'.format(mysql_file))
                    backup_file = os.path.join(vals['backup_dir'], one_genome, mysql_file)
                    if os.path.exists(backup_file):
                        gwips_tools.run_rsync(target_file, backup_file, dry_run=args.dry_run)
                    else:
                        log.warn('File does not exist in source. Nothing to backup \n{}'.format(backup_file))
                    gwips_tools.run_rsync(source_file, target_file, dry_run=args.dry_run)

                log.info('Synchronized {0}/{1}\n'.format(one_genome, dataset))
            log.info('Finished processing {}'.format(one_genome))
