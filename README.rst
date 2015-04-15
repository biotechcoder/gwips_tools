Using scripts to updating annotations and sequences
===================================================
The following scripts from gwips_tools can be used to update genome annotations
and refseq's from UCSC.

* update_annotations.py
* update_refseq.py

Usage
-----
For both the scripts, the ``-h`` flag prints a help message.

To get the list of all available genomes from configuration::

    sudo python update_annotations.py -l

To update annotations for a genome for example, hg19::

    sudo python update_annotations.py -g hg19

Reload MySQL.

To update RefSeq's::

    sudo python update_refseq.py -g hg19

`Why sudo? <sudo>`_

Configuration - adding/updating available genomes
-------------------------------------------------
List of available genomes is done in the file ``config.json``. Additional
genomes can be added to the "genomes" section. Datasets to download can be
specified in the "datasets" key of the respective genome.

Other variables

``source_url``:
    Source URL for downloading the mysql tables.

``target_dir``:
    Downloaded MySQL tables are stored in this directory.

``refseq_source_url``:
    Source URL for RefSeq sequences.

``refseq_target_dir``:
    Downloaded RefSeq's are stored in this directory.

``refseq_user``:
    User with write privileges to ``refseq_target_dir``.

``annotations_user``:
    User with write privileges to ``target_dir``.

.. _sudo:

Note regarding permissions
--------------------------
User/group id's for downloaded files are set in ``config.json`` ::

    annotations_user = 'mysql'  # for mysql tables
    refseq_user = 'vimal'  # for refseq sequences

Both the update scripts are run using ``sudo`` for the following reason.

update_annotations.py requires write access to ``/var/lib/mysql`` which is owned
by ``mysql``. When downloading datasets, the user and group id is changed to that
of the ``mysql`` user (``annotations_user``) on the system.

update_refseq.py downloads sequences to directory specified under 
``refseq_target_dir``. These are owned by user specified in ``refseq_user``.


Tests
-----
Please change paths in ``tests/config.json.sample`` and then run the test suite
from the main source directory ::

    sh runtests.sh

Tests use a different configuration file ``tests/data/config.json``.
Test configuration can be updated in ``gwips_tools/config.py``.
