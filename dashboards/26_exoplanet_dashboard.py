"""Project 26: Exoplanet population explorer (Thursday prototype dashboard).

Question: of the ~6,000 known planets, which sizes are common, and why are planets
1.5-2 times Earth's size rare (the "radius valley")?

How to run it, from the repo root:
  1. Download the data. This makes data/planets.csv (only works while the NASA archive is online):
         mkdir -p data && cd data && python3 ../starters/26_exoplanet_population.py && cd ..
  2. Start the dashboard. It opens as a web page with dropdown filters on the left:
         streamlit run dashboards/26_exoplanet_dashboard.py

Data source: NASA Exoplanet Archive, Planetary Systems Composite Parameters table (pscomppars),
https://exoplanetarchive.ipac.caltech.edu
Acknowledgement: This research has made use of the NASA Exoplanet Archive, which is operated by
the California Institute of Technology, under contract with the National Aeronautics and Space
Administration under the Exoplanet Exploration Program.

STATUS: the NASA archive was down for maintenance when this was written, so no real data has
been through this code yet. Lines marked "NOT YET TESTED WITH REAL DATA" have only been run on an
empty table (the right column names, zero planets). Check them once data/planets.csv exists.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ---------- Settings ----------
REPO = Path(__file__).resolve().parent.parent
# The starter saves planets.csv in whatever folder it is run from, so look in both likely places.
DATA_FILES = [REPO / 'data' / 'planets.csv', REPO / 'planets.csv']
NEEDED_COLUMNS = ['pl_name', 'pl_rade', 'discoverymethod', 'st_teff']

# Host-star temperature filter: bands in kelvin, labelled with the matching star type.
# The boundaries are approximate. For comparison, the Sun is about 5,800 K (a G star).
STAR_TEMPERATURE_BANDS = {
    'All stars': None,
    'Below 3,900 K (M: cool red dwarfs)': (0, 3900),
    '3,900-5,300 K (K: orange dwarfs)': (3900, 5300),
    '5,300-6,000 K (G: Sun-like stars)': (5300, 6000),
    '6,000-7,300 K (F: hotter yellow-white stars)': (6000, 7300),
    'Above 7,300 K (A and hotter stars)': (7300, 100_000),
}

# Histogram bars: 56 bars spaced evenly on a log scale from 0.25 to 32 Earth radii, so small
# planets get as much room on the chart as giant ones. Planets outside that range are left off.
RADIUS_BINS = np.logspace(np.log10(0.25), np.log10(32), 57)
RADIUS_VALLEY = (1.5, 2.0)                                            # Earth radii
REFERENCE_PLANETS = {'Earth': 1.0, 'Neptune': 3.9, 'Jupiter': 11.2}   # radius in Earth radii
BAR_COLOR, VALLEY_COLOR, INK = '#2a78d6', '#dddcd8', '#52514e'        # blue, light grey, dark grey


def find_data_file():
    """Return the path of planets.csv, or None if it hasn't been downloaded yet."""
    for path in DATA_FILES:
        if path.exists():
            return path
    return None


def filter_planets(planets, method, temperature_band):
    """Keep only the planets that match the two dropdown choices."""
    selected = planets
    if method != 'All methods':
        selected = selected[selected['discoverymethod'] == method]
    band = STAR_TEMPERATURE_BANDS[temperature_band]
    if band is not None:  # planets whose star has no measured temperature drop out here
        low, high = band
        selected = selected[(selected['st_teff'] >= low) & (selected['st_teff'] < high)]
    return selected


def plot_radius_histogram(planets, title):
    """Bar chart of how many planets have each radius, with the radius valley shaded grey."""
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.set_xscale('log')  # log scale: each step along the axis doubles the size
    ax.set_xlim(RADIUS_BINS[0], RADIUS_BINS[-1])
    ticks = [0.25, 0.5, 1, 2, 4, 8, 16, 32]
    ax.set_xticks(ticks, labels=[f'{t:g}' for t in ticks])
    ax.minorticks_off()

    ax.axvspan(*RADIUS_VALLEY, color=VALLEY_COLOR, zorder=0,
               label='Radius valley (1.5-2 Earth radii)')
    ax.hist(planets['pl_rade'], bins=RADIUS_BINS, color=BAR_COLOR, edgecolor='white', linewidth=1, zorder=2)

    # Dotted lines and labels along the top edge for familiar planets, so the sizes mean something
    for radius in REFERENCE_PLANETS.values():
        ax.axvline(radius, color=INK, linestyle=':', linewidth=1, zorder=1)
    top = ax.secondary_xaxis('top')
    top.set_xticks(list(REFERENCE_PLANETS.values()), labels=list(REFERENCE_PLANETS))
    top.minorticks_off()
    top.tick_params(colors=INK, length=0)

    ax.set_ylim(bottom=0)
    ax.set(xlabel='Planet radius (Earth radii, log scale)', ylabel='Number of planets', title=title)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc='upper left', framealpha=1, edgecolor='none')
    fig.tight_layout()
    return fig


# ---------- The web page ----------
st.set_page_config(page_title='Exoplanet population explorer')
st.title('Exoplanet population explorer')
st.write("Of the ~6,000 known planets, which sizes are common, and why are planets "
         "1.5-2 times Earth's size rare (the **radius valley**)?")
st.caption('Data: NASA Exoplanet Archive, Planetary Systems Composite Parameters table '
           '(https://exoplanetarchive.ipac.caltech.edu).')

data_file = find_data_file()
if data_file is None:
    st.warning("**No data yet.** `data/planets.csv` hasn't been downloaded. When the NASA Exoplanet "
               "Archive is back online, run this from the repo root, then reload this page:\n\n"
               "`mkdir -p data && cd data && python3 ../starters/26_exoplanet_population.py`")
    st.stop()

planets = pd.read_csv(data_file)  # NOT YET TESTED WITH REAL DATA
missing = [c for c in NEEDED_COLUMNS if c not in planets.columns]
if missing:
    st.error(f"`{data_file.name}` is missing the column(s) {missing}. It was probably made by an older "
             "version of the starter script. Run the starter again to download a fresh copy.")
    st.stop()

# Filters in the left sidebar. NOT YET TESTED WITH REAL DATA (the method names come from the file).
methods = ['All methods'] + sorted(planets['discoverymethod'].dropna().unique())
method = st.sidebar.selectbox('Discovery method', methods)
temperature_band = st.sidebar.selectbox('Host-star temperature', list(STAR_TEMPERATURE_BANDS))

# The histogram. NOT YET TESTED WITH REAL DATA: whether the dip at 1.5-2 Earth radii shows up.
selected = filter_planets(planets, method, temperature_band)
st.write(f'Showing **{len(selected):,}** of {len(planets):,} planets.')
fig = plot_radius_histogram(selected, f'{method}, {temperature_band}')
st.pyplot(fig)
plt.close(fig)

st.markdown("""
**How to read this chart**
- Each blue bar counts the planets of that size. Along the bottom, each step doubles the size.
- The grey band is 1.5-2 times Earth's size: the **radius valley**. If the valley is real, the bars
  dip there, between rocky "super-Earths" on the left and gas-wrapped "sub-Neptunes" on the right.
- Why a gap? The leading idea is that small planets close to their star lose their thin hydrogen
  atmospheres, leaving bare rock, while planets that keep their gas stay puffy and bigger. Few end
  up in between. The gap was first measured clearly in Kepler data by Fulton et al. (2017).
- Try **Transit**: that method measures a planet's size directly, so it should give the clearest view.
""")
