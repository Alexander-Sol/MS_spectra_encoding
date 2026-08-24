#from altair import X2
import pandas as pd
import numpy as np
import spectrum_utils.plot as sup
import spectrum_utils.spectrum as sus
import pyteomics
from pyteomics import mzml, auxiliary
import matplotlib.pyplot as plt
from matplotlib.pyplot import subplots
from rapidhash import rapidhash
import mmh3
import numpy as np

import numpy as np
from scipy.spatial import distance
import pandas as pds
import re


from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler
from sklearn.manifold import TSNE

import SpectrumWithTransformations

try:
    import plotly.tools as tls
except Exception:
    tls = None
    import logging
    logging.getLogger(__name__).warning(
        "plotly.tools not available; plot_MS2 will fall back to matplotlib display"
    )

"""A collection of utility functions for spectrum analysis.
Mostly take from the excellent series of tutorials by Prof. Sam Payne & Co.
[INSERT LINK HERE]"""

AMINO_ACID_DICT = {'A': 71.037114, 'R':156.101111 , 'N': 114.042927,
        'D': 115.026943, 'C': 103.009185, 'E': 129.042593,
        'Q' : 128.058578, 'G': 57.021464, 'H': 137.058912,
        'I': 113.084064, 'L': 113.084064, 'K': 128.094963,
        'M' : 131.040485, 'F':  147.068414, 'P':  97.052764,
        'S': 87.032028, 'T': 101.047679, 'U': 150.95363,
        'W': 186.079313, 'Y': 163.06332, 'V': 99.068414
        }

PROTON_MASS = 1.007276466812
HYDROGEN_MASS = 1.00784
OXYGEN_MASS = 15.994915


def extract_scan_number(scan_id):
    """Extract the integer scan number from an mzML-style spectrum id string."""
    if isinstance(scan_id, int):
        return scan_id

    match = re.search(r"(?:^|\s)scan=(\d+)(?:\s|$)", str(scan_id))
    if match is None:
        raise ValueError(f"Could not extract scan number from {scan_id!r}")

    return int(match.group(1))



def get_all_MS2_objects(mzml_path, max_spectra=None):
    ms2_spectra = []
    with pyteomics.mzml.read(mzml_path) as spectra:
        for spectrum in spectra:
            # This finds the corresponding values in the .mzml file to create list of ms2 objs
            ms_level = spectrum.get('ms level', 0)  # Use 'ms level' not 'level'
            if ms_level == 2:
                spectrum_id = spectrum['id']  # Use spectrum['id'], not spectrum['ms level'][0]
                mz = spectrum['m/z array']
                intensity = spectrum['intensity array']
                retention_time = spectrum['scanList']['scan'][0]['scan start time']
                precursor_mz = spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
                precursor_charge = int(spectrum['precursorList']['precursor'][0]['selectedIonList']['selectedIon'][0]['charge state'])

                su_spectrum = sus.MsmsSpectrum(spectrum_id, precursor_mz, precursor_charge, mz, intensity, retention_time=retention_time)

                # Process the spectrum
                processed_spectrum = (su_spectrum.filter_intensity(0.05, 100)
                                    .remove_precursor_peak(fragment_tol_mass=10, fragment_tol_mode='ppm') # used 0.5, Da
                                    .scale_intensity('root'))

                # Add processed spectrum to our list
                ms2_spectra.append(processed_spectrum)
                # stop early if requested
                if max_spectra and len(ms2_spectra) >= max_spectra:
                    break

    return ms2_spectra

def make_ion_ladder(peptide, aa_mass = None):
    """Generate b and y ion ladders for a given peptide sequence.
    If you want to know the chemistry/physics behind this, you can read
    about it in this paper: https://cse.sc.edu/~rose/790B/papers/dancik.pdf """
    aa_mass = aa_mass or AMINO_ACID_DICT
    b_ions = {}
    y_ions = {}
    mass_Hydrogen = HYDROGEN_MASS
    mass_Oxygen = OXYGEN_MASS
    proton_mass = PROTON_MASS

    # Generate b-ions
    b_mass_current = 0
    b_ion = ''
    for aa in peptide:
        b_ion += aa
        if(b_ion != peptide):
            b_mass_current += aa_mass[aa]
            b_ions[b_ion] = b_mass_current + proton_mass  # mass of the charge on fragment

    # Generate y-ions
    y_mass_current = mass_Hydrogen + mass_Oxygen #adds terminal OH
    y_mass_current += proton_mass
    y_ion = ''
    for aa in peptide[::-1]:
        y_ion += aa
        if (y_ion[::-1] != peptide):
            y_mass_current += aa_mass[aa]
            y_ions[y_ion[::-1]] = y_mass_current + proton_mass #mass of charge on fragment

    # Populate dataframe
    data = {
        'b#': [b+1 for b in range(len(peptide)-1)],
        'b_ion_m/z': [b_ions[b_key] for b_key in b_ions.keys()],
        'b_ion_sequence': [b_key for b_key in b_ions.keys()],
        'y_ion_sequence': [y_key for y_key in y_ions.keys()][::-1],
        'y_ion_m/z': [y_ions[y_key] for y_key in y_ions.keys()][::-1],
        'y#': [len(peptide)-i-1 for i in range(len(peptide)-1)]
    }

    # Format dataframe
    df = pd.DataFrame(data)

    df = df.style.set_properties(
        subset=['b_ion_sequence'],
        **{'text-align': 'left'}
    ).format({
        'b_ion_m/z': '{:,.2f}',
        'y_ion_m/z': '{:,.2f}'
    }).set_table_styles([{
        'selector': 'thead th',
        'props': [('vertical-align', 'bottom'), ('text-align', 'left')]
    }, {
        'selector': 'th.index_name',  # targeting the index name specifically
        'props': [('vertical-align', 'bottom')]
    }])

    return(df)

# @title Run this cell to declare a function that gets an MS2 spectrum object
def get_MS2_object(mzml_path, scan, peptide = None):
    su_spectrum = None
    with pyteomics.mzml.read(mzml_path) as spectra:
        for spectrum in spectra:
            scanNumber = extract_scan_number(spectrum['id'])
            if scanNumber == scan:
                # This finds the cooresponding values in the .mzml file to create our MS2 for a given scan (see the params)
                spectrum_id = spectrum['id']
                mz = spectrum['m/z array']
                intensity = spectrum['intensity array']
                retention_time = spectrum['scanList']['scan'][0]['scan start time']
                precursor_mz = spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
                precursor_charge = int(spectrum['precursorList']['precursor'][0]['selectedIonList']['selectedIon'][0]['charge state'])

                su_spectrum = sus.MsmsSpectrum(spectrum_id, precursor_mz, precursor_charge, mz, intensity, retention_time=retention_time)

                # Process the spectrum
                su_spectrum = (su_spectrum.filter_intensity(0.05, 50)
                            .remove_precursor_peak(fragment_tol_mass=10, fragment_tol_mode='ppm') # used to be 0.5, Da
                            .scale_intensity('root'))
                break
    # Formatting
    if su_spectrum:
        fragment_tol_mass = 10
        fragment_tol_mode = 'ppm'  ## for some reason, if I use 'ppm' it doesn't work

        # If given the peptide, spec_utils can annotate the peaks
        if peptide:
            su_spectrum = su_spectrum.annotate_proforma(peptide, fragment_tol_mass, fragment_tol_mode, ion_types='by', max_ion_charge=2)
    return su_spectrum

def get_MS1_object(mzml_path, scan, peptide = None):
    """Get an MS1 spectrum and return it as a Plotly figure.
    
    Parameters:
    -----------
    mzml_path : str
        Path to the mzML file
    scan : int
        Scan number to retrieve
    peptide : str, optional
        Not used for MS1 spectra (included for API consistency)
        
    Returns:
    --------
    plotly.graph_objs.Figure
        Interactive Plotly figure of the MS1 spectrum
    """
    import plotly.graph_objects as go
    
    with pyteomics.mzml.read(mzml_path) as spectra:
        for spectrum in spectra:
            scanNumber = extract_scan_number(spectrum['id'])
            if scanNumber == scan:
                # Extract spectrum data
                spectrum_id = spectrum['id']
                mz = spectrum['m/z array']
                intensity = spectrum['intensity array']
                retention_time = spectrum['scanList']['scan'][0]['scan start time']
                
                # Create Plotly figure for MS1 spectrum
                fig = go.Figure()
                
                max_intensity = np.max(intensity)
                relative_intensity = intensity / max_intensity

                # Add vertical lines for each peak where the intensity is 
                # >= 0.01 * max_intensity (stem plot style)
                for m, i in zip(mz, relative_intensity):
                    if i >= 0.01:
                        fig.add_trace(go.Scatter(
                            x=[m, m, None],
                            y=[0, i, None],
                            mode='lines',
                        line=dict(color='black', width=1),
                        showlegend=False,
                        hovertemplate=f'm/z: {m:.4f}<br>Intensity: {i:.2f}<extra></extra>'
                    ))
                
                # Update layout
                fig.update_layout(
                    title=f'MS1 Spectrum - Scan {scan}',
                    xaxis_title='m/z',
                    yaxis_title='Relative Intensity',
                    plot_bgcolor='white',
                    xaxis=dict(
                        showline=True,
                        linecolor='black',
                        linewidth=2,
                        showgrid=True,
                        gridcolor='lightgray',
                        range = [400, 1000]
                    ),
                    yaxis=dict(
                        showline=True,
                        linecolor='black',
                        linewidth=2,
                        showgrid=True,
                        gridcolor='lightgray'
                    ),
                    hovermode='closest'
                )
                
                return fig
    
    return None

def get_lcms_map_region(mzml_path, rt_range, mz_range):
    """Extract the LC-MS map region for a peptide feature as a flat point list.

    Walks the MS1 scans of an mzML file and collects every peak whose retention
    time falls in ``rt_range`` and whose m/z falls in ``mz_range``. This is the
    raw (retention time, m/z, intensity) representation of an LC-MS map region --
    the shared starting point for both the DeepIso image encoding and the
    PointIso point-cloud encoding in notebook 05.

    Parameters
    ----------
    mzml_path : str
        Path to the mzML file (e.g. the committed DDA calibration file).
    rt_range : (float, float)
        Inclusive (low, high) retention-time window in minutes.
    mz_range : (float, float)
        Inclusive (low, high) m/z window.

    Returns
    -------
    pandas.DataFrame
        One row per peak with columns ``scan`` (int MS1 scan number),
        ``rt`` (float, minutes), ``mz`` (float), and ``intensity`` (float),
        sorted by ``rt`` then ``mz``. Empty (zero-row) frame if nothing matches.
    """
    lo_rt, hi_rt = rt_range
    lo_mz, hi_mz = mz_range

    scans, rts, mzs, intensities = [], [], [], []
    with pyteomics.mzml.read(mzml_path) as spectra:
        for spectrum in spectra:
            if spectrum.get('ms level', 0) != 1:
                continue
            rt = float(spectrum['scanList']['scan'][0]['scan start time'])
            if rt < lo_rt or rt > hi_rt:
                continue
            scan = extract_scan_number(spectrum['id'])
            mz = spectrum['m/z array']
            intensity = spectrum['intensity array']
            mask = (mz >= lo_mz) & (mz <= hi_mz)
            n = int(mask.sum())
            if n == 0:
                continue
            scans.append(np.full(n, scan, dtype=int))
            rts.append(np.full(n, rt))
            mzs.append(mz[mask])
            intensities.append(intensity[mask])

    if not scans:
        return pd.DataFrame(columns=['scan', 'rt', 'mz', 'intensity'])

    df = pd.DataFrame({
        'scan': np.concatenate(scans),
        'rt': np.concatenate(rts),
        'mz': np.concatenate(mzs),
        'intensity': np.concatenate(intensities),
    })
    return df.sort_values(['rt', 'mz']).reset_index(drop=True)


def build_lcms_image(points, mz_bin=0.01, mz_range=None, max_intensity=None):
    """Encode an LC-MS map region as a fixed-resolution 2D grayscale image (DeepIso).

    This is the DeepIso (Zohora et al., 2019) encoding: the LC-MS map is binned
    onto a fixed grid and every cell's intensity is squashed to a 0-255 grayscale
    "pixel", exactly as a black-and-white image. The two axes use fixed precision:

    * **RT axis (rows):** one row per MS1 scan (``RT -> 1 MS-scan``). Rows are
      ordered by increasing retention time, so row 0 is the earliest scan.
    * **m/z axis (columns):** fixed ``mz_bin`` bins (0.01 m/z in DeepIso). Peaks
      landing in the same (scan, m/z-bin) cell have their intensities summed.

    Fixing the resolution is the whole point of the comparison with PointIso: it
    forces a grid whether or not real peaks are present, so most pixels end up
    empty (see :func:`lcms_encoding_footprint`).

    Parameters
    ----------
    points : pandas.DataFrame
        Output of :func:`get_lcms_map_region` -- rows of ``scan``, ``rt``, ``mz``,
        ``intensity``.
    mz_bin : float, optional
        Width of each m/z bin (column) in m/z units. Default ``0.01`` (DeepIso).
    mz_range : (float, float), optional
        Inclusive (low, high) m/z span for the columns. Defaults to the min/max
        m/z of ``points``. Peaks outside the range are dropped.
    max_intensity : float, optional
        Intensity mapped to pixel value 255. Defaults to the max intensity in
        ``points``. Pass an explicit value to scale several windows consistently.

    Returns
    -------
    dict
        ``image`` : 2D ``uint8`` array, shape ``(n_scans, n_mz_bins)``, 0-255.
        ``rt_values`` : 1D array, the RT (min) of each row.
        ``scan_values`` : 1D int array, the MS1 scan number of each row.
        ``mz_edges`` : 1D array of length ``n_mz_bins + 1``, the m/z bin edges.
        ``mz_bin`` : the bin width used.
        ``max_intensity`` : the intensity mapped to 255.
    """
    cols = ['scan', 'rt', 'mz', 'intensity']
    if points is None or len(points) == 0:
        return {
            'image': np.zeros((0, 0), dtype=np.uint8),
            'rt_values': np.zeros(0),
            'scan_values': np.zeros(0, dtype=int),
            'mz_edges': np.zeros(0),
            'mz_bin': mz_bin,
            'max_intensity': 0.0,
        }
    df = points[cols]

    if mz_range is None:
        lo_mz, hi_mz = float(df['mz'].min()), float(df['mz'].max())
    else:
        lo_mz, hi_mz = float(mz_range[0]), float(mz_range[1])
        df = df[(df['mz'] >= lo_mz) & (df['mz'] <= hi_mz)]

    # m/z columns: fixed-width bins spanning [lo_mz, hi_mz].
    n_mz = max(1, int(np.ceil((hi_mz - lo_mz) / mz_bin)))
    mz_edges = lo_mz + mz_bin * np.arange(n_mz + 1)

    # RT rows: one per MS1 scan, ordered by retention time.
    scan_order = df[['scan', 'rt']].drop_duplicates().sort_values('rt')
    scan_values = scan_order['scan'].to_numpy(dtype=int)
    rt_values = scan_order['rt'].to_numpy(dtype=float)
    row_of_scan = {s: i for i, s in enumerate(scan_values)}
    n_scans = len(scan_values)

    grid = np.zeros((n_scans, n_mz), dtype=float)
    if len(df):
        rows = df['scan'].map(row_of_scan).to_numpy(dtype=int)
        col = np.floor((df['mz'].to_numpy() - lo_mz) / mz_bin).astype(int)
        col = np.clip(col, 0, n_mz - 1)
        np.add.at(grid, (rows, col), df['intensity'].to_numpy())

    if max_intensity is None:
        max_intensity = float(grid.max()) if grid.size else 0.0
    if max_intensity > 0:
        image = np.clip(np.round(grid / max_intensity * 255.0), 0, 255).astype(np.uint8)
    else:
        image = np.zeros_like(grid, dtype=np.uint8)

    return {
        'image': image,
        'rt_values': rt_values,
        'scan_values': scan_values,
        'mz_edges': mz_edges,
        'mz_bin': mz_bin,
        'max_intensity': max_intensity,
    }


def lcms_point_cloud(points, mz_range=None):
    """Encode an LC-MS map region as a (RT, m/z, intensity) point cloud (PointIso).

    This is the PointIso (Zohora et al., 2021) encoding: instead of binning the
    LC-MS map onto a fixed grid (see :func:`build_lcms_image`), every real peak is
    kept as a single ``(retention time, m/z, intensity)`` triplet at its measured
    coordinates. There is **no binning** -- the m/z and RT axes keep their full
    precision, and only positions where a peak was actually observed are stored.

    That is the whole contrast with the DeepIso image: the image spends memory on
    a dense grid of mostly-empty pixels at a fixed resolution, while the point
    cloud stores only the handful of real peaks at arbitrary precision (and, in the
    4D TimsTOF extension, extends naturally to a fourth ion-mobility coordinate).
    See :func:`lcms_encoding_footprint` for the side-by-side sparsity/memory story.

    Parameters
    ----------
    points : pandas.DataFrame
        Output of :func:`get_lcms_map_region` -- rows of ``scan``, ``rt``, ``mz``,
        ``intensity``.
    mz_range : (float, float), optional
        Inclusive (low, high) m/z span. Defaults to the full range of ``points``.
        Peaks outside the range are dropped, matching :func:`build_lcms_image` so
        the two encodings describe exactly the same window.

    Returns
    -------
    numpy.ndarray
        Float array of shape ``(n_points, 3)`` with columns ``[rt, mz,
        intensity]``, one row per real peak, sorted by ``rt`` then ``mz``. Empty
        ``(0, 3)`` array if ``points`` is empty.
    """
    if points is None or len(points) == 0:
        return np.zeros((0, 3), dtype=float)

    df = points[['rt', 'mz', 'intensity']]
    if mz_range is not None:
        lo_mz, hi_mz = float(mz_range[0]), float(mz_range[1])
        df = df[(df['mz'] >= lo_mz) & (df['mz'] <= hi_mz)]

    if len(df) == 0:
        return np.zeros((0, 3), dtype=float)

    df = df.sort_values(['rt', 'mz'])
    return df.to_numpy(dtype=float)


def lcms_encoding_footprint(image, cloud):
    """Compare the DeepIso image and PointIso point cloud on sparsity and memory.

    This is the core takeaway of notebook 05, quantified: for the *same* LC-MS
    window, how much of the fixed-resolution image is actually empty, and how many
    bytes does each encoding cost? The image (see :func:`build_lcms_image`) spends
    one pixel per (scan, m/z-bin) cell whether or not a peak is there; the point
    cloud (see :func:`lcms_point_cloud`) stores only real peaks. The punchline is
    that a high-resolution window is ~300,000 pixels but only a few thousand real
    points, so the vast majority of the image is empty space.

    Parameters
    ----------
    image : dict
        Output of :func:`build_lcms_image` (uses the ``image`` 2D ``uint8`` array).
    cloud : numpy.ndarray
        Output of :func:`lcms_point_cloud` -- ``(n_points, 3)`` float array.

    Returns
    -------
    dict
        ``n_pixels`` : total grid cells in the image (n_scans x n_mz_bins).
        ``n_filled`` : image cells with a non-zero pixel (a real peak landed there).
        ``n_empty`` : image cells that are zero (wasted on empty space).
        ``fill_fraction`` : ``n_filled / n_pixels`` (0-1); ``sparsity`` is 1 minus it.
        ``sparsity`` : fraction of the image that is empty.
        ``n_points`` : number of real peaks in the point cloud.
        ``image_bytes`` : bytes to store the dense ``uint8`` image grid.
        ``point_cloud_bytes`` : bytes to store the ``(n_points, 3)`` float triplets.
        ``memory_ratio`` : ``image_bytes / point_cloud_bytes`` (image / point cloud).
    """
    grid = np.asarray(image['image']) if isinstance(image, dict) else np.asarray(image)
    cloud = np.asarray(cloud, dtype=float)
    if cloud.ndim != 2 or cloud.shape[1] != 3:
        cloud = cloud.reshape(-1, 3) if cloud.size else np.zeros((0, 3))

    n_pixels = int(grid.size)
    n_filled = int(np.count_nonzero(grid))
    n_empty = n_pixels - n_filled
    fill_fraction = (n_filled / n_pixels) if n_pixels else 0.0

    n_points = int(len(cloud))
    image_bytes = int(grid.nbytes)
    point_cloud_bytes = int(cloud.nbytes)
    memory_ratio = (image_bytes / point_cloud_bytes) if point_cloud_bytes else float('inf')

    return {
        'n_pixels': n_pixels,
        'n_filled': n_filled,
        'n_empty': n_empty,
        'fill_fraction': fill_fraction,
        'sparsity': 1.0 - fill_fraction,
        'n_points': n_points,
        'image_bytes': image_bytes,
        'point_cloud_bytes': point_cloud_bytes,
        'memory_ratio': memory_ratio,
    }


def plot_lcms_heatmap(image, title=None, frame=None):
    """Plot a DeepIso LC-MS image as an RT x m/z heatmap (intensity -> pixel 0-255).

    Renders the fixed-resolution grid produced by :func:`build_lcms_image`: each
    row is one MS1 scan (RT axis), each column is a fixed m/z bin, and the cell
    value is the 0-255 grayscale "pixel". Retention time (minutes) is used for the
    y-axis and m/z-bin centers for the x-axis so the picture is readable, while the
    pixel values are exactly what the DeepIso CNN would ingest.

    Optionally overlays the DeepIso **[15 scans x 211 m/z bins]** framing window as a
    rectangle, so the notebook can show how the model slides a fixed frame across
    the map. Prefers Plotly (interactive), falling back to matplotlib -- matching
    the rest of ``util.py``.

    Parameters
    ----------
    image : dict
        Output of :func:`build_lcms_image` (keys ``image``, ``rt_values``,
        ``mz_edges``, ``mz_bin``, ...).
    title : str, optional
        Plot title. Defaults to a description of the window size.
    frame : bool or dict, optional
        Overlay the DeepIso framing window. ``True`` draws a default
        [15 x 211] frame centered on the brightest pixel. A dict may override:

        * ``n_scans`` (int, default 15) -- frame height in MS1 scans (rows).
        * ``n_mz_bins`` (int, default 211) -- frame width in m/z bins (columns).
        * ``row0`` (int) -- top row of the frame; defaults to centering on the
          brightest pixel's row.
        * ``col0`` (int) -- left column of the frame; defaults to centering on the
          brightest pixel's column.

    Returns
    -------
    plotly.graph_objs.Figure or matplotlib.figure.Figure
        Interactive Plotly heatmap if Plotly is available, else a matplotlib figure.
    """
    grid = np.asarray(image['image'])
    rt_values = np.asarray(image['rt_values'], dtype=float)
    mz_edges = np.asarray(image['mz_edges'], dtype=float)
    mz_bin = float(image.get('mz_bin', 0.01))
    n_scans, n_mz = grid.shape if grid.ndim == 2 else (0, 0)
    mz_centers = (mz_edges[:-1] + mz_edges[1:]) / 2 if len(mz_edges) >= 2 else np.zeros(0)

    if title is None:
        title = f'DeepIso LC-MS image ({n_scans} scans x {n_mz} m/z bins @ {mz_bin} m/z)'

    # Resolve the optional [n_scans x n_mz_bins] framing window into a rectangle.
    frame_rect = None
    if frame and n_scans and n_mz:
        opts = frame if isinstance(frame, dict) else {}
        fr_scans = int(opts.get('n_scans', 15))
        fr_bins = int(opts.get('n_mz_bins', 211))
        if grid.size:
            peak_row, peak_col = np.unravel_index(int(np.argmax(grid)), grid.shape)
        else:
            peak_row, peak_col = 0, 0
        row0 = int(opts.get('row0', peak_row - fr_scans // 2))
        col0 = int(opts.get('col0', peak_col - fr_bins // 2))
        row0 = int(np.clip(row0, 0, max(0, n_scans - 1)))
        col0 = int(np.clip(col0, 0, max(0, n_mz - 1)))
        row1 = min(n_scans - 1, row0 + fr_scans - 1)
        col1 = min(n_mz - 1, col0 + fr_bins - 1)
        frame_rect = {
            'y0': rt_values[row0], 'y1': rt_values[row1],
            'x0': mz_edges[col0], 'x1': mz_edges[col1 + 1],
            'n_scans': fr_scans, 'n_mz_bins': fr_bins,
        }

    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=go.Heatmap(
            z=grid,
            x=mz_centers,
            y=rt_values,
            colorscale='Greys',
            reversescale=True,
            zmin=0, zmax=255,
            colorbar=dict(title='pixel (0-255)'),
            hovertemplate='m/z: %{x:.3f}<br>RT: %{y:.3f} min<br>pixel: %{z}<extra></extra>',
        ))
        if frame_rect is not None:
            fig.add_shape(
                type='rect',
                x0=frame_rect['x0'], x1=frame_rect['x1'],
                y0=frame_rect['y0'], y1=frame_rect['y1'],
                line=dict(color='#D32F2F', width=2),
                fillcolor='rgba(0,0,0,0)',
            )
            fig.add_annotation(
                x=frame_rect['x1'], y=frame_rect['y1'],
                text=f"[{frame_rect['n_scans']} x {frame_rect['n_mz_bins']}] frame",
                showarrow=False, font=dict(color='#D32F2F', size=11),
                xanchor='right', yanchor='bottom',
            )
        fig.update_layout(
            title=title,
            xaxis_title='m/z',
            yaxis_title='Retention time (min)',
            plot_bgcolor='white',
        )
        return fig
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            'Plotly unavailable for plot_lcms_heatmap; falling back to matplotlib'
        )
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 6))
        if grid.size and len(mz_edges) >= 2 and len(rt_values):
            extent = [mz_edges[0], mz_edges[-1], rt_values[-1], rt_values[0]]
            ax.imshow(grid, aspect='auto', cmap='gray_r', vmin=0, vmax=255,
                      extent=extent, interpolation='nearest')
        if frame_rect is not None:
            import matplotlib.patches as mpatches
            ax.add_patch(mpatches.Rectangle(
                (frame_rect['x0'], min(frame_rect['y0'], frame_rect['y1'])),
                frame_rect['x1'] - frame_rect['x0'],
                abs(frame_rect['y1'] - frame_rect['y0']),
                fill=False, edgecolor='#D32F2F', linewidth=2,
            ))
        ax.set_xlabel('m/z')
        ax.set_ylabel('Retention time (min)')
        ax.set_title(title)
        fig.tight_layout()
        return fig


def plot_lcms_point_cloud(cloud, title=None):
    """Plot a PointIso LC-MS point cloud as a 3D (m/z, RT, intensity) scatter.

    Renders the arbitrary-precision triplets produced by
    :func:`lcms_point_cloud`: one marker per real peak at its measured
    ``(m/z, retention time, intensity)``, with no binning. Markers are colored by
    intensity. This is the visual counterpart to :func:`plot_lcms_heatmap` -- the
    same feature, stored as sparse points instead of a dense grid. Prefers Plotly
    (interactive 3D), falling back to a matplotlib 3D scatter.

    Parameters
    ----------
    cloud : numpy.ndarray
        ``(n_points, 3)`` array of ``[rt, mz, intensity]`` rows, as returned by
        :func:`lcms_point_cloud`.
    title : str, optional
        Plot title. Defaults to a description including the point count.

    Returns
    -------
    plotly.graph_objs.Figure or matplotlib.figure.Figure
        Interactive Plotly 3D scatter if Plotly is available, else matplotlib.
    """
    cloud = np.asarray(cloud, dtype=float)
    if cloud.ndim != 2 or cloud.shape[1] != 3:
        cloud = cloud.reshape(-1, 3) if cloud.size else np.zeros((0, 3))
    rt, mz, intensity = cloud[:, 0], cloud[:, 1], cloud[:, 2]

    if title is None:
        title = f'PointIso point cloud ({len(cloud)} real peaks)'

    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=go.Scatter3d(
            x=mz, y=rt, z=intensity,
            mode='markers',
            marker=dict(
                size=3,
                color=intensity,
                colorscale='Viridis',
                colorbar=dict(title='intensity'),
                opacity=0.85,
            ),
            hovertemplate='m/z: %{x:.4f}<br>RT: %{y:.3f} min<br>intensity: %{z:.0f}<extra></extra>',
        ))
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title='m/z',
                yaxis_title='Retention time (min)',
                zaxis_title='intensity',
            ),
        )
        return fig
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            'Plotly unavailable for plot_lcms_point_cloud; falling back to matplotlib'
        )
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection='3d')
        if len(cloud):
            sc = ax.scatter(mz, rt, intensity, c=intensity, cmap='viridis', s=8)
            fig.colorbar(sc, ax=ax, shrink=0.6, label='intensity')
        ax.set_xlabel('m/z')
        ax.set_ylabel('Retention time (min)')
        ax.set_zlabel('intensity')
        ax.set_title(title)
        fig.tight_layout()
        return fig


def plot_MS2(ms2_spectrum, title=None, parent=None):
    """Plot an MS2 spectrum. Prefer converting the matplotlib figure to Plotly
    if plotly.tools.mpl_to_plotly is available, otherwise fall back to
    showing the matplotlib figure directly.
    """
    ax = sup.spectrum(ms2_spectrum)
    # If plotly.tools (tls) and mpl_to_plotly exist, use them for interactive Plotly output
    if tls is not None and hasattr(tls, 'mpl_to_plotly'):
        try:
            plotly_fig = tls.mpl_to_plotly(ax.figure)
            plotly_fig['layout']['plot_bgcolor'] = 'white'
            plotly_fig['layout']['xaxis']['showline'] = True
            plotly_fig['layout']['xaxis']['linecolor'] = 'black'
            plotly_fig['layout']['xaxis']['linewidth'] = 2
            plotly_fig['layout']['yaxis']['linecolor'] = 'black'
            plotly_fig['layout']['yaxis']['linewidth'] = 2
            plotly_fig['layout']['yaxis']['title'] = 'Relative Intensity'
            # Set the title if provided
            if title:
                plotly_fig['layout']['title'] = title
            elif ms2_spectrum and hasattr(ms2_spectrum, 'identifier'):
                plotly_fig['layout']['title'] = f'MS2 Spectrum - Scan {extract_scan_number(ms2_spectrum.identifier)}'
            else:
                plotly_fig['layout']['title'] = 'MS2 Spectrum'
            plotly_fig.update_yaxes(range=[0, 1.05])  # Adjust y-axis range as needed
            return plotly_fig
        except Exception:
            # If conversion fails for any reason, fall through to matplotlib fallback
            import logging
            logging.getLogger(__name__).warning(
                'Failed to convert matplotlib figure to Plotly; falling back to matplotlib display'
            )

    # Fallback: show the matplotlib figure directly
    try:
        import matplotlib.pyplot as plt
        if title:
            ax.set_title(title)
        ax.figure.tight_layout()
        plt.show()
        return ax.figure
    except Exception:
        # As a last resort, return the Axes object so the caller can handle it
        return ax
    
def add_subplot(plotly_fig, fig, row, col, showlegend=False, **kwargs):
    """Add a plotly figure as a subplot to an existing plotly figure at the specified row and column."""
    for trace in fig.data:
        plotly_fig.add_trace(trace, row=row, col=col, **kwargs)
    # Update layout properties if needed
    plotly_fig.update_layout(showlegend=showlegend)

# change to exponential graph of x = bin size, y = collision rate (mean or median) for peaks in a single spectrum.
 
def plot_and_show_statistics_for_collisions(mzml_path, max_spectra=None):
    """
    Analyze bin collisions WITHIN each spectrum.
    
    For each spectrum, counts how many peak pairs fall into the same bin.
    With coarse bins (1.0 Th), many peaks will collide (high collision count).
    With fine bins (0.04 Th), few peaks will collide (low collision count).
    
    Parameters
    ----------
    mzml_path : str
        Path to the mzML file
    max_spectra : int
        Maximum number of spectra to analyze (for performance)
    """
    
    def count_within_spectrum_collisions(mz_array, bin_width):
        """Count collision pairs within a single spectrum at given bin width."""
        from collections import Counter
        
        bin_ids = np.floor(np.asarray(mz_array) / bin_width).astype(np.int64)
        
        # Count how many peaks fall in each bin
        bin_counts = Counter(bin_ids)
        
        # Count total collision pairs: for each bin with n peaks, we have C(n,2) = n*(n-1)/2 collisions
        collision_pairs = sum(count * (count - 1) // 2 for count in bin_counts.values())
        
        return collision_pairs
    
    # Get all spectra
    all_spectra = get_all_MS2_objects(mzml_path=mzml_path, max_spectra=max_spectra)
    if max_spectra is not None and len(all_spectra) > max_spectra:
        all_spectra = all_spectra[:max_spectra]
    n_spectra = len(all_spectra)
    
    bin_widths = (1.0, 0.04)
    
    # Count within-spectrum collisions for each spectrum and bin width
    collisions_by_width = {width: [] for width in bin_widths}
    spectrum_sizes = []
    
    for spectrum in all_spectra:
        spectrum_sizes.append(len(spectrum.mz))
        for width in bin_widths:
            collision_count = count_within_spectrum_collisions(spectrum.mz, width)
            collisions_by_width[width].append(collision_count)
    
    # Convert to arrays
    collisions_1da = np.array(collisions_by_width[1.0])
    collisions_004da = np.array(collisions_by_width[0.04])
    spectrum_sizes = np.array(spectrum_sizes)
    
    # Compute collision rates (collisions per max possible peak pairs in spectrum)
    # Max possible collisions for a spectrum with n peaks is C(n,2) = n*(n-1)/2
    max_possible_collisions = spectrum_sizes * (spectrum_sizes - 1) / 2
    collision_rate_1da = collisions_1da / (max_possible_collisions)
    collision_rate_004da = collisions_004da / (max_possible_collisions)
    
    # Summary statistics
    print(f"=== Within-Spectrum Collision Analysis ===")
    print(f"File: {mzml_path}")
    print(f"Spectra analyzed: {n_spectra}")
    print(f"Mean spectrum size: {spectrum_sizes.mean():.1f} peaks")

    print(f"\n--- Bin Size = 1.0 Th ---")
    print(f"  Mean collision pairs per spectrum: {collisions_1da.mean():.1f}")
    print(f"  Median collision pairs: {np.median(collisions_1da):.1f}")
    print(f"  Max collision pairs: {collisions_1da.max():.0f}")
    print(f"  Mean collision rate (% of max possible): {collision_rate_1da.mean()*100:.2f}%")

    print(f"\n--- Bin Size = 0.04 Th ---")
    print(f"  Mean collision pairs per spectrum: {collisions_004da.mean():.1f}")
    print(f"  Median collision pairs: {np.median(collisions_004da):.1f}")
    print(f"  Max collision pairs: {collisions_004da.max():.0f}")
    print(f"  Mean collision rate (% of max possible): {collision_rate_004da.mean()*100:.2f}%")
    
    print(f"\n--- Improvement ---")
    print(f"  Reduction in mean collisions (0.04 vs 1.0 Th): {(1 - collisions_004da.mean()/collisions_1da.mean())*100:.1f}%")

    # Visualization: Distribution of collision counts within spectra
    fig, axes = subplots(1, 2, figsize=(14, 5))

    # Left: 1.0 Th collisions
    axes[0].hist(collisions_1da, bins=30, alpha=0.7, color='coral', edgecolor='black')
    axes[0].axvline(collisions_1da.mean(), color='red', linestyle='--', 
                    linewidth=2, label=f"Mean: {collisions_1da.mean():.1f}")
    axes[0].set_xlabel('Collision Pairs Within Spectrum')
    axes[0].set_ylabel('Frequency (# of spectra)')
    axes[0].set_title('Within-Spectrum Collisions (Bin = 1.0 Th)\nHigher = More False Positives')
    axes[0].set_xticks(np.arange(collisions_1da.min(), collisions_1da.max() + 1, 1))
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Right: 0.04 Th collisions
    axes[1].hist(collisions_004da, bins=30,  # Match the number of bins to the left plot
                 alpha=0.7, color='steelblue', edgecolor='black')
    axes[1].axvline(collisions_004da.mean(), color='darkblue', linestyle='--', 
                    linewidth=2, label=f"Mean: {collisions_004da.mean():.1f}")
    axes[1].set_xlabel('Collision Pairs Within Spectrum')
    axes[1].set_ylabel('Frequency (# of spectra)')
    axes[1].set_title('Within-Spectrum Collisions (Bin = 0.04 Th)\nLower = Better Discrimination')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xticks(np.arange(collisions_004da.min(), collisions_004da.max() + 1, 1))

    plt.tight_layout()
    plt.show()


# @title Proving Similarity preservation empirically 
def prove_similarity_preservation_plots_and_statistics(mzml_path, bin_width = 0.04, hash_buckets = 10000, max_spectra=300, 
                                                       spectra_idx_to_compare=None, k_means=None):
    import mmh3
    import re
      # Demonstrate similarity preservation between original sparse maps and hashed vectors
      # Let's get multiple spectra and compare their similarities

    def get_scan_number_from_spectrum_id(spectrum_id):
        """Extract scan number from spectrum ID string."""    
        match = re.search(r'scan=(\d+)', spectrum_id)
        if match:
            return int(match.group(1))
        else:
            raise ValueError(f"Could not extract scan number from spectrum ID: {spectrum_id}")

    # Get spectra (stop early if max_spectra provided)
    spectra_to_compare = None
    if spectra_idx_to_compare is not None:
        spectra_to_compare = get_all_MS2_objects(mzml_path)
        scan_num = lambda s: get_scan_number_from_spectrum_id(s.identifier)
        spectra_to_compare = [s for s in spectra_to_compare if scan_num(s) in spectra_idx_to_compare]
    elif max_spectra is not None:
        spectra_to_compare = get_all_MS2_objects(mzml_path, max_spectra=max_spectra)
        spectra_to_compare = spectra_to_compare[:max_spectra]
    else:
        spectra_to_compare = get_all_MS2_objects(mzml_path)

    # make sure all the spectra we loaded have peaks!
    n_spectra_before = len(spectra_to_compare)
    spectra_to_compare = [s for s in spectra_to_compare if len(s.intensity) > 0]
    n_spectra = len(spectra_to_compare)
    scan_numbers = [get_scan_number_from_spectrum_id(s.identifier) for s in spectra_to_compare]

    print(f"Comparing {n_spectra} spectra (out of {n_spectra_before} loaded)")

    # Convert each spectrum to sparse map and hash vector representations
    sparse_maps = []
    hash_vectors = []
    
    WIDTH_OF_BIN = bin_width
    hash_buckets = hash_buckets  # Increased from 800 to reduce collisions with ~100k dimensional space

    def normalize_intensity():
        """Normalize intensities across all spectra to range [0,1]"""
        # Collect all intensities from all spectra
        all_intensities = []
        for ms2 in spectra_to_compare:
            all_intensities.extend(ms2.intensity)

        print(f"Before normalization:\n Mean intensity: {np.mean(all_intensities)}\n " 
              f"Median intensity: {np.median(all_intensities)}")
        
        max_int = max(all_intensities)
        min_int = min(all_intensities)
        
        def normalize_formula(intensity_array):
            res = []
            for intensity in intensity_array:
                int = (intensity - min_int) / (max_int - min_int)
                res.append(int)
            return res
        # Create normalized spectra tuples (mz, normalized_intensity)
        normalized_spectra = []
        for ms2 in spectra_to_compare:
            normalized_intensities = normalize_formula(ms2.intensity)
            # Create tuple of (mz_array, normalized_intensity_array)
            normalized_spectrum = (ms2.mz, normalized_intensities)
            normalized_spectra.append(normalized_spectrum)
        
        return normalized_spectra

        # Get normalized data
     # normalized_spectra_tuples = normalize_intensity()

    # Mutate spectra_to_compare to use normalized data
    """     spectra_to_compare = [
        type('NormalizedSpectrum', (), {
            'mz': mz_array, 
            'intensity': intensity_array
        })() 
        for mz_array, intensity_array in normalized_spectra_tuples
    ] """


    def create_sparse_map(mz_array, intensity_array): # same as our code above.
        """Convert spectrum to sparse map representation"""
        sparse_map = {}
        for mz, intensity in zip(mz_array, intensity_array):
            idx = int(mz // WIDTH_OF_BIN)
            sparse_map[idx] = sparse_map.get(idx, 0) + intensity
        return sparse_map

    def hash_bucket_and_sign(sparse_idx, num_buckets=hash_buckets):
        """Map a sparse index to a bucket and a deterministic sign for signed hashing."""
        bucket_idx = mmh3.hash(str(sparse_idx), seed=42) % num_buckets
        sign = 1 if mmh3.hash(str(sparse_idx), seed=43) % 2 == 0 else -1
        return bucket_idx, sign

    def sparse_map_to_hash_vector(sparse_map, num_buckets=hash_buckets):
        """Convert sparse map to a signed hash vector."""
        hash_vec = [0] * num_buckets
        for sparse_idx, intensity in sparse_map.items():
            bucket_idx, sign = hash_bucket_and_sign(sparse_idx, num_buckets)
            hash_vec[bucket_idx] += sign * intensity
        return hash_vec
    
    def sparse_map_to_hash_vector_2(sparse_map, key_to_hash, num_buckets=hash_buckets):
        """Convert sparse map to a signed hash vector using pre-computed mappings."""
        hash_vec = [0] * num_buckets
        for sparse_idx, intensity in sparse_map.items():
            hash_info = key_to_hash.get(sparse_idx)
            if hash_info is not None:
                bucket_idx, sign = hash_info
                hash_vec[bucket_idx] += sign * intensity
        return hash_vec

    def cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors (returns value between 0 and 1)"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Calculate dot product
        dot_prod = np.dot(vec1, vec2)
        
        # Calculate magnitudes
        norm1 = np.linalg.norm(vec1) # here's the "cosine" part of cosine_similarity
        norm2 = np.linalg.norm(vec2)
        
        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity = dot_product / (norm1 * norm2)
        return dot_prod / (norm1 * norm2)
    
    def sparse_cosine_similarity(map1, map2):
        """Calculate cosine similarity between two sparse maps (returns value between 0 and 1)"""
        # Get all unique indices from both maps
        all_indices = set(map1.keys()) | set(map2.keys())
        
        # Convert sparse maps to dense vectors for the shared indices

        vec1 = np.array([map1.get(idx, 0.0) for idx in sorted(all_indices)])
        vec2 = np.array([map2.get(idx, 0.0) for idx in sorted(all_indices)])
        # Calculate cosine similarity using the dot_product function
        return cosine_similarity(vec1, vec2)


    sparse_map_keys = set()
    # Create representations for each spectrum
    for spec_data in spectra_to_compare:
        sparse_map = create_sparse_map(spec_data.mz, spec_data.intensity)
        sparse_map_keys |= set(sparse_map.keys())
        sparse_maps.append(sparse_map)
    
    # Create dictionary mapping sparse-map keys to signed hash outputs.
    key_to_hash = {}
    for key in sparse_map_keys:
        key_to_hash[key] = hash_bucket_and_sign(key, hash_buckets)
     
    # Now create hash vectors using the pre-computed signed hash mapping.
    for sparse_map in sparse_maps:
        hash_vec = sparse_map_to_hash_vector_2(sparse_map, key_to_hash, hash_buckets)
        hash_vectors.append(hash_vec)

    Xh = np.array(hash_vectors)

    # Build full dense unhashed matrix from sparse_maps (no compression)
    all_indices = set()
    for sm in sparse_maps:
        all_indices |= set(sm.keys())

    print(f"Total unique bins across all spectra: {len(all_indices)}")

    max_idx = max(all_indices)
    n_bins = max_idx + 1
    
    def remap(sm_):
        arr = np.zeros(n_bins, dtype=float)
        for k, v in sm_.items():
            arr[k] = v
        return arr

    Xs = np.vstack([remap(sm) for sm in sparse_maps])
    
    # L2 normalize each spectrum vector to unit length before scaling
    from sklearn.preprocessing import normalize
    Xs = normalize(Xs, norm='l2', axis=1)
    Xh = normalize(Xh, norm='l2', axis=1)  # Also normalize hashed vectors

    # Scale to reduce outlier influence
    scaler_s = RobustScaler().fit(Xs)
    scaler_h = RobustScaler().fit(Xh)
    Xs_scaled = scaler_s.transform(Xs)
    Xh_scaled = scaler_h.transform(Xh)
    
    # 1) Compute PCA on the unhashed (Xs_scaled) data
    max_pcs = min(50, Xs_scaled.shape[1], Xs_scaled.shape[0])
    pca_full = PCA(n_components=max_pcs, random_state=0).fit(Xs_scaled)
    var_ratio = pca_full.explained_variance_ratio_
    cum_var = np.cumsum(var_ratio)


    # 2) Choose a reasonable number of PCs based on the scree/cumulative variance:
    #    aim for the number of components that explain ~90% variance but clamp between 5 and 25
    pcs_for_downstream = int(np.searchsorted(cum_var, 0.90) + 1)
    
    # make sure bounds make sense
    pcs_for_downstream = max(5, pcs_for_downstream)
    pcs_for_downstream = min(25, pcs_for_downstream, len(var_ratio))

    # Project unhashed and hashed data into PCA subspaces.
    # Fit PCA separately for unhashed and hashed data to avoid feature-size mismatch
    pca_reducer_s = PCA(n_components=pcs_for_downstream, random_state=0).fit(Xs_scaled)
    Xs_pca = pca_reducer_s.transform(Xs_scaled)

    # For hashed data, ensure the requested n_components is valid for its shape
    pcs_h = min(pcs_for_downstream, Xh_scaled.shape[1], Xh_scaled.shape[0])
    if pcs_h < 1:
        pcs_h = 1
    pca_reducer_h = PCA(n_components=pcs_h, random_state=0).fit(Xh_scaled)
    Xh_pca = pca_reducer_h.transform(Xh_scaled)
    
    # t-SNE on combined data ensures both representations share the same embedded space
    # 1. Compute pairwise cosine similarities for both representations
    print("Computing pairwise similarities...")
    n_spectra = len(sparse_maps)
    sparse_similarities = np.zeros((n_spectra, n_spectra))
    hash_similarities = np.zeros((n_spectra, n_spectra))

    for i in range(n_spectra):
        print(f"  Processing spectrum {i+1}/{n_spectra}", end='\r')
        for j in range(i, n_spectra):  # Only compute upper triangle
            sparse_sim = sparse_cosine_similarity(sparse_maps[i], sparse_maps[j])
            hash_sim = cosine_similarity(hash_vectors[i], hash_vectors[j])
            
            sparse_similarities[i, j] = sparse_sim
            sparse_similarities[j, i] = sparse_sim  # Symmetric
            hash_similarities[i, j] = hash_sim
            hash_similarities[j, i] = hash_sim

    # 2. Extract upper triangle (excluding diagonal) for correlation analysis
    upper_indices = np.triu_indices(n_spectra, k=1)
    sparse_upper = sparse_similarities[upper_indices]
    hash_upper = hash_similarities[upper_indices]
    
    perp = min(30, max(5, (n_spectra // 3)))

    import umap
    umap_s = umap.UMAP(n_components=2, n_neighbors=perp, min_dist=0.1, random_state=0)
    umap_h = umap.UMAP(n_components=2, n_neighbors=perp, min_dist=0.1, random_state=0)
    Xs2 = umap_s.fit_transform(Xs_pca)
    Xh2 = umap_h.fit_transform(Xh_pca)

    # Cluster on the unhashed representation only, then reuse those labels on both plots.
    if k_means is not None:
        N_CLUSTERS = k_means
    else:
        N_CLUSTERS = 12

    try:
        km_reference = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(Xs2)
        km_hashed = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(Xh2)
    except Exception as e:
        logging.getLogger(__name__).warning('KMeans failed: %s', e)
        return
    
    labels_shared = km_reference.labels_
    labels_hashed = km_hashed.labels_

    # Calculate per-plot centers from the shared reference labels.
    centers_s = np.array([Xs2[labels_shared == k].mean(axis=0) if (labels_shared == k).any() 
                        else np.zeros(Xs2.shape[1]) for k in range(N_CLUSTERS)])
    centers_h = np.array([Xh2[labels_shared == k].mean(axis=0) if (labels_shared == k).any() 
                        else np.zeros(Xh2.shape[1]) for k in range(N_CLUSTERS)])

    # Detect outliers relative to the shared labels in each embedding.
    dists_s = np.linalg.norm(Xs2 - centers_s[labels_shared], axis=1)
    dists_h = np.linalg.norm(Xh2 - centers_h[labels_shared], axis=1)
    thr_s = np.percentile(dists_s, 90)
    thr_h = np.percentile(dists_h, 90)
    out_s = dists_s > thr_s
    out_h = dists_h > thr_h

        # 7. Create visualizations
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1])

    from scipy.stats import pearsonr, spearmanr
    from sklearn.metrics import adjusted_rand_score
    pearson_corr, pearson_pval = pearsonr(sparse_upper, hash_upper)
    ari_score = adjusted_rand_score(labels_shared, labels_hashed)

    from IPython.display import display, Markdown

    # Replace print statements with display for pretty printing
    display(Markdown(f"""
---
### SIMILARITY PRESERVATION METRICS
---
- **Pearson correlation**:  {pearson_corr:.4f} (p-value: {pearson_pval:.2e})
- **Adjusted Rand Index (independent KMeans on UMAP spaces)**: {ari_score:.4f}
- **Number of pairwise comparisons**: {len(sparse_upper):,}
- **Mean absolute error**: {np.mean(np.abs(sparse_upper - hash_upper)):.4f}
---
"""))

    # Top row: Scatter plot comparing similarities
    ax_scatter = fig.add_subplot(gs[0, :])
    ax_scatter.scatter(sparse_upper, hash_upper, alpha=0.3, s=10, edgecolors='none')
    lower_bound = min(0.0, float(np.min(sparse_upper)), float(np.min(hash_upper)))
    upper_bound = max(1.0, float(np.max(sparse_upper)), float(np.max(hash_upper)))
    ax_scatter.plot([lower_bound, upper_bound], [lower_bound, upper_bound], 'r--', linewidth=2, label='Perfect preservation')
    ax_scatter.set_xlabel('Unhashed (Sparse) Cosine Similarity', fontsize=12)
    ax_scatter.set_ylabel('Hashed Cosine Similarity', fontsize=12)
    ax_scatter.set_title(f'Pairwise Similarity Preservation\n' + 
                        f'Pearson r={pearson_corr:.4f}',
                        fontsize=12)  # Match the bottom title font size
    ax_scatter.legend()
    ax_scatter.grid(alpha=0.3)
    ax_scatter.set_xlim(lower_bound, upper_bound)
    ax_scatter.set_ylim(lower_bound, upper_bound)
    ax_scatter.set_aspect('equal')
    
    plt.show()
    
    
    
    # Create visualization with shared colors
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    def plot_with_shared_colors(ax, X2, centers, labels, out_mask, title):
        """Plot with colors based on unhashed reference labels."""
        # Plot points with shared colors
        ax.scatter(X2[~out_mask,0], X2[~out_mask,1], c=labels[~out_mask], 
                cmap='tab20', s=28, edgecolor='k', linewidth=0.2)
        if out_mask.any():
            ax.scatter(X2[out_mask,0], X2[out_mask,1], c='lightgray', 
                    s=18, alpha=0.8, label='outliers')
        ax.scatter(centers[:,0], centers[:,1], c='k', marker='x', s=60)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('Dim1')
        ax.set_ylabel('Dim2')
        ax.grid(alpha=0.25)

        from matplotlib.lines import Line2D

        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='HNGPEHWHKDFPIANGER',
                markerfacecolor='#e377c3', markersize=8),
            Line2D([0], [0], marker='o', color='w', label='RMVNNGHSFNVEYDDSQDK',
                markerfacecolor='#9edbe5', markersize=8),
            Line2D([0], [0], marker='o', color='w', label='MVNNGHSFNVEYDDSQDKAVLK',
                markerfacecolor='#2d9d2c', markersize=8),
            Line2D([0], [0], marker='o', color='w', label='SHHWGYGK',
                markerfacecolor='#bcbd22', markersize=8),
            Line2D([0], [0], marker='o', color='w', label='QSPVDIDTK',
                markerfacecolor='#1e78b4', markersize=8),
            Line2D([0], [0], marker='o', color='w', label='LVQFHFHWGSSDDQGSEHTVDRK',
                markerfacecolor='#9567bd', markersize=8),
        ]
        ax.legend(handles=legend_elements, title="Peptide Key", loc='center')

    plot_with_shared_colors(axes[0], Xs2, centers_s, labels_shared, out_s,
                            f'Unhashed UMAP - {N_CLUSTERS} reference clusters')
    plot_with_shared_colors(axes[1], Xh2, centers_h, labels_shared, out_h,
                            f'Hashed UMAP ({hash_buckets} buckets) - colored by unhashed labels')

    plt.tight_layout()
    plt.show()


def plot_theoretical_ions(b_mz, y_mz, peptide):
    # Peak height scaling (b1/y1 highest, b20/y20 lowest)
    max_height = 0.9
    min_height = 0.1
    b_heights = np.linspace(max_height, min_height, len(b_mz))
    y_heights = np.linspace(max_height, min_height, len(y_mz))

    # Plot
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    ax.vlines(b_mz, 0, b_heights, colors='#1976D2', linewidth=1.5, label='b-ions')
    ax.vlines(y_mz, 0, y_heights, colors='#D32F2F', linewidth=1.5, label='y-ions')

    ax.set_ylim(0, 1.1)
    ax.set_xlabel("m/z")
    ax.set_ylabel("Intensity (scaled)")
    ax.set_title(f"Theoretical ions for {peptide}")
    ax.legend(loc='upper center') 
    ax.grid(True, axis='y', alpha=0.25)

    # Labels
    for i, (x, h) in enumerate(zip(b_mz, b_heights), start=1):
        ax.text(x, h + 0.02, f"b{i}", rotation=90, ha="center", va="bottom", fontsize=8)
    for i, (x, h) in enumerate(zip(y_mz, y_heights), start=1):
        j = len(y_mz) - i + 1 #count right to left
        ax.text(x, h + 0.02, f"y{j}", rotation=90, ha="center", va="bottom", fontsize=8)

    plt.show()

# This function should read in an mzml file and return an object of type SpectrumWithTransformations
# Based off of get_MS2_object from Sam Payne lesson 4
def get_SWT_object(
    mzml_path: str,
    scan_number: int,
    full_sequence = None,
) -> "SpectrumWithTransformations":
    
    index = scan_number -1 #scan_number is 1-based, index is 0-based
    with mzml.MzML(mzml_path, use_index=True) as reader: #use_index=True allows us to avoid reading through the entire mzml file
        selected_spectrum = reader.get_by_index(index)
    # Test to see if we accessed the correct scan: PASSED!
    # precursor_mz = selected_spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
    # print(precursor_mz)
    
    # This finds the cooresponding values in the .mzml file to create our MS2 for a given scan (see the params)
    spectrum_id = selected_spectrum['id']
    retention_time = selected_spectrum['scanList']['scan'][0]['scan start time']
    precursor_mz = selected_spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
    precursor_charge = int(selected_spectrum['precursorList']['precursor'][0]['selectedIonList']['selectedIon'][0]['charge state'])
    mz_array = np.asarray(selected_spectrum['m/z array'])
    intensity_array = np.asarray(selected_spectrum['intensity array'])
    
    swt_object = SpectrumWithTransformations.SpectrumWithTransformations(
        identifier=spectrum_id,
        scan_number=scan_number,
        precursor_mz=precursor_mz,
        precursor_charge=precursor_charge,
        mz_array=mz_array,
        intensity_array=intensity_array,
        retention_time=retention_time,
        annotation_dictionary=None,
        binned_mz=None,
        hashed_mz=None,
    )

    if full_sequence:
        swt_object = swt_object.annotate_proforma(
            proforma_str = full_sequence,
            fragment_tol_mass = 10, # We consider two peaks (actual and theoretical) "equivalent" if they are within +/- 0.01 Th
            fragment_tol_mode = 'ppm',
            ion_types = 'by',
            max_ion_charge = max(1, precursor_charge - 1)
        )
    return swt_object