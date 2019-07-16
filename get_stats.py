#coding: utf8

import argparse

from fasteign import MblFasteign, Flat

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True)
parser.add_argument("--count", type=int)
parser.add_argument("--csv", action="store_true")
args = parser.parse_args()

if __name__ == "__main__":
    mblfasteign = MblFasteign(args.file)
    last = mblfasteign.last_flats_like_mine(args.count)
    for flat in last:
        if args.csv:
            print "{},{},{},{}".format(
                flat.date, flat.name, flat.size, flat.price)
        else:
            print flat.short_template(), flat.name
