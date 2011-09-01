"""This module provides a way to grab and store raw data for radioactive decay."""
import os
import re
import glob
import urllib
import urllib2
from zipfile import ZipFile

import numpy as np
import tables as tb

from pyne import nucname
from pyne import ensdf

def grab_ensdf_decay(build_dir=""):
    """Grabs the ENSDF decay data files
    if not already present.

    Parameters
    ----------
    build_dir : str
        Major directory to place html files in. 'KAERI/' will be appended.
    """
    # Add kaeri to build_dir
    build_dir = os.path.join(build_dir, 'ENSDF')
    try:
        os.makedirs(build_dir)
    except OSError:
        pass

    # Grab ENSDF files and unzip them.
    iaea_base_url = 'http://www-nds.iaea.org/ensdf_base_files/2010-November/'
    ensdf_zip = ['ensdf_1010_099.zip', 'ensdf_1010_199.zip', 'ensdf_1010_294.zip',]

    for f in ensdf_zip:
        fpath = os.path.join(build_dir, f)
        if f not in os.listdir(build_dir):
            print "  grabing {0} and placing it in {1}".format(f, fpath)
            urllib.urlretrieve(iaea_base_url + f, fpath)

        with ZipFile(fpath) as zf:
            for name in zf.namelist():
                if not os.path.exists(os.path.join(build_dir, name)):
                    print "    extracting {0} from {1}".format(name, f)
                    zf.extract(name, build_dir)



atomic_decay_dtype = np.dtype([
    ('from_nuc_name', 'S6'),
    ('from_nuc_zz',   int),
    ('to_nuc_name',   'S6'),
    ('to_nuc_zz',     int), 
    ('half_life',    float),
    ('decay_const',   float),
    ('branch_ratio',  float),
    ])
    
    
def parse_decay(build_dir=""):
    """Builds and returns a list of nuclide decay data.
    """
    build_dir = os.path.join(build_dir, 'ENSDF')

    decay_data = []
    files = sorted([f for f in glob.glob(os.path.join(build_dir, 'ensdf.*'))])
    for f in files:
        print "    parsing decay data from {0}".format(f)
        decay_data += ensdf.half_life(f)

    ln2 = np.log(2.0)
    decay_data = [(nucname.name(fn), fn, nucname.name(tn), tn, hl, ln2/hl, br) for fn, tn, hl, br in decay_data]

    decay_array = np.array(decay_data, dtype=atomic_decay_dtype)
    return decay_array
    
    
def make_atomic_decay_table(nuc_data, build_dir=""):
    """Makes an atomic weight table in the nuc_data library.

    Parameters
    ----------
    nuc_data : str
        Path to nuclide data file.
    build_dir : str
        Directory to place html files in.
    """
    # Grab raw data
    atomic_decay  = parse_decay(build_dir)

    # Open the HDF5 File
    decay_db = tb.openFile(nuc_data, 'a')

    # Make a new the table
    decaytable = decay_db.createTable("/", "atomic_decay", atomic_decay_dtype, 
                             "Atomic Decay Data half_life [s], decay_const [1/s], branch_ratio [frac]", expectedrows=len(atomic_decay))
    decaytable.append(atomic_decay)

    # Ensure that data was written to table
    decaytable.flush()

    # Close the hdf5 file
    decay_db.close()




def make_decay(nuc_data, build_dir):
    #with tb.openFile(nuc_data, 'r') as f:
    #    if hasattr(f.root, 'decay'):
    #        return 

    # grab the decay data
    print "Grabing the ENSDF decay data from IAEA"
    grab_ensdf_decay(build_dir)

    # Make atomic weight table once we have the array
    print "Making decay data table."
    make_atomic_decay_table(nuc_data, build_dir)
