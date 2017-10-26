#!/usr/bin/env python2
from __future__ import print_function, division
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle

plt.style.use('ggplot')

def main(args):
    print("Loading {}...".format(args.filename))

    data = pickle.load(open(args.filename, 'rb'))
    method = data['method']
    complexity = data['complexity']
    files = data['files']
    channels = data['channels']

    n_results = len(complexity)
    n_channels = np.mean([len(chs) for chs in channels])

    print("  {} results, {:.2f} channels each".format(n_results, n_channels))
    if channels[1:] == channels[:-1]:
        print("  Channels: {}".format(channels[0]))
    else:
        print("  Channels: mixed")
    print("  Method: {}".format(method))
    print("  #samples: {}".format(data['nsamples']))
    print("  Compression: {}".format(data['compression']))
    print("")

    for i, c in enumerate(complexity):
        if method == 'per-channel':
            mean = np.mean(c)
            std = np.std(c)
            print("  {}: mean={} std={}".format(i, mean, std))
        else:
            print("  {}: {}".format(i, c))

    plt.title(os.path.basename(args.filename))

    if method == 'per-channel':
        x = np.arange(len(complexity))

        if args.max:
            max = np.array([np.max(v) for v in complexity])
            line, = plt.plot(x, max)
        else:
            mean = np.array([np.mean(v) for v in complexity])
            std = np.array([np.std(v) for v in complexity])
            line, = plt.plot(x, mean)
            plt.fill_between(x, mean-std, mean+std, alpha=0.25, facecolor=line.get_color())

        # Per channel scatter plot
        color = None
        for i, v in enumerate(complexity):
            line, = plt.plot(np.repeat(i, len(v)), v, '.', color=color)
            color = line.get_color()

    else:
        plt.plot(complexity)

    # ugh...
    labels = map(os.path.basename, files)
    plt.xticks(np.arange(len(complexity)), labels, rotation='vertical')
    plt.subplots_adjust(bottom=0.50)
    xmin, xmax = plt.xlim()
    plt.xlim(xmin-1, xmax+1)

    ymin, ymax = plt.ylim()
    if ymin < 0:
        plt.ylim(ymin=0)
    plt.ylabel("Complexity")

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Complexity plot')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='save plot to file')
    parser.add_argument('-m', '--max', action='store_true',
                        help='plot max value (per-channel only)')
    parser.add_argument('filename', metavar='FILE',
                        help='pickle file from complexity_analysis.py')

    args = parser.parse_args()
    main(args)