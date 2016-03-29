#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: oesteban
# @Date:   2015-11-19 16:44:27
# @Last Modified by:   oesteban
# @Last Modified time: 2016-03-10 12:51:17

"""
fMRI preprocessing workflow
=====
"""
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import os
import os.path as op
from multiprocessing import cpu_count

from mriqc.utils import gather_bids_data
from nipype import config as ncfg

from fmriprep.workflows import fmri_preprocess
from fmriprep.workflows.anatomical import t1w_preprocessing


__author__ = "Oscar Esteban"
__copyright__ = ("Copyright 2016, Center for Reproducible Neuroscience, "
                 "Stanford University")
__credits__ = "Oscar Esteban"
__license__ = "BSD"
__version__ = "0.0.1"
__maintainer__ = "Oscar Esteban"
__email__ = "code@oscaresteban.es"
__status__ = "Prototype"


def main():
    """Entry point"""
    parser = ArgumentParser(description='fMRI Preprocessing workflow',
                            formatter_class=RawTextHelpFormatter)

    g_input = parser.add_argument_group('Inputs')
    g_input.add_argument('-i', '--bids-root', action='store',
                         default=os.getcwd())
    g_input.add_argument('--nthreads', action='store', default=0,
                         type=int, help='number of threads')
    g_input.add_argument(
        "--write-graph", action='store_true', default=False,
        help="Write workflow graph.")
    g_input.add_argument(
        "--use-plugin", action='store', default=None,
        help='nipype plugin configuration file')

    g_outputs = parser.add_argument_group('Outputs')
    g_outputs.add_argument('-o', '--output-dir', action='store')
    g_outputs.add_argument('-w', '--work-dir', action='store')

    opts = parser.parse_args()

    settings = {'bids_root': op.abspath(opts.bids_root),
                'output_dir': os.getcwd(),
                'write_graph': opts.write_graph,
                'skip': [],
                'nthreads': opts.nthreads}

    if opts.output_dir:
        settings['output_dir'] = op.abspath(opts.output_dir)

    if not op.exists(settings['output_dir']):
        os.makedirs(settings['output_dir'])

    if opts.work_dir:
        settings['work_dir'] = op.abspath(opts.work_dir)

        log_dir = op.join(settings['work_dir'], 'log')
        if not op.exists(log_dir):
            os.makedirs(log_dir)

        # Set nipype config
        ncfg.update_config({
            'logging': {'log_directory': log_dir, 'log_to_file': True},
            'execution': {'crashdump_dir': log_dir}
        })

    plugin_settings = {'plugin': 'Linear'}
    if opts.use_plugin is not None:
        from yaml import load as loadyml
        with open(opts.use_plugin) as f:
            plugin_settings = loadyml(f)
    else:
        # Setup multiprocessing
        if settings['nthreads'] == 0:
            settings['nthreads'] = cpu_count()

        if settings['nthreads'] > 1:
            plugin_settings['plugin'] = 'MultiProc'
            plugin_settings['plugin_args'] = {'n_procs': settings['nthreads']}

    subjects = gather_bids_data(settings['bids_root'])

    if not any([len(subjects[k]) > 0 for k in subjects.keys()]):
        raise RuntimeError('No scans found in %s' % settings['bids_root'])

    #fmriwf = fmri_preprocess(subject_list=subjects, settings=settings)
    #fmriwf.run(**plugin_settings)
    t1w_preproc = t1w_preprocessing(settings=settings)
    t1w_preproc.inputs.inputnode.t1 = subjects['anat'][0][-1]
    t1w_preproc.run(**plugin_settings)


if __name__ == '__main__':
    main()
