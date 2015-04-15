#!/usr/bin/env python2
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
    gwips_tools.check_config_json(CONFIG.CONFIG_FILE)
    if not gwips_tools.is_sudo():
        print ('WARN: For actual updates (-g or -a), please run this script '
               'using sudo')

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
    if not (args.genome or args.list):
        parser.print_help()

    vals = gwips_tools.read_config(CONFIG.CONFIG_FILE)
    if args.list:
        print 'Available genomes'
        for org in vals['genomes']:
            print org
        sys.exit(0)

    genomes = []
    wanted_genome = args.genome
    if wanted_genome:
        if wanted_genome not in vals['genomes']:
            sys.exit('Genome "{}" does not exist in configuration '
                     'file'.format(wanted_genome))
        genomes.append(wanted_genome)

    if args.all:
        genomes.extend(key for key in vals['genomes'])

    if len(genomes):
        user = pwd.getpwnam(vals['annotations_user'])
        print 'Switching to user {0}, id {1}, group id {2}'.format(
            user.pw_name, user.pw_uid, user.pw_gid)
        os.setegid(user.pw_gid), os.seteuid(user.pw_uid)

        for one_genome in genomes:
            genome = vals['genomes'][one_genome]
            for dataset in genome['datasets']:
                print 'Syncing {0}/{1}...'.format(one_genome, dataset),
                gwips_tools.run_rsync(
                    os.path.join(genome['source_url'], dataset),
                    os.path.join(genome['target_dir'], dataset)
                )
                print 'done.'
