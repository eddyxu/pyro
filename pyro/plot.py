#!/usr/bin/env python
#
# Copyright: 2014 (c) Lei Xu <eddyxu@gmail.com>
# License: BSD

"""Generic Plot Functions"""

import itertools
import matplotlib.pyplot as plt

_LINE_STYLES = ['-', '--', '-.', ':']
_LINE_MARKERS = ['', 'x', '+', 'o', '^', '.', ',']


def auto_label(axe, rects):
    """Automatically add value labels to bars

    @param axe
    @param rects
    """
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        axe.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                 '%0.2f%%' % float(height), ha='center', va='bottom')


def line_style_iterator():
    """Iterator all combinations of line styles (and markers)
    """
    for style in itertools.cycle(_LINE_STYLES):
        for marker in _LINE_MARKERS:
            yield style, marker


def plot(curves, title, xlabel, ylabel, outfile, **kwargs):
    """A generic function to plot curves

    @param curves a list of curves. [ (xvalues, yvalues, label), ... ]
    @param title graph title
    @param xlabel x-axes label
    @param ylabel y-axes label
    @param outfile the path of output file

    Optional parameters:
    @param ylim the scale of y-axes
    @param ncol number of columns in legends
    @param loc the location of legend
    @param colortheme defaults is black
    @param semilogy set log values on y-axes
    """
    assert curves
    ylim = kwargs.get('ylim', None)
    ncol = kwargs.get('ncol', 1)
    loc = kwargs.get('loc', 0)  # best loc
    color_theme = kwargs.get('colortheme', 'black')
    semilogy = kwargs.get('semilogy', False)

    plt.figure()
    style_iterator = line_style_iterator()
    for xvalues, yvalues, label in curves:
        if color_theme == 'black':
            style, marker = style_iterator.__next__()
            plt.plot(xvalues, yvalues, label=label, color='k', ls=style,
                     marker=marker)
        else:
            plt.plot(xvalues, yvalues, label=label)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if ylim:
        plt.ylim(ylim)
    if semilogy:
        plt.semilogy()
    plt.legend(ncol=ncol, loc=loc)
    plt.savefig(outfile)
    plt.close()


def plot_dict(data, title, xlabel, ylabel, outfile, **kwargs):
    """Plots a two-level dictionary.

    Optional parameters:
    @param reverse sets to true to use 2nd-level keys as x-axis.
    """
    assert type(data) == dict
    # analysis.fill_missing_data(data)
    x_values = sorted(data.keys())
    y_values = {}
    for x_value in x_values:
        y_value = data[x_value]
        for key, value in y_value.iteritems():
            try:
                y_values[key].append(value)
            except KeyError:
                y_values[key] = [value]
    curves = []
    for label, y_value in y_values.iteritems():
        curves.append((x_values, y_value, label))

    plot(curves, title, xlabel, ylabel, outfile, **kwargs)
