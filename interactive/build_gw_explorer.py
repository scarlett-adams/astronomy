"""Build the Stellar Graveyard Explorer: an interactive web page for Project 18.

This script puts the real gravitational-wave catalogue into the web page, so the page always shows
real data. It writes two files:
  interactive/18_gw_explorer.html        the page (this is the version published as a claude.ai link)
  interactive/18_gw_explorer_local.html  the same page wrapped so you can open it by double-clicking
                                          (it needs internet to load the Plotly charting library)

Run it from the repo root:
    python3 interactive/build_gw_explorer.py

Data: LIGO-Virgo-KAGRA Gravitational-Wave Transient Catalog (GWTC-1 to GWTC-5.0), from the
Gravitational Wave Open Science Center, https://gwosc.org/eventapi/csv/GWTC/
"""
import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
CATALOG_URL = 'https://gwosc.org/eventapi/csv/GWTC/'
DATA_FILE = REPO / 'data' / 'gwtc_events.csv'          # saved copy, shared with the notebook
PAGE = REPO / 'interactive' / '18_gw_explorer.html'
LOCAL_COPY = REPO / 'interactive' / '18_gw_explorer_local.html'
NS_LIMIT = 3  # solar masses: rough dividing line between neutron stars and black holes

# Short names used inside the web page, and the catalogue column each one comes from.
# Every column also has _lower and _upper versions: the 90% range around the best estimate.
COLUMNS = {
    'm1': 'mass_1_source',          # heavier object (solar masses)
    'm2': 'mass_2_source',          # lighter object (solar masses)
    'final': 'final_mass_source',   # object left after the merger (solar masses)
    'dist': 'luminosity_distance',  # distance (megaparsecs)
    'spin': 'chi_eff',              # effective spin: + spinning with the orbit, - against it
}


def load_catalog():
    """Read the saved copy of the catalogue, downloading it from GWOSC the first time."""
    if DATA_FILE.exists():
        return pd.read_csv(DATA_FILE)
    events = pd.read_csv(CATALOG_URL)
    DATA_FILE.parent.mkdir(exist_ok=True)
    events.to_csv(DATA_FILE, index=False)
    return events


def collision_type(m1, m2):
    """Same rough labels as the notebook. m1 is always the heavier partner."""
    if pd.isna(m1) or pd.isna(m2):
        return 'No masses published yet'
    if m1 < NS_LIMIT:
        return 'Two neutron stars'
    if m2 < NS_LIMIT:
        return 'Black hole + neutron star'
    return 'Two black holes'


def number(value):
    """A plain number for the web page, or None (shown as 'not published') if it's missing."""
    return None if pd.isna(value) else float(value)


events = load_catalog()
records = []
for _, row in events.iterrows():
    record = {
        'name': row['commonName'],
        'date': pd.to_datetime(row['commonName'][2:8], format='%y%m%d').strftime('%Y-%m-%d'),
        'catalog': row['catalog.shortName'],
        'url': row['jsonurl'].replace('/json/', '/html/') + '/',   # the event's page on GWOSC
        'type': collision_type(row['mass_1_source'], row['mass_2_source']),
    }
    for short, column in COLUMNS.items():
        record[short] = number(row[column])
        record[short + '_lower'] = number(row[column + '_lower'])
        record[short + '_upper'] = number(row[column + '_upper'])
    records.append(record)
records.sort(key=lambda r: r['date'])

# Put the data inside the page's <script id="gw-data"> tag, replacing whatever was there before.
data_json = json.dumps(records, separators=(',', ':')).replace('</', '<\\/')
page = PAGE.read_text()
page, replaced = re.subn(r'(<script id="gw-data" type="application/json">).*?(</script>)',
                         lambda m: m.group(1) + data_json + m.group(2), page, flags=re.S)
if replaced != 1:
    raise SystemExit(f'Could not find the <script id="gw-data"> tag in {PAGE}')
PAGE.write_text(page)

LOCAL_COPY.write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                      '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                      '</head>\n<body>\n' + page + '\n</body>\n</html>\n')

with_masses = sum(r['type'] != 'No masses published yet' for r in records)
print(f'Put {len(records)} events ({with_masses} with masses) into {PAGE.relative_to(REPO)}')
print(f'Wrote {LOCAL_COPY.relative_to(REPO)} for opening on your own computer')
