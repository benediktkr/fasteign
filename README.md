# fasteign

Quick script to scrape Fasteignarvefur Mbl.

## Usage

Go www.mbl.is/fasteignir and create a search you are interested in. Copy the url into the parameter in `fasteign.py`.

## Code quality

Not great, but it works

## If in doubt..

Compare json files with this

```
jq --argfile a breidholt.json --argfile b ../breidholt.json.filled.out.15.07.2019 -n '($a | (.. | arrays) |= sort) as $a | ($b | (.. | arrays) |= sort) as $b | $a == $b'
```
