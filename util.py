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
from sklearn.manifold import TSNE



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


def plot_and_show_statistics_for_collisions(mzml_path, max_spectra=None):
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
    """
    
    def spectrum_to_bin_set(mz_array, bin_width):
        """Convert spectrum m/z values to a set of bin indices."""
        bin_ids = np.floor(np.asarray(mz_array) / bin_width).astype(np.int64)
        return set(bin_ids)
    
    # Get all spectra
    all_spectra = get_all_MS2_objects(mzml_path=mzml_path, max_spectra=max_spectra)
    if max_spectra is not None and len(all_spectra) > max_spectra:
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
def prove_similarity_preservation_plots_and_statistics(mzml_path, max_spectra=300):
    print("newer!")
    import mmh3
      # Demonstrate similarity preservation between original sparse maps and hashed vectors
      # Let's get multiple spectra and compare their similarities

    # Get spectra (stop early if max_spectra provided)
    spectra_to_compare = get_all_MS2_objects(mzml_path, max_spectra=max_spectra)
    if max_spectra and len(spectra_to_compare) > max_spectra:
        spectra_to_compare = spectra_to_compare[:max_spectra]
    n_spectra = len(spectra_to_compare)

    # Convert each spectrum to sparse map and hash vector representations
    sparse_maps = []
    hash_vectors = []

    WIDTH_OF_BIN = 0.01
    hash_buckets = 10000  # Increased from 800 to reduce collisions with ~100k dimensional space

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

    # Create representations for each spectrum
    for spec_data in spectra_to_compare:
        sparse_map = create_sparse_map(spec_data.mz, spec_data.intensity)
        hash_vec = sparse_map_to_hash_vector(sparse_map,hash_buckets)
        
        sparse_maps.append(sparse_map)
        hash_vectors.append(hash_vec)

    # # Calculate similarity matrices

    # n_spectra = len(spectra_to_compare)
    # sparse_similarities = np.zeros((n_spectra, n_spectra)) # tuples
    # hash_similarities = np.zeros((n_spectra, n_spectra))

    # # Calculate pairwise similarities using cosine similarity
    # for i in range(n_spectra):
    #     for j in range(n_spectra):
    #         # Sparse map cosine similarities (0 to 1)
    #         sparse_similarities[i, j] = sparse_cosine_similarity(sparse_maps[i], sparse_maps[j])
            
    #         # Hash vector cosine similarities (0 to 1)  
    #         hash_similarities[i, j] = cosine_similarity(hash_vectors[i], hash_vectors[j])


    # When you compute pairwise similarities between spectra, you get a symmetric matrix
    #      Spec0  Spec1  Spec2  Spec3
    # Spec0  1.0   0.8    0.3    0.6
    # Spec1  0.8   1.0    0.4    0.5
    # Spec2  0.3   0.4    1.0    0.7
    # Spec3  0.6   0.5    0.7    1.0
    #
    # Using np.triu allows us to just grab the upper (right) triangle. np.tril_indices would grab the lower left.
    #
    # Show distance between sparse and hash similarities using cosine distance
    # sparse_upper = sparse_similarities[np.triu_indices(n_spectra, k=1)]
    # hash_upper = hash_similarities[np.triu_indices(n_spectra, k=1)]


    # # # Calculate cosine distance between the similarity matrices
    # # cosine_similarity_preservation = 1- distance.cosine(sparse_upper, hash_upper)
    # # correlation = np.corrcoef(sparse_upper, hash_upper)
    
    
    
    # # # ################################ Ignore everything below this line, it's just for plotting and displaying statistics ################################
    
    
    
    # # # print(f"\nSimilarity Preservation Analysis:")
    # # # print(f"Cosine similarity between sparse and hash similarities: {cosine_similarity_preservation:.3f}")
    # # # print(f"This shows how well the hash representation preserves the similarity structure")
    # # # print(f"A similarity close to 1 indicates good similarity preservation")
    # # # print("shape of correlation matrix:", correlation.shape, "shape of other arrays:", sparse_similarities.shape, hash_similarities.shape)

    # # # # Create multiple cleaner visualizations instead of one overwhelming scatter plot
    # # # fig, axes = plt.subplots(1, 1, figsize=(10, 6))
    # # # # Difference histogram - shows how well similarities are preserved
    # # # differences = hash_upper - sparse_upper
    # # # axes.hist(differences, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    # # # axes.axvline(0, color='red', linestyle='--', linewidth=2, label='Perfect preservation')
    # # # axes.set_xlabel('Hash Similarity - Sparse Similarity')
    # # # axes.set_ylabel('Frequency')
    # # # axes.set_title(f'Similarity Preservation Errors\nMean: {np.mean(differences):.4f}, Std: {np.std(differences):.4f}')
    # # # axes.legend()
    # # # axes.set_xlim(-0.1, 1.0)
    # # # axes.grid(True, alpha=0.3)

    # # # plt.tight_layout()
    # # # plt.show()

    # # # # Summary statistics
    # # # print(f"\nDetailed Statistics:")
    # # # print(f"Number of pairwise comparisons: {len(sparse_upper):,}")
    # # # print(f"Sparse similarities range: {np.min(sparse_upper):.3f} to {np.max(sparse_upper):.3f}")
    # # # print(f"Hash similarities range: {np.min(hash_upper):.3f} to {np.max(hash_upper):.3f}")
    # # # print(f"Mean absolute difference: {np.mean(np.abs(differences)):.4f}")
    # # # print(f"Pearson correlation coefficient: {correlation[0,1]:.4f}")

    # # # # Convert sparse similarities to DataFrame for better display
    # # # sparse_df = pd.DataFrame(sparse_similarities)
    # # # sparse_df.index.name = 'Spectrum'
    # # # sparse_df.columns.name = 'Spectrum'

    # # # # Convert hash similarities to DataFrame for better display  
    # # # hash_df = pd.DataFrame(hash_similarities)
    # # # hash_df.index.name = 'Spectrum'
    # # # hash_df.columns.name = 'Spectrum'

    # # # import seaborn as sns

    # # # # Perform hierarchical clustering on the sparse (unhashed) similarities
    # # # # Convert similarity to distance (1 - similarity) for clustering
    # # # sparse_distances = 1 - sparse_similarities

    # # # # Create clustermaps with the same ordering
    # # # print("Clustering based on unhashed similarities, showing both matrices with same ordering:")

    # # # # First clustermap: sparse similarities (this determines the ordering)
    # # # fig1 = sns.clustermap(1-sparse_df, method="average", cmap="viridis", 
    # # #                     figsize=(10, 8), cbar_pos=(0.02, 0.8, 0.03, 0.18))
    # # # fig1.figure.suptitle('Unhashed (Sparse) Matrix Similarities\n(Hierarchical Clustering)', y=0.95)

    # # # # grab ordering from fig 1
    # # # row_order = fig1.dendrogram_row.reordered_ind
    # # # col_order = fig1.dendrogram_col.reordered_ind

    # # # plt.show()

    # # # # Reorder the hash_df according to the clustering results from fig 1
    # # # hash_df_reordered = hash_df.iloc[row_order, col_order]

    # # # fig2 = sns.clustermap(1-hash_df_reordered, method="average", cmap="viridis",
    # # #                     row_cluster=False, col_cluster=False,  # Don't re-cluster, use existing order
    # # #                     figsize=(10, 8), cbar_pos=(0.02, 0.8, 0.03, 0.18))
    # # # fig2.figure.suptitle('Hashed Matrix Similarities\n(Same ordering as unhashed clustering)', y=0.95)

    # # # plt.show()

    # hashed vectors (already built above)

    
    
    
    
        
    Xh = np.array(hash_vectors)

    # Build full dense unhashed matrix from sparse_maps (no compression)
    all_indices = set()
    for sm in sparse_maps:
        all_indices |= set(sm.keys())

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
    
    from umap import UMAP
    
    # t-SNE: set perplexity to a reasonable value relative to sample size
    perp = min(30, max(5, (n_spectra // 3)))
    tsne_s = TSNE(n_components=2, perplexity=perp, random_state=0, init='pca')
    tsne_h = TSNE(n_components=2, perplexity=perp, random_state=0, init='pca')
    Xs2 = tsne_s.fit_transform(Xs_pca)
    Xh2 = tsne_h.fit_transform(Xh_pca)



    N_CLUSTERS = 12
    try:
        km_s = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(Xs2)
        km_h = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(Xh2)
    except Exception as e:
        logging.getLogger(__name__).warning('KMeans failed: %s', e)
        return

    labels_s = km_s.labels_
    labels_h = km_h.labels_
    centers_s = km_s.cluster_centers_
    centers_h = km_h.cluster_centers_

    # detect and mark outliers (distance to centroid > 90th percentile)
    dists_s = np.linalg.norm(Xs2 - centers_s[labels_s], axis=1)
    dists_h = np.linalg.norm(Xh2 - centers_h[labels_h], axis=1)
    thr_s = np.percentile(dists_s, 90)
    thr_h = np.percentile(dists_h, 90)
    out_s = dists_s > thr_s
    out_h = dists_h > thr_h

    # Create Voronoi-like background by nearest-centroid on a grid
    def plot_with_voronoi(ax, X2, centers, labels, out_mask, title):
        # grid
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
        # compute nearest center
        d = np.linalg.norm(grid[:, None, :] - centers[None, :, :], axis=2)
        nearest = np.argmin(d, axis=1).reshape(gy, gx)
        cmap = plt.get_cmap('tab20')
        ax.pcolormesh(xxg, yyg, nearest, cmap=cmap, shading='auto', alpha=0.18)
        # plot non-outliers colored
        ax.scatter(X2[~out_mask,0], X2[~out_mask,1], c=labels[~out_mask], cmap='tab20', s=28, edgecolor='k', linewidth=0.2)
        # plot outliers faint
        if out_mask.any():
            ax.scatter(X2[out_mask,0], X2[out_mask,1], c='lightgray', s=18, alpha=0.8, label='outliers')
        # centers
        ax.scatter(centers[:,0], centers[:,1], c='k', marker='x', s=60)
        ax.set_title(title)
        ax.set_xlabel('Dim1')
        ax.set_ylabel('Dim2')

    fig, axes = plt.subplots(1, 2, figsize=(14,6))
    plot_with_voronoi(axes[0], Xs2, centers_s, labels_s, out_s, f'Clusters (full precision unhashed) - {N_CLUSTERS} clusters')
    plot_with_voronoi(axes[1], Xh2, centers_h, labels_h, out_h, f'Clusters (hashed {hash_buckets} buckets) - {N_CLUSTERS} clusters')

    for ax in axes:
        ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.show()
    
        
    # ============= RIGOROUS SIMILARITY PRESERVATION PROOF =============

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

    # 3. Calculate correlation metrics (Mantel-test style)
    from scipy.stats import pearsonr, spearmanr
    pearson_corr, pearson_pval = pearsonr(sparse_upper, hash_upper)
    spearman_corr, spearman_pval = spearmanr(sparse_upper, hash_upper)

    print(f"\n{'='*60}")
    print(f"SIMILARITY PRESERVATION METRICS")
    print(f"{'='*60}")
    print(f"Pearson correlation:  {pearson_corr:.4f} (p-value: {pearson_pval:.2e})")
    print(f"Spearman correlation: {spearman_corr:.4f} (p-value: {spearman_pval:.2e})")
    print(f"Number of pairwise comparisons: {len(sparse_upper):,}")
    print(f"Mean absolute error: {np.mean(np.abs(sparse_upper - hash_upper)):.4f}")
    print(f"{'='*60}\n")

    # 4. Apply t-SNE to CONCATENATED data so both embeddings share the same space
    # This is key: t-SNE on combined data ensures consistent spatial relationships
    perp = min(30, max(5, (n_spectra // 3)))
    
    # Ensure both PCA matrices have same number of columns for concatenation
    min_cols = min(Xs_pca.shape[1], Xh_pca.shape[1])
    Xs_pca_aligned = Xs_pca[:, :min_cols]
    Xh_pca_aligned = Xh_pca[:, :min_cols]
    
    # Run t-SNE on combined data
    combined_pca = np.vstack([Xs_pca_aligned, Xh_pca_aligned])
    tsne_combined = TSNE(n_components=2, perplexity=perp, random_state=0, init='pca')
    combined_2d = tsne_combined.fit_transform(combined_pca)
    
    # Split back into unhashed and hashed embeddings
    Xs2 = combined_2d[:n_spectra]
    Xh2 = combined_2d[n_spectra:]
    
    # 5. Cluster on the COMBINED 2D embedding (not just unhashed PCA)
    # This ensures both representations use the same cluster structure in the shared space
    N_CLUSTERS = 12
    km_combined = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(combined_2d)
    labels_shared = km_combined.labels_[:n_spectra]  # Use first half for both plots

    # Calculate centers for visualization based on actual cluster assignments in shared space
    # Handle empty clusters by checking if they have points
    centers_s = np.array([Xs2[labels_shared == k].mean(axis=0) if (labels_shared == k).any() 
                        else np.zeros(Xs2.shape[1]) for k in range(N_CLUSTERS)])
    centers_h = np.array([Xh2[labels_shared == k].mean(axis=0) if (labels_shared == k).any() 
                        else np.zeros(Xh2.shape[1]) for k in range(N_CLUSTERS)])

    # 6. Detect outliers using shared clustering
    dists_s = np.linalg.norm(Xs2 - centers_s[labels_shared], axis=1)
    dists_h = np.linalg.norm(Xh2 - centers_h[labels_shared], axis=1)
    thr_s = np.percentile(dists_s, 90)
    thr_h = np.percentile(dists_h, 90)
    out_s = dists_s > thr_s
    out_h = dists_h > thr_h

    # 7. Create visualizations
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1])

    # Top row: Scatter plot comparing similarities
    ax_scatter = fig.add_subplot(gs[0, :])
    ax_scatter.scatter(sparse_upper, hash_upper, alpha=0.3, s=10, edgecolors='none')
    ax_scatter.plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect preservation')
    ax_scatter.set_xlabel('Unhashed (Sparse) Cosine Similarity', fontsize=12)
    ax_scatter.set_ylabel('Hashed Cosine Similarity', fontsize=12)
    ax_scatter.set_title(f'Pairwise Similarity Preservation\n' + 
                        f'Pearson r={pearson_corr:.4f}, Spearman ρ={spearman_corr:.4f}',
                        fontsize=14, fontweight='bold')
    ax_scatter.legend()
    ax_scatter.grid(alpha=0.3)
    ax_scatter.set_xlim(0, 1)
    ax_scatter.set_ylim(0, 1)
    ax_scatter.set_aspect('equal')

    # Bottom row: t-SNE plots with SAME colors
    ax_unhashed = fig.add_subplot(gs[1, 0])
    ax_hashed = fig.add_subplot(gs[1, 1])

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

    plot_with_shared_colors(ax_unhashed, Xs2, centers_s, labels_shared, out_s,
                            f'Unhashed (Full Precision) - {N_CLUSTERS} clusters')
    plot_with_shared_colors(ax_hashed, Xh2, centers_h, labels_shared, out_h,
                            f'Hashed ({hash_buckets} buckets) - Same {N_CLUSTERS} clusters')

    plt.tight_layout()
    plt.show()

    # 8. Additional validation: Heatmap comparison
    fig2, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Sort by hierarchical clustering for better visualization
    from scipy.cluster.hierarchy import linkage, leaves_list
    linkage_matrix = linkage(1 - sparse_similarities, method='average')
    order = leaves_list(linkage_matrix)

    im1 = axes[0].imshow(sparse_similarities[np.ix_(order, order)], 
                        cmap='viridis', vmin=0, vmax=1)
    axes[0].set_title('Unhashed Similarity Matrix\n(Hierarchically Ordered)')
    plt.colorbar(im1, ax=axes[0])

    im2 = axes[1].imshow(hash_similarities[np.ix_(order, order)], 
                        cmap='viridis', vmin=0, vmax=1)
    axes[1].set_title('Hashed Similarity Matrix\n(Same Order)')
    plt.colorbar(im2, ax=axes[1])

    # Difference map
    diff = np.abs(sparse_similarities - hash_similarities)[np.ix_(order, order)]
    im3 = axes[2].imshow(diff, cmap='Reds', vmin=0, vmax=0.3)
    axes[2].set_title(f'Absolute Difference\n(Mean: {np.mean(np.abs(sparse_similarities - hash_similarities)):.4f})')
    plt.colorbar(im3, ax=axes[2])

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
