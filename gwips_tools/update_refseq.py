#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import pwd
import sys
import argparse
import logging

import config
import gwips_tools

# path to the configuration file
CONFIG = config.ProductionConfig()

if __name__ == '__main__':

    gwips_tools.check_config_json(CONFIG.CONFIG_FILE)
    parser = argparse.ArgumentParser('Available options')

    down_type = parser.add_mutually_exclusive_group()
    down_type.add_argument(
        '-a', '--all', help='Download RefSeq sequences for all genomes',
        action='store_true')
    down_type.add_argument(
        '-g', '--genome', help='Genome to download FASTA sequences for')
    parser.add_argument(
        '-l', '--list', help='List available genomes from configuration file',
        action='store_true')
    parser.add_argument(
        '-n', '--dry-run', help='Dry run. No files are downloaded (rsync -n)',
        action='store_true')

    args = parser.parse_args()
    if not (args.genome or args.list or args.all):
        parser.print_usage()

    vals = gwips_tools.read_config(CONFIG.CONFIG_FILE)
    if args.list:
        gwips_tools.list_genomes(vals)

    genomes = []
    if args.genome:
        wanted_genome = args.genome
        if gwips_tools.is_genome_in_config(vals, wanted_genome):
            genomes.append(wanted_genome)
        else:
            sys.exit()

    if args.all:
        genomes.extend(key for key in vals['genomes'])

    if len(genomes):
        gwips_tools.check_sudo()
        log = gwips_tools.setup_logging(CONFIG, file_name='refseq.log')
        user = pwd.getpwnam(vals['refseq_user'])
        gwips_tools.switch_user(user)
        # TODO: verify this has happened
        log.info('Switched to user: {}'.format(user.pw_name))

        all_fasta_files = []
        for genome in genomes:
            log.info('Processing genome: {}'.format(genome))
            gene_table = vals['genomes'][genome]['gene_table']
            fasta_files = gwips_tools.find_missing_fasta(genome, gene_table)

            if len(fasta_files):
                all_fasta_files.extend(fasta_files)

        # remove duplicates and download refseqs
        gwips_tools.download_refseqs(
            list(set(all_fasta_files)), vals['refseq_source_url'],
            vals['refseq_target_dir'], dry_run=args.dry_run)
