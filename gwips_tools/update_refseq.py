#!/usr/bin/env python2
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
    log = gwips_tools.setup_logging(CONFIG, file_name='refseq.log')

    gwips_tools.check_config_json(CONFIG.CONFIG_FILE)
    parser = argparse.ArgumentParser('Available options')
    parser.add_argument('-g', '--genome',
                        help='Genome to download FASTA sequences for')
    parser.add_argument('-l', '--list',
                        help='List available genomes from configuration file',
                        action='store_true')

    args = parser.parse_args()
    if not (args.genome or args.list):
        parser.print_usage()

    vals = gwips_tools.read_config(CONFIG.CONFIG_FILE)
    if args.list:
        gwips_tools.list_genomes(vals)

    if args.genome:
        wanted_genome = args.genome
        if not gwips_tools.is_genome_in_config(vals, wanted_genome):
            sys.exit()

        gwips_tools.check_sudo()
        gene_table = vals['genomes'][wanted_genome]['gene_table']
        fasta_files = gwips_tools.find_missing_fasta(wanted_genome, gene_table)
        if not len(fasta_files):
            log.info('No files to download')
            sys.exit()

        user = pwd.getpwnam(vals['refseq_user'])
        gwips_tools.switch_user(user)

        mrnas, peps = gwips_tools.download_refseqs(
            fasta_files, vals['refseq_source_url'], vals['refseq_target_dir'])
