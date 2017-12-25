#coding: utf8
import json
import pprint
import sys

import requests
from lxml import html

class Fasteign(object):
    def __init__(self, searchurl):
        self.searchurl = searchurl
        self.flatids = self.search()

    def search(self):
        res = requests.get(self.searchurl)
        if not res.status_code == 200:
            res.raise_for_status()
        tree = html.fromstring(res.text)
        try:
            resultlist = tree.xpath('//*[@id="resultlist"]')[0]
        except IndexError:
            raise ValueError("Empty resultlist")
        prefix = len("realeastate-result-")-1
        return [a.get("id")[prefix:] for a in resultlist]

    def _str2int(self, string):
        return int(
            "".join([a for a in string if a.isdigit()]))

    def parse_flat(self, flatid):
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
        xprice = tree.xpath(xprice)[0]

        xsize = ('//*[@id="realestate-infobox-description"]'
                 '/div[1]/table/tbody/tr[7]/td[2]')
        xsize = tree.xpath(xsize)[0]

        xname = ('//*[@id="fs-canvas"]/section/div[1]'
                 '/div/div[1]/span[1]/strong')
        xname = tree.xpath(xname)[0]

        xdate = ('//*[@id="realestate-infobox-description"]'
                 '/div[1]/table/tbody/tr[14]/td[2]')
        xdate = tree.xpath(xdate)[0]

        return {
            "price": self._str2int(xprice.text.strip()),
            "price_str": xprice.text.strip(),
            "name": xname.text.strip(),
            "size": self._str2int(xsize.text.strip()),
            "flatid": flatid,
            "entry": xentry.text.strip(),
            "type": xtype.text.strip(),
            "date": xdate.text.strip(),
            "url": url,
        }

    def write_json(self, filename):
        try:
            with open(filename, "r") as f:
                existing = json.loads(f.read())
        except IOError:
            print "New file"
            existing = dict()
        for flatid in self.flatids:
            if flatid in existing:
                # NOTE: not updating
                pass
            else:
                flat = self.parse_flat(flatid)
                pprint.pprint(flat)
                existing[flatid] = flat

        with open(filename, "w") as f:
            f.write(json.dumps(existing))


if __name__ == "__main__":
    breidholt = "http://www.mbl.is/fasteignir/leit/?q=e09ddca032a239798b5f3c4ac91beb50"
    test = "http://www.mbl.is/fasteignir/leit/?q=80f323c5382397611e72800316f250d1"
    try:
        filename = sys.argv[1]
    except IndexError:
        print "python fasteign.py filename"
        sys.exit(1)
    f = Fasteign(breidholt)
    f.write_json(filename)
