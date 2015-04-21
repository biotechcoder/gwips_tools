# -*- coding: utf-8 -*-
import os
import sys
import pwd
import json
import shutil
import logging
import logging.handlers
import subprocess
import MySQLdb
import config

MYSQL = pwd.getpwnam('mysql')
log = logging.getLogger('gwips_tools')


def setup_logging(conf, file_name):
    """Setup logging to console and files under log directory
    (only in production mode).

    """
    logger = logging.getLogger('gwips_tools')
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s. %(asctime)s.',
                                  datefmt='%Y-%m-%d %I:%M %p')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if isinstance(conf, config.ProductionConfig):
        log_dir = os.path.join(conf.APP_DIR, 'log')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        fh = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, file_name), maxBytes=10485760, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


def is_sudo():
    """Returns True if sudo is being used (uid = 0) else returns False."""
    if os.getuid() == 0:
        return True
    else:
        return False


def check_config_json(conf):
    """If config.json does not exist, create it from template. """
    if not os.path.exists(conf):
        log.info('Creating "{}" from template ...'.format(conf))
        template = '{}.sample'.format(conf)
        if not os.path.exists(template):
            log.critical(
                'config.json.sample missing! Cannot create configuration file. '
                'Please create config.json manually before proceeding')
            sys.exit()
        shutil.copy(template, conf)


def run_rsync(src, dst):
    """Executes rsync on src -> dst with the -qavzP options."""
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    rsync_cmd = ['rsync', '-qavzP', src, dst]
    log.info('{0} -> {1}'.format(src, dst))
    try:
        subprocess.check_call(rsync_cmd)
    except subprocess.CalledProcessError:
        log.exception('While downloading {}'.format(src))
        sys.exit(1)


def read_config(conf):
    """Read a config file and return a dictionary. """
    try:
        output = json.load(open(conf))
    except ValueError:
        log.critical('Error reading configuration file. Please check if it '
                     'is in the right format')
        raise
    return output


def find_missing_fasta(genome, gene_table='refGene'):
    """Returns list of missing RefSeq mRNA FASTA files for the given genome."""
    conn = MySQLdb.connect('localhost', db=genome)
    cursor = conn.cursor()

    fasta_files = []
    sql = ('select distinct(gbExtFile.path) from gbExtFile join gbSeq '
           'on (gbSeq.gbExtFile=gbExtFile.id) join {0} on '
           '({0}.name = gbSeq.acc);'.format(gene_table))
    cursor.execute(sql)
    while 1:
        row = cursor.fetchone()
        if not row:
            break
        # /gbdb/genbank/./data/processed/refseq.69/daily.2015.0316/mrna.fa
        fasta_files.append(row[0])

    cursor.close()
    conn.close()
    return fasta_files


def download_mysql_table(src, dst, table):
    """Downloads MySQL data, index and table definition files
    ('MYD', 'MYI', 'frm') for the given table from src to dst using rsync.

    """
    datasets = ['{0}.{1}'.format(table, item) for item in ('MYD', 'MYI', 'frm')]
    for dataset in datasets:
        run_rsync('{0}{1}'.format(src, dataset), os.path.join(dst, dataset))


def download_refseqs(refseq_paths, source_url, target_dir):
    """Given the list of mRNA fasta files from database, download both mRNA
    and Protein FASTA sequences to target_dir.

    """
    mrnas = []
    peps = []
    log.info('Source URL: {0}. Target directory: {1}.'.format(
        source_url, target_dir))

    for refseq in refseq_paths:
        refseq_mrna = refseq.strip().split('/gbdb/genbank/./data/processed/')[1]
        dir_paths = os.path.split(refseq_mrna)[0].split('/')
        refseq_pep = refseq_mrna.replace('mrna.fa', 'pep.fa')

        dirs_created = False
        for seq, seq_type in ((refseq_mrna, 'mrna'), (refseq_pep, 'protein')):
            target_seq = os.path.join(target_dir, seq)
            if os.path.exists(target_seq):
                log.info('Skipped. File exists: {}'.format(target_seq))
            else:
                if not dirs_created:
                    base_dir = target_dir
                    for dpath in dir_paths:
                        base_dir = os.path.join(base_dir, dpath)
                        if not os.path.exists(base_dir):
                            os.mkdir(base_dir)
                    dirs_created = True
                run_rsync(os.path.join(source_url, seq), target_seq)
                if seq_type == 'mrna':
                    mrnas.append(target_seq)
                else:
                    peps.append(target_seq)
    log.info('Completed downloading RefSeq\'s')
    return mrnas, peps
