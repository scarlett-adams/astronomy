# pip install requests pandas matplotlib
import io, requests, pandas as pd, matplotlib.pyplot as plt

ARCHIVE = 'https://exoplanetarchive.ipac.caltech.edu'

# NASA Exoplanet Archive TAP: one row per confirmed planet (Planetary Systems Composite table)
# st_teff is the host star's temperature in kelvin; the Project 26 dashboard filters on it.
q = ("select pl_name, pl_rade, pl_orbper, discoverymethod, disc_year, st_teff from pscomppars "
     "where pl_rade is not null and pl_orbper is not null")
r = requests.get(ARCHIVE + '/TAP/sync', params={'query': q, 'format': 'csv'}, timeout=120)

# Stop with a plain-English message if the archive didn't send back a table of planets.
if r.status_code == 503:  # 503 = "Service Unavailable": the archive is down, usually for maintenance
    raise SystemExit("The NASA Exoplanet Archive is offline right now (HTTP 503), usually for maintenance.\n"
                     "This is a problem on NASA's side, not a bug in this script. Nothing was downloaded or saved.\n"
                     f"Check {ARCHIVE} in a browser, then run this script again later.")
r.raise_for_status()                # any other HTTP error (404, 500, ...) stops here with its code
if r.text.lstrip().startswith('<'):  # a web page or an XML error message came back instead of CSV
    raise SystemExit("The NASA Exoplanet Archive sent back a web page instead of a table of planets.\n"
                     "Nothing was saved. Open this link in a browser to see what it says:\n" + r.url)

df = pd.read_csv(io.StringIO(r.text))
df.to_csv('planets.csv', index=False)                  # snapshot so the plot is reproducible
print(len(df), 'planets with radius and period')

fig, ax = plt.subplots(figsize=(8, 6))
for method, g in df.groupby('discoverymethod'):
    if len(g) >= 10:
        ax.scatter(g.pl_orbper, g.pl_rade, s=4, label=f'{method} ({len(g)})')
ax.axhspan(1.5, 2.0, color='gray', alpha=0.2, label='radius valley (~1.5-2 Earth radii)')
ax.set(xscale='log', yscale='log', xlabel='Orbital period (days)', ylabel='Planet radius (Earth radii)')
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig('exoplanet_population.png', dpi=150)
