# coding: utf8

import argparse
import re
import sys

from fasteign import MblFasteign, Flat

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True)
parser.add_argument("--write", action="store_true")
args = parser.parse_args()

class GoFishing(Exception): pass

def to_iso_hacky(flat):

    datestring = flat.date

    if datestring is None:
        return flat.timestamp.split("T")[0]

    if re.match(r"\d{4}-\d{2}-\d{2}", datestring):
        return datestring

    if "ekki" in datestring.lower() or datestring.lower().startswith("j"):
        raise GoFishing

    # .split() will raise a value error for whats not a date

    day, month, year = datestring.split(" ")
    if int(year) < 2015 or int(year) > 2020:
        raise ValueError("Probably not a year: '{}'".format(year))


    day = day.split(".")[0].zfill(2)
    m = month.lower()
    if m.startswith("jan"):
        month = "01"
    elif m.startswith("feb"):
        month = "02"
    elif m.startswith("mar"):
        month = "03"
    elif m.startswith("apr"):
        month = "05"
    elif m.startswith("ma"):
        month = "05"
    elif m.startswith(u"júní"):
        month = "06"
    elif m.startswith("j"):
        month = "07"
    elif m.startswith(u"ágú"):
        month = "08"
    elif m.startswith("sep"):
        month = "09"
    elif m.startswith("okt"):
        month = "10"
    elif m.startswith("n"):
        month = "11"
    elif m.startswith("des"):
        month = "12"
    else:
        raise ValueError("Not a month: '{}'".format(m))


    return "-".join([year, month, day])

mblfasteign = MblFasteign(args.file)
sorted_flats = sorted(mblfasteign.existing_flats, key=lambda x: x.flatid)
i = 0
for flat in sorted_flats: #mblfasteign.existing.iteritems():
    f_id = flat.flatid
    strdate = flat.date
    try:
        #print strdate, flat.price
        isodate = to_iso_hacky(flat)
        if isodate != strdate:
            print "Fixed", isodate, "from", strdate
            mblfasteign.existing[f_id]['date'] = isodate
            try:
                mblfasteign.existing[f_id]["strings"]["date"] = strdate
            except KeyError:
                mblfasteign.existing[f_id]["strings"] = {"date": strdate}
        if args.write:
            print "writing file"
            mblfasteign.write_json()
    except GoFishing as gf:
        print flat.flatid
        datein = raw_input("Enter iso date: ")
        if not re.match(r"\d{4}-\d{2}-\d{2}", datein):
            print "Not changing anything, but aborting here so we can continue where we left off"
            sys.exit(0)

        mblfasteign.existing[f_id]["date"] = datein
        if 'strings' in mblfasteign.existing[f_id]:
            mblfasteign.existing[f_id]['strings']['date'] = strdate
        else:
            mblfasteign.existing[f_id]["strings"] = {'date': strdate}

        if args.write:
            print "writing file"
            mblfasteign.write_json()

    #except ValueError as ve:
    #    print flat.date
    #    print ve
    #    pass
