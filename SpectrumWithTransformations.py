import numpy as np
from spectrum_utils.spectrum import MsmsSpectrum
from typing import Dict, Iterable, Optional, Union

class SpectrumWithTransformation(MsmsSpectrum):

    def __init__(
        self,
        scan_number: int,
        identifier: str,
        precursor_mz: float,
        precursor_charge: int,
        mz_array: Union[np.ndarray, Iterable],
        intensity_array: Union[np.ndarray, Iterable],
        retention_time: float = np.nan,
        annotation_dictionary= None,
        binned_mz: Union[np.ndarray, Iterable]=None,
        hashed_mz: Union[np.ndarray, Iterable]=None
    ) -> None:
        
        super().__init__(identifier, precursor_mz, precursor_charge, mz_array, intensity_array, retention_time)
        # self.mz_array = np.asarray(mz_array, dtype=float)
        # self.intensity_array = np.asarray(intensity_array, dtype=float)
        self.scan_number = int(scan_number)
        self.annotation_dictionary = None if binned_mz is None else dict(annotation_dictionary)
        self.binned_mz = None if binned_mz is None else np.asarray(binned_mz, dtype=float)
        self.hashed_mz = None if hashed_mz is None else np.asarray(hashed_mz, dtype=float)

    def __getstate__(self):
        return {
            "mz_array": self.mz,
            "intensity_array": self.intensity,
            "scan_number": self.scan_number,
            "annotation_dictionary": self.annotation_dictionary,
            "binned_mz": self.binned_mz,
            "hashed_mz": self.hashed_mz
        } 
    
    def __setstate__(self, state):
        self.mz_array = np.asarray(state["mz_array"], dtype=float)
        self.intensity_array = np.asarray(state["intensity_array"], dtype=float)
        self.scan_number = int(state["scan_number"])
        self.annotation_dictionary = state.get("annotation_dictionary") # None by default
        self.binned_mz = (
            None if state.get("binned_mz") is None else np.asarray(state["binned_mz"], dtype=float)
        )
        self.hashed_mz = (
            None if state.get("hashed_mz") is None else np.asarray(state["hashed_mz"], dtype=float)
        )
    

    

