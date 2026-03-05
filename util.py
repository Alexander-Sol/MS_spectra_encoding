import re

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
import pandas as pd


from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler
import umap



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
                                    .remove_precursor_peak(fragment_tol_mass=0.5, fragment_tol_mode='Da')
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
            scanNumber = int(spectrum['id'].split('=')[-1])
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
                su_spectrum = (su_spectrum.filter_intensity(0.05, 100)
                            .remove_precursor_peak(fragment_tol_mass=0.5, fragment_tol_mode='Da')
                            .scale_intensity('root'))
                break
    # Formatting
    if su_spectrum:
        fragment_tol_mass = 0.5
        fragment_tol_mode = 'Da'  ## for some reason, if I use 'ppm' it doesn't work

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
            scanNumber = int(spectrum['id'].split('=')[-1])
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
            else:
                plotly_fig['layout']['title'] = f'MS1 Spectrum - Scan {ms2_spectrum.scan_number}'
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


def plot_and_show_statistics_for_collisions(mzml_path, max_spectra=None, spectra_to_compare=None):
    """
    Analyze bin collisions between pairs of spectra.
    
    For each pair of spectra, counts how many bins they share in common.
    With coarse bins (1.0 Da), different spectra will falsely share many bins.
    With fine bins (0.01 Da), truly different spectra should share very few bins.
    
    Parameters
    ----------
    mzml_path : str
        Path to the mzML file
    max_spectra : int
        Maximum number of spectra to analyze (for performance)
    spectra_to_compare : list of ints specifcying scan numbers to compare (if None, will use all spectra up to max_spectra)
    """
    
    def spectrum_to_bin_set(mz_array, bin_width):
        """Convert spectrum m/z values to a set of bin indices."""
        bin_ids = np.floor(np.asarray(mz_array) / bin_width).astype(np.int64)
        return set(bin_ids)
    
    # Get all spectra
    all_spectra = get_all_MS2_objects(mzml_path=mzml_path, max_spectra=max_spectra)
    if spectra_to_compare is not None:
        all_spectra = [s for s in all_spectra if s.scan_number in spectra_to_compare]
    elif max_spectra is not None and len(all_spectra) > max_spectra:
        all_spectra = all_spectra[:max_spectra]
    n_spectra = len(all_spectra)
    
    bin_widths = (1.0, 0.01, 500.0)
    
    # Pre-compute bin sets for all spectra at both bin widths
    bin_sets = {}
    for width in bin_widths:
        bin_sets[width] = [spectrum_to_bin_set(ms2.mz, width) for ms2 in all_spectra]
    
    # For each PAIR of spectra, count shared bins (collisions)
    pairwise_collisions = {width: [] for width in bin_widths}
    
    for i in range(n_spectra):
        for j in range(i + 1, n_spectra):  # Only upper triangle, no self-comparison
            for width in bin_widths:
                bins_i = bin_sets[width][i]
                bins_j = bin_sets[width][j]
                shared_bins = len(bins_i & bins_j)  # Intersection = shared bins
                # Normalize by the smaller spectrum's size
                min_size = min(len(bins_i), len(bins_j))
                collision_rate = shared_bins / min_size if min_size > 0 else 0
                pairwise_collisions[width].append(collision_rate)
    
    # Convert to arrays for statistics
    collisions_1da = np.array(pairwise_collisions[1.0])
    collisions_001da = np.array(pairwise_collisions[0.01])
    collisions_500da = np.array(pairwise_collisions[500.0])
    
    n_pairs = len(collisions_1da)
    
    # Summary statistics
    print(f"=== Pairwise Spectrum Collision Analysis ===")
    print(f"File: {mzml_path}")
    print(f"Spectra analyzed: {n_spectra}")
    print(f"Total pairs compared: {n_pairs:,}")
    
    print(f"\n--- Bin Size = 500.0 Da ---")
    print(f"  Mean collision rate per pair: {collisions_500da.mean()*100:.2f}%")
    print(f"  Median collision rate: {np.median(collisions_500da)*100:.2f}%")
    print(f"  Max collision rate: {collisions_500da.max()*100:.2f}%")
    print(f"  Pairs with >50% collision: {(collisions_500da > 0.5).sum():,} ({(collisions_500da > 0.5).mean()*100:.1f}%)")

    print(f"\n--- Bin Size = 1.0 Da ---")
    print(f"  Mean collision rate per pair: {collisions_1da.mean()*100:.2f}%")
    print(f"  Median collision rate: {np.median(collisions_1da)*100:.2f}%")
    print(f"  Max collision rate: {collisions_1da.max()*100:.2f}%")
    print(f"  Pairs with >50% collision: {(collisions_1da > 0.5).sum():,} ({(collisions_1da > 0.5).mean()*100:.1f}%)")
    
    print(f"\n--- Bin Size = 0.01 Da ---")
    print(f"  Mean collision rate per pair: {collisions_001da.mean()*100:.2f}%")
    print(f"  Median collision rate: {np.median(collisions_001da)*100:.2f}%")
    print(f"  Max collision rate: {collisions_001da.max()*100:.2f}%")
    print(f"  Pairs with >50% collision: {(collisions_001da > 0.5).sum():,} ({(collisions_001da > 0.5).mean()*100:.1f}%)")
        
    print(f"\n--- Improvement ---")
    print(f"  Reduction in mean collision rate (0.01 vs 1.0 Da): {(1 - collisions_001da.mean()/collisions_1da.mean())*100:.1f}%")
    print(f"  Change in mean collision rate (500.0 vs 1.0 Da): {(1 - collisions_500da.mean()/collisions_1da.mean())*100:.1f}%")
    
    # Visualization: Distribution of collision rates (now including 500 Da)
    fig, axes = subplots(1, 3, figsize=(21, 5))
    
    # Left: 500.0 Da bin collisions
    axes[2].hist(collisions_500da * 100, bins=30, alpha=0.7, color='seagreen', edgecolor='black')
    axes[2].axvline(collisions_500da.mean() * 100, color='darkgreen', linestyle='--', 
                    linewidth=2, label=f"Mean: {collisions_500da.mean()*100:.1f}%")
    axes[2].set_xlabel('Collision Rate Between Spectrum Pairs (%)')
    axes[2].set_ylabel('Frequency')
    axes[2].set_title('Pairwise Collisions (Bin = 500.0 Da)\nVery Large Bins => High False Similarity')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    # Middle: 1.0 Da bin collisions
    axes[0].hist(collisions_1da * 100, bins=30, alpha=0.7, color='coral', edgecolor='black')
    axes[0].axvline(collisions_1da.mean() * 100, color='red', linestyle='--', 
                    linewidth=2, label=f"Mean: {collisions_1da.mean()*100:.1f}%")
    axes[0].set_xlabel('Collision Rate Between Spectrum Pairs (%)')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Pairwise Collisions (Bin = 1.0 Da)\nHigher = More False Similarity')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Right: 0.01 Da bin collisions
    axes[1].hist(collisions_001da * 100, bins=30, alpha=0.7, color='steelblue', edgecolor='black')
    axes[1].axvline(collisions_001da.mean() * 100, color='darkblue', linestyle='--', 
                    linewidth=2, label=f"Mean: {collisions_001da.mean()*100:.1f}%")
    axes[1].set_xlabel('Collision Rate Between Spectrum Pairs (%)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Pairwise Collisions (Bin = 0.01 Da)\nLower = Better Discrimination')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


# @title Proving Similarity preservation empirically 
def prove_similarity_preservation_plots_and_statistics(mzml_path, bin_width = 0.04, hash_buckets = 10000, max_spectra=300, spectra_idx_to_compare=None):
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
    normalized_spectra_tuples = normalize_intensity()

    # Mutate spectra_to_compare to use normalized data
    spectra_to_compare = [
        type('NormalizedSpectrum', (), {
            'mz': mz_array, 
            'intensity': intensity_array
        })() 
        for mz_array, intensity_array in normalized_spectra_tuples
    ]


    def create_sparse_map(mz_array, intensity_array): # same as our code above.
        """Convert spectrum to sparse map representation"""
        sparse_map = {}
        for mz, intensity in zip(mz_array, intensity_array):
            idx = int(mz // WIDTH_OF_BIN)
            sparse_map[idx] = intensity
        return sparse_map

    def sparse_map_to_hash_vector(sparse_map, num_buckets=hash_buckets):
        """Convert sparse map to hash vector"""
        hash_vec = [0] * num_buckets
        for sparse_idx, intensity in sparse_map.items():
            bucket_idx = mmh3.hash(str(sparse_idx), seed=42) % num_buckets
            hash_vec[bucket_idx] += intensity
        return hash_vec
    
    def sparse_map_to_hash_vector_2(sparse_map, key_to_bucket, num_buckets=hash_buckets):
        """Convert sparse map to hash vector using pre-computed key_to_bucket mapping"""
        hash_vec = [0] * num_buckets
        for sparse_idx, intensity in sparse_map.items():
            bucket_idx = key_to_bucket.get(sparse_idx)
            if bucket_idx is not None:
                hash_vec[bucket_idx] += intensity
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
    
    # Create dictionary mapping sparse map keys to their hashed bucket indices (for analysis)
    key_to_bucket = {}
    for key in sparse_map_keys:
        bucket_idx = mmh3.hash(str(key), seed=42) % hash_buckets
        key_to_bucket[key] = bucket_idx
     
    # Now create hash vectors using the new mapping function that relies on pre-computed key_to_bucket
    for sparse_map in sparse_maps:
        hash_vec = sparse_map_to_hash_vector_2(sparse_map, key_to_bucket, hash_buckets)
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
    
    # Ensure both PCA matrices have same number of columns for concatenation
    min_cols = min(Xs_pca.shape[1], Xh_pca.shape[1])
    Xs_pca_aligned = Xs_pca[:, :min_cols]
    Xh_pca_aligned = Xh_pca[:, :min_cols]
    
    # Run UMAP on combined data
    combined_pca = np.vstack([Xs_pca_aligned, Xh_pca_aligned])
    umap_combined = umap.UMAP(n_components=2, n_neighbors=perp, min_dist=0.1, random_state=0)
    combined_2d = umap_combined.fit_transform(combined_pca)
    
    # Split back into unhashed and hashed embeddings
    Xs2 = combined_2d[:n_spectra]
    Xh2 = combined_2d[n_spectra:]
    
    # Cluster on the combined 2D embedding with shared clustering
    N_CLUSTERS = 12
    try:
        km_combined = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(combined_2d)
    except Exception as e:
        logging.getLogger(__name__).warning('KMeans failed: %s', e)
        return
    
    labels_shared = km_combined.labels_[:n_spectra]  # Use first half for both plots

    # Calculate centers for visualization based on actual cluster assignments in shared space
    # Handle empty clusters by checking if they have points
    centers_s = np.array([Xs2[labels_shared == k].mean(axis=0) if (labels_shared == k).any() 
                        else np.zeros(Xs2.shape[1]) for k in range(N_CLUSTERS)])
    centers_h = np.array([Xh2[labels_shared == k].mean(axis=0) if (labels_shared == k).any() 
                        else np.zeros(Xh2.shape[1]) for k in range(N_CLUSTERS)])

    # Detect outliers using shared clustering
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
    pearson_corr, pearson_pval = pearsonr(sparse_upper, hash_upper)

    from IPython.display import display, Markdown

    # Replace print statements with display for pretty printing
    display(Markdown(f"""
---
### SIMILARITY PRESERVATION METRICS
---
- **Pearson correlation**:  {pearson_corr:.4f} (p-value: {pearson_pval:.2e})
- **Number of pairwise comparisons**: {len(sparse_upper):,}
- **Mean absolute error**: {np.mean(np.abs(sparse_upper - hash_upper)):.4f}
---
"""))

    # Top row: Scatter plot comparing similarities
    ax_scatter = fig.add_subplot(gs[0, :])
    ax_scatter.scatter(sparse_upper, hash_upper, alpha=0.3, s=10, edgecolors='none')
    ax_scatter.plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect preservation')
    ax_scatter.set_xlabel('Unhashed (Sparse) Cosine Similarity', fontsize=12)
    ax_scatter.set_ylabel('Hashed Cosine Similarity', fontsize=12)
    ax_scatter.set_title(f'Pairwise Similarity Preservation\n' + 
                        f'Pearson r={pearson_corr:.4f}',
                        fontsize=12)  # Match the bottom title font size
    ax_scatter.legend()
    ax_scatter.grid(alpha=0.3)
    ax_scatter.set_xlim(0, 1)
    ax_scatter.set_ylim(0, 1)
    ax_scatter.set_aspect('equal')
    
    plt.show()
    
    
    
    # Create visualization with shared colors
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    def plot_with_shared_colors(ax, X2, centers, labels, out_mask, title):
        """Plot with colors based on unhashed clustering"""
        # Voronoi background
        pad = 0.08
        x_min, x_max = X2[:,0].min(), X2[:,0].max()
        y_min, y_max = X2[:,1].min(), X2[:,1].max()
        dx = x_max - x_min
        dy = y_max - y_min
        x_min -= dx*pad; x_max += dx*pad
        y_min -= dy*pad; y_max += dy*pad
        gx = gy = 200
        xx = np.linspace(x_min, x_max, gx)
        yy = np.linspace(y_min, y_max, gy)
        xxg, yyg = np.meshgrid(xx, yy)
        grid = np.stack([xxg.ravel(), yyg.ravel()], axis=1)
        d = np.linalg.norm(grid[:, None, :] - centers[None, :, :], axis=2)
        nearest = np.argmin(d, axis=1).reshape(gy, gx)
        cmap = plt.get_cmap('tab20')
        ax.pcolormesh(xxg, yyg, nearest, cmap=cmap, shading='auto', alpha=0.18)
        
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

    plot_with_shared_colors(axes[0], Xs2, centers_s, labels_shared, out_s,
                            f'Unhashed (Full Precision) - {N_CLUSTERS} clusters')
    plot_with_shared_colors(axes[1], Xh2, centers_h, labels_shared, out_h,
                            f'Hashed ({hash_buckets} buckets) - Same {N_CLUSTERS} clusters')

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
