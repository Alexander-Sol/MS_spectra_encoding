import numpy as np

class SpectrumWithTransformation:

    def __init__(
        mz: np.ndarray,
        intensity: np.ndarray,
        scan_number: int,
        annotation_dictionary: None,
        binned_mz: None,
        hashed_mz: None
    )-> None:
        '''
        Parameters
        ----------
        mz: array of m/z values of fragment peaks
        intensity: array of intensity values of fragment peaks
        scan_number: one-based scan number from mzml file
        '''

    def __getstate__(self):
        return {
            "mz": self.mz,
            "intensity": self.intensity,
            "scan_number": self.scan_number,
            "annotation_dictionary": self.annotation_dictionary,
            "binned_mz": self.binned_mz,
            "hashed_mz": self.hashed_mz
        } 
    
    def __setstate__(self, state):
        self.mz = np.asarray(state["mz"], dtype=float)
        self.intensity = np.asarray(state["intensity"], dtype=float)
        self.scan_number = int(state["scan_number"])
        self.annotation_dictionary = state.get("annotation_dictionary") # None by default
        self.binned_mz = (
            None if state.get("binned_mz") is None else np.asarray(state["binned_mz"], dtype=float)
        )
        self.hashed_mz = (
            None if state.get("hashed_mz") is None else np.asarray(state["hashed_mz"], dtype=float)
        )
    

    

