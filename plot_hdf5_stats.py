#!/usr/bin/env python2
#
# Stats:
#   sample_count
#   spike_count
#   bit_count
#   mean
#   std
#
# Aggregate:
#   All channels
#   Per channel
#
# Filters:
#   Channels
#   Time range
#
# Data format
#   array with N rows, M columns
#      N = number of files
#      M = number of channels
#
#   -- or --
#
#   array with N rows
#      N = number of files
#
from __future__ import print_function, division
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import datetime
from collections import defaultdict

from nevroutil import *

inf = float('inf')

import McsPy.McsData
import McsPy.McsCMOS
from McsPy import ureg

McsPy.McsData.VERBOSE = False

stats_available = set(('sample_count', 'spike_count', 'bit_count', 'mean', 'std'))

def sample_count(raw_data):
    """ Sample count all channels """
    rec = raw_data.recordings[0]
    stream = rec.analog_streams[0]
    n_samples = stream.channel_data.shape[1]

    return n_samples

def spike_count(raw_data, channels, t0=0, t1=inf):
    """ Spike count per channel """
    rec = raw_data.recordings[0]
    te = rec.timestamp_streams[0].timestamp_entity
    timestamps = get_timestamp_data_in_range(te, channels, t0, t1)

    spike_counts = np.zeros(len(channels))
    for i, ch in enumerate(channels):
        if ch in timestamps:
            spike_counts[i] = len(timestamps[ch])

    return spike_counts

def bit_count(raw_data, channels, t0=0, t1=inf):
    """ Bit count per channel """
    rec = raw_data.recordings[0]
    stream = rec.analog_streams[0]
    stream_data = get_stream_data_in_range(stream, channels, t0, t1)

    bit_counts = np.zeros(len(channels))
    for i, ch in enumerate(channels):
        if ch in stream_data:
            data = stream_data[ch]

            mean = np.mean(data)
            std = np.std(data)
            th_lo = mean - 5 * std
            th_hi = mean + 5 * std

            bits = digitize(data, th_lo, th_hi)
            idx = split_where(bits)
            bit_counts[i] = len(idx)

    return bit_counts




def normalize_stats(stats_data, divisor):
    if len(stats_data.shape) > len(divisor.shape):
        divisor = divisor.reshape((-1, 1))
    return stats_data / divisor




def plot_stats_total(stats, stats_data, xticks, labels):
    fig, ax = plt.subplots(figsize=(11,11))
    axes = [ax] + [plt.twinx() for i in range(len(stats) - 1)]
    prop_cycler = ax._get_lines.prop_cycler

    x = xticks
    ax.set_xticklabels(xticks, rotation='vertical')
    lines = []

    for i, k in enumerate(stats):
        ax = axes[i]
        y = stats_data[k]
        if len(y.shape) == 2:
            # Aggregate
            y = np.sum(y, axis=1)

        line, = ax.plot(x, y, label=labels[i], **prop_cycler.next())
        lines.append(line)
        ax.set_ylabel(labels[i], color=line.get_color())

    labels = [l.get_label() for l in lines]
    plt.legend(lines, labels)
    plt.subplots_adjust(bottom=0.4)



def main(args):
    stats = args.stats.split(',')
    t0 = args.t0
    t1 = args.t1

    assert set(stats) - stats_available == set()

    stats_data = defaultdict(list)

    # Channel selection
    channels = args.channels
    if channels:
        channels = channels.split(',')
        channels = set(map(int, channels))
    else:
        channels = set(range(60)) # TODO: dont hardcode this

    if args.exclude_channels:
        exclude_channels = args.exclude_channels.split(',')
        exclude_channels = set(map(int, exclude_channels))
        channels = channels - exclude_channels

    for i, filename in enumerate(args.files):
        print("Processing {}...".format(filename))

        raw_data = McsPy.McsData.RawData(filename)
        rec = raw_data.recordings[0]
        stream = rec.analog_streams[0]
        timestamps = rec.timestamp_streams[0].timestamp_entity

        if 'sample_count' in stats or args.normalize:
            sc = sample_count(raw_data)
            stats_data['sample_count'].append(sc)

        if 'spike_count' in stats:
            sc = spike_count(raw_data, channels, t0, t1)
            stats_data['spike_count'].append(sc)

        if 'bit_count' in stats:
            bc = bit_count(raw_data, channels, t0, t1)
            stats_data['bit_count'].append(bc)

        # date = datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=int(raw_data.date_in_clr_ticks)/10)
        # dates.append(date)

    for k in stats_data:
        stats_data[k] = np.array(stats_data[k])

    labels = list(stats)

    if args.normalize:
        for i,k in enumerate(stats):
            if k not in ('spike_count', 'bit_count'):
                continue
            stats_data[k] = normalize_stats(stats_data[k], stats_data['sample_count'])
            labels[i] += ' (normalized)'

    if args.mode == 'total':
        xticks = list(map(os.path.basename, args.files))
        plot_stats_total(stats, stats_data, xticks, labels)
    else:
        raise NotImplementedError()

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Plot hdf5 data.')
    parser.add_argument('-o', '--output', metavar='FILE',
            help='save plot to file')
    parser.add_argument('-s', '--stats', default='spike_count',
                        help='what stats to plot [{}] (default: %(default)s)'.format(','.join(stats_available)))
    parser.add_argument('-m', '--mode', choices=('total', 'per-channel'), default='total')
    parser.add_argument('-t0', type=float, default=0)
    parser.add_argument('-t1', type=float, default=inf)
    parser.add_argument('-ch', '--channels', help='list of channels (default: all)')
    parser.add_argument('-ech', '--exclude-channels')
    parser.add_argument('-n', '--normalize', action='store_true',
            help='normalize by sample_count')
    parser.add_argument('files', nargs='+', metavar='FILE',
            help='files to analyse (hdf5)')

    args = parser.parse_args()
    main(args)