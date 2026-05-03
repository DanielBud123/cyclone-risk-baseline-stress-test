import os
import glob
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA1D_ROOT = PROJECT_ROOT / "data" / "raw" / "TCND_Data1D" / "Data1D"

BASINS = ['WP', 'EP', 'NA', 'SI', 'SP']
SPLITS = ['train', 'test', 'val']

TRACK_COLS = ['step_idx', 'flag', 'lon_norm', 'lat_norm',
              'pres_norm', 'wind_norm', 'time_raw', 'storm_name']

def intensity_class(wind_ms):
    """Intensity class based on 2-min sustained wind thresholds."""
    if wind_ms < 17.5: return 'Sub-tropical'
    if wind_ms < 32.9: return 'Tropical storm'
    if wind_ms < 42.7: return 'Hurricane (low)'
    if wind_ms < 49.4: return 'Hurricane (mid)'
    if wind_ms < 58.1: return 'Major hurricane'
    if wind_ms < 70.5: return 'Intense'
    return 'Extreme'

def denormalise(df):
    '''Add physical-unit columns derived from normalised values.
    Formulas from the original github readme documentation
    '''
    df['wind_ms']  = df['wind_norm'] * 25 + 40
    df['lat_deg']  = df['lat_norm']  * 5
    lon_raw        = df['lon_norm']  * 5 + 180
    df['lon_deg']  = ((lon_raw + 180) % 360) - 180  # wrap to [-180, 180]
    df['pres_hPa'] = df['pres_norm'] * 50 + 960
    return df

def parse_year_from_filename(fname):
    '''Extract 4-digit year from filename like WP1950_01.txt or similar ones'''
    base = os.path.splitext(os.path.basename(fname))[0]
    try:
        return int(base[2:6])
    except ValueError:
        warnings.warn(f"Could not parse year from {fname}")
        return None

def load_basin(data_root, basin, splits = SPLITS):
    '''Load all storms for a single basin across train/val/test splits'''
    
    rows = []
    for split in splits:
        path = os.path.join(data_root, basin, split)
        if not os.path.isdir(path):
            warnings.warn(f"Missing directory: {path}")
            continue

        for f in sorted(glob.glob(os.path.join(path, '*.txt'))):
            df = pd.read_csv(f, sep = '\t', header = None, names = TRACK_COLS)
            base = os.path.splitext(os.path.basename(f))[0]
            df['storm_id'] = f"{basin}_{base}"
            df['basin'] = basin
            df['year'] = parse_year_from_filename(f)
            df['split'] = split
            rows.append(df)

    if not rows:
        warnings.warn(f"No files loaded for basin {basin}")
        return pd.DataFrame()
    
    tracks = pd.concat(rows, ignore_index= True)
    tracks = denormalise(tracks)

    tracks['storm_name'] = tracks['storm_name'].astype(str).str.strip()
    tracks['time_step'] = pd.to_datetime(
        tracks['time_raw'].astype(int).astype(str),
        format='%Y%m%d%H', errors='coerce'
    )

    tracks['intensity_class'] = tracks['wind_ms'].apply(intensity_class)
    return tracks

def load_all_basins(data_root=DATA1D_ROOT):
    """Load all basins, concatenate into one DataFrame."""
    parts = []
    for basin in BASINS:
        print(f"Loading {basin}...", end=' ')
        df = load_basin(data_root, basin)
        if not df.empty:
            print(f"{len(df):,} timesteps from {df['storm_id'].nunique():,} storms")
            parts.append(df)
        else:
            print("(empty)")
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def haversine_km(lat1, lon1, lat2, lon2):
    '''Great-circle distance in km between paired (lat, lon) arrays in degrees.'''
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2-lat1)
    dlam = np.radians(lon2-lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) *np.sin(dlam/2) **2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def per_storm_metrics(group):
    '''Compute intensity, Rapid Intensification flag, translation speed for one storm.'''
    g = group.sort_values('time_step')
    wind = g['wind_ms'].values
    lat   = g['lat_deg'].values
    lon   = g['lon_deg'].values
    times = g['time_step'].values

    #Peak intensity
    peak_wind = float(np.nanmax(wind)) if len(wind) else np.nan
    peak_class = intensity_class(peak_wind) if np.isfinite(peak_wind) else 'Sub-tropical'

    #Rapid intensitifcation is defined as 30 kt increase over any 24 hour window
    #We have 4 timesteps at 6-hour intervals
    RI_threshold_ms = 30/ 1.944    #Convert to m/s
    ri = False
    if len(wind) >= 5:
        deltas = wind[4:] - wind[:-4]
        ri = bool(np.any(deltas >= RI_threshold_ms))

    #Mean translation speed
    if len(wind) >= 2:
        seg_km = haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:])
        seg_h = (np.diff(times) / np.timedelta64(1, 'h')).astype(float)
        with np.errstate(divide='ignore', invalid='ignore'):
            speeds = np.where(seg_h > 0, seg_km / seg_h, np.nan)
        mean_speed = float(np.nanmean(speeds)) if np.any(np.isfinite(speeds)) else np.nan
    else:
        mean_speed = np.nan

    #Lifetime in hours robust to NaT
    valid_times = times[~pd.isna(times)]
    if len(valid_times) >= 2:
        lifetime_h = float((valid_times.max() - valid_times.min()) / np.timedelta64(1, 'h'))
    else:
        lifetime_h = 0.0

    return pd.Series({
        'peak_wind_ms':         peak_wind,
        'intensity_class':      peak_class,
        'is_major_hurricane':   peak_class in {'Major hurricane', 'Intense', 'Extreme'},
        'is_intense_or_above':  peak_class in {'Intense', 'Extreme'},
        'is_extreme':           peak_class == 'Extreme',
        'experienced_RI':       ri,
        'mean_translation_kmh': mean_speed,
        'genesis_lat':          float(lat[0]) if len(lat) else np.nan,
        'genesis_lon':          float(lon[0]) if len(lon) else np.nan,
        'lifetime_hours':       lifetime_h,
        'n_observations':       len(wind),
    })

def build_storm_summary(tracks):
    '''Aggregate timesteps tracks into one summary row per storm.'''
    if tracks.empty:
        return pd.DataFrame()
    
    keys = (
        tracks[['storm_id', 'basin', 'year', 'storm_name', 'split']]
        .drop_duplicates('storm_id')
        .set_index('storm_id')
     )
    metrics = (
        tracks
        .groupby("storm_id", sort=False)
        .apply(per_storm_metrics, include_groups=False)
    )

    summary = keys.join(metrics).reset_index()
    summary['decade'] = (summary['year'] // 10 * 10).astype(int)
    return summary