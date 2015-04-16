import os
import sys
import pwd
import json
import time
import shutil
import urllib2
import subprocess
import MySQLdb
from urlparse import urljoin

MYSQL = pwd.getpwnam('mysql')


def is_sudo():
    """Returns True if sudo is being used (uid = 0) else returns False. """
    if os.getuid() == 0:
        return True
    else:
        return False


def check_config_json(config):
    """If config.json does not exist, create it from template. """
    if not os.path.exists(config):
        print 'Creating "{}" from template ...'.format(config)
        template = '{}.sample'.format(config)
        if not os.path.exists(template):
            sys.exit('config.json.sample missing! Cannot create '
                     'configuration file. Please create config.json manually '
                     'before proceeding')
        shutil.copy(template, config)


def run_rsync(src, dst):
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    rsync_cmd = ['rsync', '-qavzP', src, dst]
    subprocess.check_call(rsync_cmd)


def read_config(config):
    """Read a config file and return a dictionary. """
    try:
        output = json.load(open(config))
    except ValueError:
        print 'Error reading configuration file. Please check if it is in ' \
              'the right format'
        raise
    return output


def chown_mysql(fname):
    """Make mysql:mysql the owner of given file. """
    os.chown(fname, MYSQL.pw_uid, MYSQL.pw_gid)


def find_missing_fasta(db):
    conn = MySQLdb.connect('localhost', db=db)
    cursor = conn.cursor()

    fasta_files = []
    sql = ('select distinct(gbExtFile.path) from gbExtFile join gbSeq '
           'on (gbSeq.gbExtFile=gbExtFile.id) join refGene on '
           '(refGene.name = gbSeq.acc);')
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
    datasets = ["{0}.{1}".format(table, item) for item in ("MYD", "MYI", "frm")]
    for dataset in datasets:
        run_rsync('{0}{1}'.format(src, dataset), os.path.join(dst, dataset))


def download_fasta(src, dst, fasta_path):
    url = urljoin(src, fasta_path)
    print url
    data = urllib2.urlopen(url)

    fasta_file = os.path.join(dst, fasta_path)
    with open(fasta_file, 'wb') as fp:
        shutil.copyfileobj(data, fp)
        return fasta_file


def download_refseqs(refseq_paths, source_url, target_dir):
    """Given the list of mRNA fasta files from database, download both mRNA
    and Protein FASTA sequences to target_dir.

    """
    mrnas = []
    peps = []
    print 'Source URL: {0}\nTarget directory: {1}\nCurrent time: {2}'.format(
        source_url, target_dir, time.asctime())

    for refseq in refseq_paths:
        refseq_mrna = refseq.strip().split('/gbdb/genbank/./data/processed/')[1]
        dir_paths = os.path.split(refseq_mrna)[0].split('/')
        refseq_pep = refseq_mrna.replace('mrna.fa', 'pep.fa')

        dirs_created = False
        for seq, seq_type in ((refseq_mrna, 'mrna'), (refseq_pep, 'protein')):
            target_seq = os.path.join(target_dir, seq)
            if os.path.exists(target_seq):
                print 'Skipped. File exists: {}'.format(target_seq)
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

    print 'Completed at: {}'.format(time.asctime())
    return mrnas, peps
