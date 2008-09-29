#! /usr/bin/env python

############################################################################
##  test_tree_io.py
##
##  Part of the DendroPy phylogenetic computation library.
##
##  Copyright 2008 Jeet Sukumaran and Mark T. Holder.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this programm. If not, see <http://www.gnu.org/licenses/>.
##
############################################################################

"""
Tests input/output of trees from files.
"""

import unittest
import datetime
import logging
import tempfile
import os
from optparse import OptionGroup
from optparse import OptionParser
import StringIO

from dendropy import get_logger
from dendropy import get_logging_level

import dendropy.tests
_LOG = get_logger("NEXUS/NEWICK Tree Parsing and Writing")

from dendropy import taxa
from dendropy import trees
from dendropy import utils
from dendropy import datasets

### MODULES THAT WE ARE TESTING ###
from dendropy import nexus
from dendropy import nexml
### MODULES THAT WE ARE TESTING ###

def iterate_on_trees(tree_files, tf_iterator=nexus.iterate_over_trees):
    """
    Test (supposedly) memory-economical iteration on trees.
    """
    logging_level = get_logging_level()
    total_tree_files = len(tree_files)
    total_trees = 0
    start_time = datetime.datetime.now()
    if logging_level > logging.INFO:
        minimal_logging = True
    else:
        minimal_logging = False
    _LOG.info("\n*** ITERATOR: <%s> ***" % tf_iterator.__name__)
    for tree_file_idx, tree_file in enumerate(tree_files):
        _LOG.info("   - %s" % os.path.basename(tree_file))
        for tree_idx, tree in enumerate(tf_iterator(file=open(tree_file,'r'))):
            if not minimal_logging:
                _LOG.debug("\n%s" % str(tree))
        total_trees += (tree_idx + 1)
    if not minimal_logging:
        _LOG.debug("\n")
    end_time = datetime.datetime.now()
    _LOG.info("Trees Read: %s" % total_trees)
    _LOG.info("Start time: %s" % start_time)
    _LOG.info("  End time: %s" % end_time)
    run_time = end_time-start_time
    _LOG.info("  Run time: %s" % utils.pretty_print_timedelta(run_time))
    return run_time

def compare_parse_performance(tree_files, methods):
    _LOG.info("\nRunning iterators for (speed) performance comparison ...")
    results = {}
    for method in methods:
        results[method] = iterate_on_trees(tree_files=tree_files, tf_iterator=method)
    _LOG.info("\n---")
    for m1 in methods:
        for m2 in methods[methods.index(m1)+1:]:
            t1 = results[m1]
            t2 = results[m2]
            if t1 >= t2:
                diff = t1 - t2
                diff_sign = "+"
            else:
                diff = t2 - t1
                diff_sign = "-"
            diff_seconds = diff.seconds + float(diff.microseconds)/1000000
            _LOG.info("<%s> vs. <%s> = %s%s seconds " % (m1.__name__, m2.__name__, diff_sign, diff_seconds))

def test_tree_iter_performance(format,
                               heavy=False,
                               wait_to_start=False):
    """
    Test speed of (supposedly) memory-economical iteration on trees.
    """
    sources = dendropy.tests.data_source_path(format=format, heavy=heavy)
    if wait_to_start:
        raw_input("Hit [ENTER] to begin iterating over trees: ")
    iterate_on_trees(sources)

# def get_anolis_consensus_tree():
#     leaves = {
#             "Anolis_ahli": 0.2642,
#             "Anolis_aliniger": 0.16,
#             "Anolis_alutaceus": 0.1619,
#             "Anolis_angusticeps": 0.0857,
#             "Anolis_bahorucoensis": 0.2267,
#             "Anolis_barahonae": 0.2115,
#             "Anolis_brevirostris": 0.1801,
#             "Anolis_coelestinus": 0.1932,
#             "Anolis_cristatellus": 0.2144,
#             "Anolis_cuvieri": 0.1687,
#             "Anolis_distichus": 0.1151,
#             "Anolis_equestris": 0.0227,
#             "Anolis_garmani": 0.1068,
#             "Anolis_grahami": 0.0864,
#             "Anolis_insolitus": 0.2439,
#             "Anolis_krugi": 0.1573,
#             "Anolis_lineatopus": 0.1957,
#             "Anolis_loysiana": 0.1836,
#             "Anolis_luteogularis": 0.0306,
#             "Anolis_marcanoi": 0.2359,
#             "Anolis_occultus": 0.4231,
#             "Anolis_olssoni": 0.2569,
#             "Anolis_ophiolepis": 0.0945,
#             "Anolis_paternus": 0.0595,
#             "Anolis_sagrei": 0.0968,
#             "Anolis_strahmi": 0.1978,
#             "Anolis_stratulus": 0.1973,
#             "Anolis_valencienni": 0.1643,
#             "Anolis_vanidicus": 0.206,
#             "Diplolaemus_darwinii": 0.3182,
#     }
#
#     taxa_block = taxa.TaxaBlock()
#     leaf_nodes = []
#     for tax_label in leaves:
#         taxon = taxa_block.add_taxon(elem_id="TAXON_"+tax_label, label=tax_label)
#         node = trees.Node(elem_id="tax_label_"+tax_label, taxon=taxon)
#         node.edge.length = leaves[tax_label]

def read_newick_tree(tree_filepath):
    """
    Wrapper to read and return a tree from a single-tree NEWICK file.
    """
    f = open(tree_filepath, 'r')
    tstr = f.read()
    _LOG.info('Reading "%s"' % os.path.basename(tree_filepath))
    _LOG.debug(tstr)
    tree = nexus.parse_newick_string(tstr)
    leaves = tree.leaves()
    _LOG.info("%d leaves on tree: %s" % (len(leaves), (", ".join([str(n.taxon) for n in leaves]))))
    return tree

def write_newick_tree(tree, tree_filepath):
    """
    Wrapper to write a single tree to a NEWICK file.
    """
    nw = nexus.NewickWriter()
    f = open(tree_filepath, 'w')
    tstr = nw.compose_tree(tree)
    _LOG.info('\nWriting "%s"' % os.path.basename(tree_filepath))
    f.write(tstr)

def read_nexus_tree(tree_filepath):
    """
    Wrapper to read and return a tree from a single-tree NEWICK file.
    """
    f = open(tree_filepath, 'r')
    tstr = f.read()
    _LOG.info('Reading "%s"' % os.path.basename(tree_filepath))
    _LOG.debug(tstr)
    reader = nexus.NexusReader()
    dataset = reader.read_dataset(StringIO.StringIO(tstr))
    tree = dataset.trees_blocks[0][0]
    leaves = tree.leaves()
    _LOG.info("%d leaves on tree: %s" % (len(leaves), (", ".join([str(n.taxon) for n in leaves]))))
    return tree

def write_nexus_tree(tree, tree_filepath):
    """
    Wrapper to write a single tree to a NEWICK file.
    """
    d = datasets.Dataset()
    taxa_block = tree.infer_taxa_block()
    tree_block = d.add_trees_block(taxa_block=taxa_block)
    tree_block.append(tree)
    nw = nexus.NexusWriter()
    _LOG.info('\nWriting "%s"' % os.path.basename(tree_filepath))
    nw.write_dataset(d, open(tree_filepath, 'w'))

class TreeIOTest(unittest.TestCase):

    def setUp(self):
        self.formats = ["newick",
                        "nexus",
                        "nexml",
                       ]
        self.readers = {"newick": nexus.NewickReader,        
                        "nexus": nexus.NexusReader,
                        "nexml": nexml.NexmlReader,
                       }        
        self.writers = {"newick": nexus.NewickWriter,        
                        "nexus": nexus.NexusWriter,
                        "nexml": nexml.NexmlWriter,
                       }
        self.tree_data = ["anolis.mbcon",
                          #"anolis.mcmct",
                          #"primates.mcmct",
                         ]
        self.tree_files = {}
        for format in self.readers:
            self.tree_files[format] = []
            for td in self.tree_data:
                self.tree_files[format].append(dendropy.tests.data_source_path(td + ".trees." + format))

    def round_trip_tree_file(self,
                             tree_filepath,
                             reader_class,
                             writer_class):
        """
        Round-trips a treefile.
        """
        reader = reader_class()
        _LOG.info("\nDATA FILE: \"%s\"" % os.path.basename(tree_filepath))
        dataset = reader.read_dataset(src=open(tree_filepath, "r"))      
        for tb_idx, trees_block in enumerate(dataset.trees_blocks):
            for t_idx, tree in enumerate(trees_block):
            
                _LOG.info("*** Tree %d of %d from tree block %d of %d in \"%s\""
                            % (t_idx+1,
                            len(trees_block),
                            tb_idx+1,
                            len(dataset.trees_blocks),
                            os.path.basename(tree_filepath)
                            ))
                
                _LOG.debug("\nORIGINAL TREE >>>\n%s\n<<< ORIGINAL TREE" 
                            % tree.compose_newick()
                              )                
                # write ...
                _LOG.info("(writing out)")
                temp_dataset = datasets.Dataset()
                temp_trees_block = trees.TreesBlock(taxa_block=trees_block.taxa_block)
                temp_trees_block.append(tree)
                temp_dataset.add_trees_block(trees_block=temp_trees_block)
                writer = writer_class()
                result1 = StringIO.StringIO()
                writer.write_dataset(temp_dataset, result1)
                result1 = result1.getvalue()                               
                _LOG.debug("\nWRITE OUT >>>\n%s\n<<< WRITE OUT" % result1)

                # read back ...
                _LOG.info("(reading back)")           
                r2 = StringIO.StringIO(result1)
                #r2 = open("/Users/jeet/Documents/Projects/Phyloinformatics/DendroPy/dendropy/dendropy/tests/data/anolis.mbcon.trees.nexus", "r")
                temp_dataset2 = reader.read_dataset(src=r2)                                
                tree2 = temp_dataset2.trees_blocks[0][0]
                result2 = StringIO.StringIO()
                writer.write_dataset(temp_dataset, result2)
                result2 = result2.getvalue()                
                _LOG.debug("\nREAD IN >>>\n%s\n<<< READ IN" % result2)      
                
                # compare ...
                _LOG.debug("\nREPARSED TREE >>>\n%s\n<<< REPARSED TREE\n" 
                            % tree.compose_newick()
                              )                    
                self.assertEqual(result1, result2, "Reparsed tree strings do not match:\n\n" \
                                                       +"FIRST >>>\n%s\n<<< FIRST\n\nSECOND >>>\n%s\n<<< SECOND" % (result1, result2))
                _LOG.info("(reparsed tree string match)")
            
                


    def test_tree_file_parse(self):
        for format in self.formats:
            _LOG.info('\n[Testing %s format parsing: <%s>, <%s>]'  % (format.upper(),
                                                                          self.readers[format].__name__,
                                                                          self.writers[format].__name__))
            for tfile in self.tree_files[format]:
                self.round_trip_tree_file(tfile, self.readers[format], self.writers[format])

def main_local():
    """
    Main CLI handler.
    """

    parser = OptionParser(add_help_option=True)

    parser.add_option('-p', '--performance',
                      action="store_const",
                      dest="format_type",
                      const="all",
                      help="evaluate NEXUS and NEWICK parsing performance")

    parser.add_option('--NEXUS',
                      action="store_const",
                      dest="format_type",
                      const="NEXUS",
                      help="evaluate NEXUS format parsing performance")

    parser.add_option('--NEWICK',
                      action="store_const",
                      dest="format_type",
                      const="NEWICK",
                      help="evaluate NEWICK format parsing performance")

    parser.add_option('-H', '--heavy',
                        action='store_true',
                        dest='heavy',
                        default=False,
                        help='run heavy (large file) version of performance tests')

    parser.add_option('-w', '--wait',
                        action='store_true',
                        dest='wait',
                        default=False,
                        help='wait for user confirmation before starting runs')

    (opts, args) = parser.parse_args()

    if opts.format_type == "NEXUS":
        filename_filter = "*.trees.nexus"
    elif opts.format_type == "NEWICK":
        filename_filter = "*.trees.newick"
    else:
        filename_filter = "*.trees.*"
    test_tree_iter_performance(filename_filter=filename_filter,
                               heavy=opts.heavy,
                               wait_to_start=opts.wait)


import sys
if __name__ == "__main__":
    if len(sys.argv) == 1:
        unittest.main()
    else:
        main_local()


    #compare_heavy(nexus.iterate_over_trees, "*.newick.tre")
    #compare_heavy(nexus.tree_iter, "*.newick.tre")
