import numpy as np
from pyteomics import mzml
from SpectrumWithTransformations import SpectrumWithTransformation

class LoadSpectra:

    # This function should read in an mzml file and return an object of type SpectrumWithTransformations
    # Based off of get_MS2_object from Sam Payne lesson 4
    @classmethod
    def get_MS2_object4(
        cls,
        mzml_path: str,
        scan_number: int = 8090,
    ) -> "SpectrumWithTransformation":
        print("HELWKDGJFNBWHYIGUEOO)ERGHBUIWJ")
        with mzml.MzML(mzml_path) as reader:
            selected_spectrum = reader.get_by_index(scan_number)

        mz_array = np.asarray(selected_spectrum["m/z array"], dtype=float)
        intensity_array = np.asarray(selected_spectrum["intensity array"], dtype=float)
        #scan_number = selected_spectrum["index"]

        return SpectrumWithTransformation(
        mz=mz_array,
        intensity=intensity_array,
        #scan_number=scan_number,
        annotation_dictionary=None,
        binned_mz=None,
        hashed_mz=None,
        )
            

    # def get_MS2_object(mzml_path, scan, peptide = None):
    # su_spectrum = None
    # with pyteomics.mzml.read(mzml_path) as spectra:
    #     for spectrum in spectra:
    #         scanNumber = int(spectrum['id'].split('=')[-1])
    #         if scanNumber == scan:
    #             # This finds the cooresponding values in the .mzml file to create our MS2
    #             spectrum_id = spectrum['id']
    #             mz = spectrum['m/z array']
    #             intensity = spectrum['intensity array']
    #             retention_time = spectrum['scanList']['scan'][0]['scan start time']
    #             precursor_mz = spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
    #             precursor_charge = int(spectrum['precursorList']['precursor'][0]['selectedIonList']['selectedIon'][0]['charge state'])

    #             su_spectrum = sus.MsmsSpectrum(spectrum_id, precursor_mz, precursor_charge, mz, intensity, retention_time=retention_time)

    #             # Process the spectrum
    #             su_spectrum = (su_spectrum.filter_intensity(0.05, 100)
    #                            .remove_precursor_peak(fragment_tol_mass=0.5, fragment_tol_mode='Da')
    #                            .scale_intensity('root'))
    #             break
    # # Formatting
    # if su_spectrum:
    #     fragment_tol_mass = 0.5
    #     fragment_tol_mode = 'Da'  ## for some reason, if I use 'ppm' it doesn't work

    #     # If given the peptide, spec_utils can annotate the peaks
    #     if peptide:
    #       su_spectrum = su_spectrum.annotate_proforma(peptide, fragment_tol_mass, fragment_tol_mode, ion_types='by', max_ion_charge=2)
    # return su_spectrum