import numpy as np
from pyteomics import mzml
from SpectrumWithTransformations import SpectrumWithTransformation
from spectrum_utils.proforma import Proteoform

class LoadSpectra:

    # This function should read in an mzml file and return an object of type SpectrumWithTransformations
    # Based off of get_MS2_object from Sam Payne lesson 4
    @classmethod
    def get_MS2_object(
        cls,
        mzml_path: str,
        scan_number: int,
        peptide = None,
        modifications_list = None
    ) -> "SpectrumWithTransformation":
        index = scan_number -1 #scan_number is 1-based, index is 0-based
        with mzml.MzML(mzml_path, use_index=True) as reader: #use_index=True allows us to avoid reading through the entire mzml file
            selected_spectrum = reader.get_by_index(index)

        mz_array = np.asarray(selected_spectrum['m/z array'])
        intensity_array = np.asarray(selected_spectrum['intensity array'])
        precursor_charge = int(selected_spectrum['precursorList']['precursor'][0]['selectedIonList']['selectedIon'][0]['charge state'])

        # Test to see if we accessed the correct scan: PASSED!
        # precursor_mz = selected_spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
        # print(precursor_mz)

            #Create annotation dictionary:
        annotation_dictionary = None
        if peptide:
            annotation_dictionary = cls.get_annotation_dictionary(
                peptide,
                precursor_charge,
                modifications_list
            )
        
        return SpectrumWithTransformation(
            mz=mz_array,
            intensity=intensity_array,
            scan_number= scan_number,
            annotation_dictionary=annotation_dictionary,
            binned_mz=None,
            hashed_mz=None,
        )
    
    @staticmethod
    def get_annotation_dictionary(
        sequence,
        precursor_charge,
        modifications_list
    ) -> dict:
        annotation_dictionary = None

        fragment_tol_mass = 0.01 # We consider two peaks (actual and theoretical) "equivalent" if they are within +/- 0.01 Da
        fragment_tol_mode = 'Da'
        ion_types = 'by'
        max_ion_charge = max(1, precursor_charge - 1)

        # Generate peptide fragments and calculate theoretical masses
        # Based on spectrum_utils => fragment_annotation.py => get_theoretical_fragments
        # N-terminal peptide fragments: (b ions)
        base_fragments = []
        proteoform = Proteoform(
            sequence=sequence,
            modifications=modifications_list
        )
        for ion_type in set("abc") & set(ion_types):
            mod_i, mod_mass = 0, 0
            for fragment_i in range(1, len(proteoform.sequence)):
                fragment_sequence = proteoform.sequence[:fragment_i]
                # Ignore unlocalized modifications.
                while (
                    proteoform.modifications is not None
                    and mod_i < len(proteoform.modifications)
                    and isinstance(proteoform.modifications[mod_i].position, str)
                    and proteoform.modifications[mod_i].position != "N-term"
                ):
                    mod_i += 1
                # Include prefix modifications.
                while (
                    proteoform.modifications is not None
                    and mod_i < len(proteoform.modifications)
                    and (
                        proteoform.modifications[mod_i].position == "N-term"
                        or (
                            isinstance(
                                proteoform.modifications[mod_i].position, int
                            )
                            and proteoform.modifications[mod_i].position
                            < fragment_i
                        )
                    )
                ):
                    mod_mass += proteoform.modifications[mod_i].mass
                    mod_i += 1
                base_fragments.append(
                    (fragment_sequence, ion_type, fragment_i, mod_mass)
                )
        return annotation_dictionary

