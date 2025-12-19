import pandas as pd
import numpy as np
import spectrum_utils.plot as sup
import spectrum_utils.spectrum as sus
import pyteomics
from pyteomics import mzml, auxiliary
import matplotlib.pyplot as plt
from matplotlib.pyplot import subplots
from rapidhash import rapidhash
import numpy as np

import numpy as np
from scipy.spatial import distance
import pandas as pd


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


def get_all_MS2_objects(mzml_path):
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


def plot_and_show_statistics_for_collisions(mzml_path):
    def count_collisions(mz_array, bin_width):
        """
        Count how many peaks collide (fall into the same bin) for a given bin width.
        
        Returns: (num_collisions, num_peaks)
        """
        bin_ids = np.floor(np.asarray(mz_array) / bin_width).astype(np.int64)
        buckets = {}
        for i, b in enumerate(bin_ids):
            buckets.setdefault(b, []).append(i)
        
        collision_count = sum(len(idxs) for idxs in buckets.values() if len(idxs) > 1)
        return collision_count, len(mz_array)


    def analyze_per_spectrum_collisions(mzml_path, bin_widths=(1.0, 0.01), max_spectra=None):
        """
        Analyze collision rates for each individual MS2 spectrum in an mzML file.
        
        Parameters
        ----------
        mzml_path : str
            Path to the mzML file
        bin_widths : tuple
            Bin widths to compare (default: 1.0 Da and 0.01 Da)
        max_spectra : int or None
            Limit number of spectra to analyze (None = all)
        
        Returns
        -------
        DataFrame with collision statistics per spectrum
        """
        all_spectra = get_all_MS2_objects(mzml_path=mzml_path)
        
        if max_spectra:
            all_spectra = all_spectra[:max_spectra]
        
        results = []
        for i, ms2 in enumerate(all_spectra):
            row = {'spectrum_idx': i, 'num_peaks': len(ms2.mz)}
            
            for width in bin_widths:
                collisions, total = count_collisions(ms2.mz, width)
                row[f'collisions_{width}Da'] = collisions
                row[f'collision_rate_{width}Da'] = collisions / total if total > 0 else 0
            
            results.append(row)
        
        df = pd.DataFrame(results)
        return df, all_spectra


    # Analyze collisions per spectrum
    collision_df, all_objs = analyze_per_spectrum_collisions(mzml_path, max_spectra=None)

    # Summary statistics
    print(f"=== Per-Spectrum Collision Analysis ===")
    print(f"File: {mzml_path}")
    print(f"Total spectra analyzed: {len(collision_df)}")
    print(f"\n--- Bin Size = 1.0 Da ---")
    print(f"  Spectra with collisions: {(collision_df['collisions_1.0Da'] > 0).sum()} / {len(collision_df)}")
    print(f"  Mean collisions per spectrum: {collision_df['collisions_1.0Da'].mean():.2f}")
    print(f"  Max collisions in a spectrum: {collision_df['collisions_1.0Da'].max()}")
    print(f"  Mean collision rate: {collision_df['collision_rate_1.0Da'].mean()*100:.2f}%")

    print(f"\n--- Bin Size = 0.01 Da ---")
    print(f"  Spectra with collisions: {(collision_df['collisions_0.01Da'] > 0).sum()} / {len(collision_df)}")
    print(f"  Mean collisions per spectrum: {collision_df['collisions_0.01Da'].mean():.2f}")
    print(f"  Max collisions in a spectrum: {collision_df['collisions_0.01Da'].max()}")
    print(f"  Mean collision rate: {collision_df['collision_rate_0.01Da'].mean()*100:.2f}%")

    # Visualization: Distribution of collision counts per spectrum
    fig, axes = subplots(1, 2, figsize=(14, 5))

    # Left: 1.0 Da bin collisions
    axes[0].hist(collision_df['collisions_1.0Da'], bins=30, alpha=0.7, color='coral', edgecolor='black')
    axes[0].axvline(collision_df['collisions_1.0Da'].mean(), color='red', linestyle='--', 
                    linewidth=2, label=f"Mean: {collision_df['collisions_1.0Da'].mean():.1f}")
    axes[0].set_xlabel('Number of Collisions per Spectrum')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Collisions per Spectrum (Bin = 1.0 Da)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Right: 0.01 Da bin collisions
    axes[1].hist(collision_df['collisions_0.01Da'], bins=30, alpha=0.7, color='steelblue', edgecolor='black')
    axes[1].axvline(collision_df['collisions_0.01Da'].mean(), color='darkblue', linestyle='--', 
                    linewidth=2, label=f"Mean: {collision_df['collisions_0.01Da'].mean():.1f}")
    axes[1].set_xlabel('Number of Collisions per Spectrum')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Collisions per Spectrum (Bin = 0.01 Da)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# @title Proving Similarity preservation empirically 
def prove_similarity_preservation_plots_and_statistics(mzml_path):
    # Demonstrate similarity preservation between original sparse maps and hashed vectors
    # Let's get multiple spectra and compare their similarities

    # Get all spectra first
    spectra_to_compare = get_all_MS2_objects(mzml_path)

    # Convert each spectrum to sparse map and hash vector representations
    sparse_maps = []
    hash_vectors = []

    WIDTH_OF_BIN = 0.01
    hash_buckets = 800

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
            byte_representation = int(sparse_idx).to_bytes(8, 'little')
            bucket_idx = rapidhash(byte_representation) % num_buckets
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

    # Calculate similarity matrices

    n_spectra = len(spectra_to_compare)
    sparse_similarities = np.zeros((n_spectra, n_spectra)) # tuples
    hash_similarities = np.zeros((n_spectra, n_spectra))

    # Calculate pairwise similarities using cosine similarity
    for i in range(n_spectra):
        for j in range(n_spectra):
            # Sparse map cosine similarities (0 to 1)
            sparse_similarities[i, j] = sparse_cosine_similarity(sparse_maps[i], sparse_maps[j])
            
            # Hash vector cosine similarities (0 to 1)  
            hash_similarities[i, j] = cosine_similarity(hash_vectors[i], hash_vectors[j])


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
    sparse_upper = sparse_similarities[np.triu_indices(n_spectra, k=1)]
    hash_upper = hash_similarities[np.triu_indices(n_spectra, k=1)]


    # Calculate cosine distance between the similarity matrices
    cosine_similarity_preservation = 1- distance.cosine(sparse_upper, hash_upper)
    correlation = np.corrcoef(sparse_upper, hash_upper)

    print(f"\nSimilarity Preservation Analysis:")
    print(f"Cosine similarity between sparse and hash similarities: {cosine_similarity_preservation:.3f}")
    print(f"This shows how well the hash representation preserves the similarity structure")
    print(f"A similarity close to 1 indicates good similarity preservation")
    print("shape of correlation matrix:", correlation.shape, "shape of other arrays:", sparse_similarities.shape, hash_similarities.shape)

    # Create multiple cleaner visualizations instead of one overwhelming scatter plot
    fig, axes = plt.subplots(1, 1, figsize=(10, 6))
    # Difference histogram - shows how well similarities are preserved
    differences = hash_upper - sparse_upper
    axes.hist(differences, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    axes.axvline(0, color='red', linestyle='--', linewidth=2, label='Perfect preservation')
    axes.set_xlabel('Hash Similarity - Sparse Similarity')
    axes.set_ylabel('Frequency')
    axes.set_title(f'Similarity Preservation Errors\nMean: {np.mean(differences):.4f}, Std: {np.std(differences):.4f}')
    axes.legend()
    axes.set_xlim(-0.1, 1.0)
    axes.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # Summary statistics
    print(f"\nDetailed Statistics:")
    print(f"Number of pairwise comparisons: {len(sparse_upper):,}")
    print(f"Sparse similarities range: {np.min(sparse_upper):.3f} to {np.max(sparse_upper):.3f}")
    print(f"Hash similarities range: {np.min(hash_upper):.3f} to {np.max(hash_upper):.3f}")
    print(f"Mean absolute difference: {np.mean(np.abs(differences)):.4f}")
    print(f"Pearson correlation coefficient: {correlation[0,1]:.4f}")

    # Convert sparse similarities to DataFrame for better display
    sparse_df = pd.DataFrame(sparse_similarities)
    sparse_df.index.name = 'Spectrum'
    sparse_df.columns.name = 'Spectrum'

    # Convert hash similarities to DataFrame for better display  
    hash_df = pd.DataFrame(hash_similarities)
    hash_df.index.name = 'Spectrum'
    hash_df.columns.name = 'Spectrum'

    import seaborn as sns

    # Perform hierarchical clustering on the sparse (unhashed) similarities
    # Convert similarity to distance (1 - similarity) for clustering
    sparse_distances = 1 - sparse_similarities

    # Create clustermaps with the same ordering
    print("Clustering based on unhashed similarities, showing both matrices with same ordering:")

    # First clustermap: sparse similarities (this determines the ordering)
    fig1 = sns.clustermap(1-sparse_df, method="average", cmap="viridis", 
                        figsize=(10, 8), cbar_pos=(0.02, 0.8, 0.03, 0.18))
    fig1.figure.suptitle('Unhashed (Sparse) Matrix Similarities\n(Hierarchical Clustering)', y=0.95)

    # grab ordering from fig 1
    row_order = fig1.dendrogram_row.reordered_ind
    col_order = fig1.dendrogram_col.reordered_ind

    plt.show()

    # Reorder the hash_df according to the clustering results from fig 1
    hash_df_reordered = hash_df.iloc[row_order, col_order]

    fig2 = sns.clustermap(1-hash_df_reordered, method="average", cmap="viridis",
                        row_cluster=False, col_cluster=False,  # Don't re-cluster, use existing order
                        figsize=(10, 8), cbar_pos=(0.02, 0.8, 0.03, 0.18))
    fig2.figure.suptitle('Hashed Matrix Similarities\n(Same ordering as unhashed clustering)', y=0.95)

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