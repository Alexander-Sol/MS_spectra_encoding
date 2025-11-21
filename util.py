import pandas as pd
import numpy as np
import spectrum_utils.plot as sup
import spectrum_utils.spectrum as sus
import pyteomics
from pyteomics import mzml, auxiliary
try:
    import plotly.tools as tls
except Exception:
    tls = None
    import logging
    logging.getLogger(__name__).warning(
        "plotly.tools not available; CustomUtil.plot_MS2 will fall back to matplotlib display"
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

def make_ion_ladder(peptide, aa_mass = None):
    """Generate b and y ion ladders for a given peptide sequence.
    If you want to know the chemistry/physics behind this, you can read
    about it in this paper: https://cse.sc.edu/~rose/790B/papers/dancik.pdf """
    aa_mass = aa_mass or CustomUtil.AMINO_ACID_DICT
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

