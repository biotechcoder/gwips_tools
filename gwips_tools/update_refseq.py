# -*- coding: utf-8 -*-
import os
import pwd
import sys
import argparse

import config
import gwips_tools

# path to the configuration file
CONFIG = config.ProductionConfig()

if __name__ == '__main__':
    gwips_tools.check_config_json(CONFIG.CONFIG_FILE)
    if not gwips_tools.is_sudo():
        sys.exit('Need permissions to update as gwips user. Please run this '
                 'script using sudo')

    parser = argparse.ArgumentParser('Available options')
    parser.add_argument('-g', '--genome',
                        help='Genome to download FASTA sequences for')
    parser.add_argument('-l', '--list',
                        help='List available genomes from configuration file',
                        action='store_true')
    args = parser.parse_args()

    if not (args.genome or args.list):
        parser.print_help()

    vals = gwips_tools.read_config(CONFIG.CONFIG_FILE)
    if args.list:
        print 'Available genomes'
        for org in vals:
            print org
        sys.exit(0)

    if args.genome:
        wanted_genome = args.genome
        if wanted_genome not in vals['genomes']:
            sys.exit('Genome "{}" does not exist in configuration '
                     'file'.format(wanted_genome))

        # for testing, we use a single sequence instead of querying mysql
        # fasta_files = [open('../tests/data/missing.fa').readline().strip()]
        fasta_files = gwips_tools.find_missing_fasta(wanted_genome)

        print 'Downloading FASTA files...'
        user = pwd.getpwnam(vals['refseq_user'])

        print 'Switching to user {0}, id {1}, group id {2}'.format(
            user.pw_name, user.pw_uid, user.pw_gid)

        os.setegid(user.pw_gid), os.seteuid(user.pw_uid)
        mrnas, peps = gwips_tools.download_refseqs(
            fasta_files, vals['refseq_source_url'], vals['refseq_target_dir'])
