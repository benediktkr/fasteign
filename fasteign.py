#coding: utf8
import argparse
import json
import pprint
import sys
import re
import decimal
from datetime import datetime

import requests
from lxml import html

from sudoisbot import sendmsg

TEMPLATE = """
{name}
{price_short} mkr. || {size} m²
{extra}
{url}
"""

class Flat(object):
    def __init__(self, *args, **kwargs):
        self.size = kwargs.get('size')
        self.price = kwargs.get('price')
        self.name = kwargs.get('name').encode('utf-8')
        self.flatid = kwargs.get('flatid')
        self.url = "http://www.mbl.is/fasteignir/fasteign/{}/".format(self.flatid)
        self.strings = kwargs.get('strings')
        self.timestamp = kwargs.get('timestamp', datetime.now().isoformat())
        self.img = kwargs.get('img', [])

        # Now removed but may be relevant if i have to dig into data
        # self.price_str
        # NOTE: self.size_str never existed so don't go looking for it

    def __iter__(self):
        return self.__dict__

    def __repr__(self):
        return "<Flat {}>".format(self.name)

    def is_like_mine(self):
        return 90.0 <= self.size <= 92.0

    def price_per_sqm(self):
        return float(self.price) / float(self.size)

    def price_short(self):
        try:
            return decimal.Decimal(self.price) / 1000000
        except decimal.InvalidOperation:
            # Happens with it's a string (saying Tilbod)
            return ""

    def template(self):
        ps = self.price_short()
        if self.is_like_mine():
            extra = "(like mine)"
        else:
            extra = ""
        return TEMPLATE.format(price_short=ps, extra=extra, **vars(self))

    def short_template(self):
        ps = self.price_short()
        ts = self.timestamp.split("T")[0] # lol
        return "{}: {} mkr".format(ts, ps)

    def send_notification(self, send_imgs=True):
        print self.template()
        if self.img and send_imgs:
            if args.printall:
                print "Sending {} images..".format(len(self.img))
            sendmsg.send_to_me("", img=self.img)
        # summary on the bottom
        sendmsg.send_to_me(self.template())

def parse_flat_pics(flatid):
    """Makes a request to mbl.is and parses the pictures for
    the flat.
    """

    url = "http://www.mbl.is/fasteignir/fasteign/{}/photos/".format(flatid)
    res = requests.get(url)
    if not res.status_code == 200:
        res.raise_for_status()

    tree = html.fromstring(res.text)
    xpics = '//div[@class="realestate_photos"]/a/img/@src'
    ret = list(tree.xpath(xpics))
    return ret

def parse_flat(flatid):
    """Makes a request to mbl.is and parses the flat info
    """
    url = "http://www.mbl.is/fasteignir/fasteign/{}/".format(flatid)
    res = requests.get(url)
    if not res.status_code == 200:
        res.raise_for_status()

    tree = html.fromstring(res.text)

    xentry = ('//*[@id="realestate-infobox-description"]'
                  '/div[1]/table/tbody/tr[12]/td[2]')
    xentry = tree.xpath(xentry)[0]

    xtype = ('//*[@id="realestate-infobox-description"]'
                 '/div[1]/table/tbody/tr[5]/td[2]')
    xtype = tree.xpath(xtype)[0]

    xprice = ('//*[@id="realestate-infobox-description"]'
                  '/div[1]/table/tbody/tr[1]/td[2]')
    price = tree.xpath(xprice)[0].text.strip()

    xsize = ('//*[@id="realestate-infobox-description"]'
                 '/div[1]/table/tbody/tr[7]/td[2]')
    xsize = tree.xpath(xsize)[0]

    xname = ('//*[@id="fs-canvas"]/section/div[1]'
                 '/div/div[1]/span[1]/strong')
    xname = tree.xpath(xname)[0]


    img = parse_flat_pics(flatid)

    d = {
        'name': xname.text.strip(),
        'size': size_from_string(xsize.text),
        'price': price_from_string(price),
        'flatid': flatid,
        'strings': {'price': price, 'size': xsize.text},
        'type': xtype.text.strip(),
        'img': img,
    }

    return Flat(**d)

def price_from_string(price):
    if price.strip().startswith("Tilb"):
        return "Tilbod"

    return int(
        "".join([a for a in price.strip() if a.isdigit()]))


def size_from_string(size):
    hits = re.findall(r"\d+\.\d+", size)
    assert len(hits) == 1, "regex failed for '{}'".format(size)
    return float(hits[0])


class MblFasteign(object):
    def __init__(self, filename, printall=False):
        self.filename = filename
        self.printall = printall


        self.existing = self.read_json()
        self.existing_flats = [Flat(**e[1]) for e in self.existing.items()]

    def last_flats_like_mine(self, count=3):
        return [a for a in self.existing_flats if a.is_like_mine()][:count]

    def send_summary(self):
        last = self.last_flats_like_mine()
        if not last:
            print "I don't know about any flats"
            return

        summary = "\n".join([a.short_template() for a in last])
        if self.printall:
            print summary
        sendmsg.send_to_me(summary)

    def search(self, searchurl):
        res = requests.get(searchurl)
        if not res.status_code == 200:
            res.raise_for_status()
        tree = html.fromstring(res.text)
        try:
            resultlist = tree.xpath('//*[@id="resultlist"]')[0]
        except IndexError:
            raise ValueError("Empty resultlist")
        prefix = len("realeastate-result-")-1
        return [a.get("id")[prefix:] for a in resultlist]

    def update(self):
        pass

    def read_json(self):
        try:
            with open(self.filename, "r") as f:
                return json.loads(f.read().decode('utf-8'))
        except IOError as e:
            if e.errno == 2:
                print "New file: {}".format(self.filename)
                return dict()
            else:
                raise


    def parse_new_flats(self, searchurl):
        start_count = len(self.existing)
        flatids = self.search(searchurl)

        for flatid in flatids:

            if flatid not in self.existing:
                # Just parse (send a request to mbl) new finds
                #
                # NOTE: this means we do not observe changes in price listings
                # which would be interesting.
                flat = parse_flat(flatid)

                send_imgs = flat.is_like_mine() or self.printall
                flat.send_notification(send_imgs)

                self.existing[flatid] = flat.__dict__

            elif self.printall:
                flat = Flat(**self.existing[flatid])
                if flat.is_like_mine():
                    flat.send_notification()

        return len(self.existing) != start_count


    def write_json(self):
        with open(self.filename, "w") as f:
            f.write(json.dumps(self.existing, indent=4))
        if self.printall:
            print "Saved json: {}".format(self.filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", required=True, type=str)
    parser.add_argument("--search", default="breidholt", type=str)
    parser.add_argument("--printall", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    searches = {
        'breidholt': "http://www.mbl.is/fasteignir/leit/?q=e09ddca032a239798b5f3c4ac91beb50",
        'test': "http://www.mbl.is/fasteignir/leit/?q=80f323c5382397611e72800316f250d1"
        }

    try:
        f = MblFasteign(args.filename, printall=args.printall)
        if args.summary:
            f.send_summary()
            sys.exit(0)

        if args.printall:
            print "Looking up flats from search results.."

        newflats = f.parse_new_flats(searches[args.search])
        if newflats or args.printall:
            f.send_summary()
    except Exception as e:
        sendmsg.send_to_me("fasteign.py: {}".format(e))
        raise
    finally:
        f.write_json()
