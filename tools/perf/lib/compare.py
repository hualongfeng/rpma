#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-3-Clause
# Copyright 2021, Intel Corporation
#

"""compare.py -- compare multiple benchmarks results (EXPERIMENTAL)"""

from lib.common import json_from_file
from lib.figure import Figure, draw_png

import json
import os

class Compare:
    """a helper class allowing generating comparisons"""

    def __init__(self, names, benches, result_dir):
        if len(benches) != len(names):
            raise ArithmeticError(
                                  "# of names is not equal to # of benches provided")
        for bench in benches:
            bench.check_completed()
        self._benches = {name: bench for name, bench in zip(names, benches)}
        self._result_dir = result_dir

    @staticmethod
    def _figure_id(figure):
        """generate the identifier of the figure"""
        return "{}.{}".format(figure.file, figure.key)

    def prepare_series(self):
        """generate all comparisons required (both JSON and PNG files)"""
        # track whether a given figure is already done
        done = {}
        # Loop over all benches and figures just in case not all figures are
        # present in all benches.
        for _, bench in self._benches.items():
            for figure in bench.figures:
                if done.get(Compare._figure_id(figure), False):
                    continue
                comparison = Comparison(self, figure)
                comparison.prepare_series()
                comparison.to_pngs()
                done[Compare._figure_id(figure)] = True

    def cache(self):
        """store the comparison to bench.json file"""
        # XXX assuming the first benchmark covers all figures of the comparison
        # which may not always be true
        _, bench = list(self._benches.items())[0]
        output = {
            'config': {
                'compare': True},
            'parts': bench.parts,
            'figures': [figure.cache() for figure in bench.figures],
            'requirements': {
                id: r.cache()
                    for id, r in bench.requirements.items()}
        }

        output_path = os.path.join(self._result_dir, 'bench.json')
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(output, file, indent=4)

class Comparison:
    """a comparison between the same figure present in different benches"""

    def __init__(self, compare, figure):
        self._compare = compare
        self._figure = figure # the sample figure
        # pick all figures matching the sample one
        self._figures = {}
        for name, bench in self._compare._benches.items():
            for figure in bench.figures:
                if figure == self._figure:
                    self._figures[name] = figure
                    break

    def _merge(self):
        """combine series from all figures involved into a single figure"""
        benchlines = []
        for name, figure in self._figures.items():
            for oneseries in figure.results:
                benchline = {}
                benchline['label'] = '{} {}'.format(name, oneseries['label'])
                benchline['group'] = name
                # extract the data
                benchline['points'] = oneseries['points']
                # append the line
                benchlines.append(benchline)
        return {
                'title': self._figure.title,
                'x': self._figure.argx,
                'y': self._figure.argy,
                'xscale': self._figure.xscale,
                'series': benchlines}

    def _series_file(self):
        """generate a JSON file path"""
        return os.path.join(self._compare._result_dir,
                            self._figure.file + '.json')

    def prepare_series(self):
        """prepare JSON files with picked results for the comparison"""
        if os.path.isfile(self._series_file()):
            output = json_from_file(self._series_file())['json']
        else:
            output = {}
        keycontent = self._merge()
        output[self._figure.key] = keycontent
        with open(self._series_file(), 'w', encoding='utf-8') as file:
            json.dump(output, file, indent=4)

    def png_path(self):
        """get a path to the output PNG file"""
        output = self._figure.file + '_' + self._figure.key + '.png'
        return os.path.join('.', output)

    def to_pngs(self):
        """generate all PNG files"""
        os.chdir(self._compare._result_dir)
        data = json_from_file(self._series_file())['json']
        keycontent = data.get(self._figure.key)
        output_path = self.png_path()
        # XXX add setters to yaxis_max for bw and lat
        draw_png(keycontent['x'], keycontent['y'], keycontent['series'],
                 keycontent['xscale'], output_path, None, None, None)
