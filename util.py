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