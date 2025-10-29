import numpy as np
from pyteomics import mzml
from SpectrumWithTransformations import SpectrumWithTransformation

from spectrum_utils.proforma import Proteoform

class LoadSpectra(SpectrumWithTransformation):

    # This function should read in an mzml file and return an object of type SpectrumWithTransformations
    # Based off of get_MS2_object from Sam Payne lesson 4
    @classmethod
    def get_MS2_object(
        cls,
        mzml_path: str,
        scan_number: int,
        full_sequence = None,
        base_sequence = None,
        modifications_list = None
    ) -> "SpectrumWithTransformation":
        index = scan_number -1 #scan_number is 1-based, index is 0-based
        with mzml.MzML(mzml_path, use_index=True) as reader: #use_index=True allows us to avoid reading through the entire mzml file
            selected_spectrum = reader.get_by_index(index)

        # This finds the cooresponding values in the .mzml file to create our MS2 for a given scan (see the params)
        spectrum_id = selected_spectrum['id']
        retention_time = selected_spectrum['scanList']['scan'][0]['scan start time']
        precursor_mz = selected_spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
        precursor_charge = int(selected_spectrum['precursorList']['precursor'][0]['selectedIonList']['selectedIon'][0]['charge state'])

        mz_array = np.asarray(selected_spectrum['m/z array'])
        intensity_array = np.asarray(selected_spectrum['intensity array'])
        
        # Test to see if we accessed the correct scan: PASSED!
        # precursor_mz = selected_spectrum['precursorList']['precursor'][0]['isolationWindow']['isolation window target m/z']
        # print(precursor_mz)
        
        ms2_object = SpectrumWithTransformation(
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

        #Create annotation dictionary:
        annotation_dictionary = None
        # if base_sequence:
            # annotation_dictionary = cls.get_annotation_dictionary(
                # base_sequence,
                # precursor_charge,
                # modifications_list
            # )

        return ms2_object    
        if full_sequence:
            ms2_object.annotate_proforma(
                proforma_str = full_sequence,
                fragment_tol_mass = 0.01, # We consider two peaks (actual and theoretical) "equivalent" if they are within +/- 0.01 Da
                fragment_tol_mode = 'Da',
                ion_types = 'by',
                max_ion_charge = max(1, precursor_charge - 1)
            )
            print("Hello!")
            
        ms2_object.annotation_dictionary = annotation_dictionary

        return ms2_object
    
    def annotate_proforma(self, proforma_str, fragment_tol_mass, fragment_tol_mode, ion_types = "by", max_ion_charge = None, neutral_losses = False):
        return super().annotate_proforma(proforma_str, fragment_tol_mass, fragment_tol_mode, ion_types, max_ion_charge, neutral_losses)
    
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

