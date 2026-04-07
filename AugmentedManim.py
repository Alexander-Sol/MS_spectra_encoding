from manim import *
import numpy as np


DATA_FILE = "DIA/E24484_Mag_1_4_50_3.mzML"

# Acquisition constants measured from DIA/E24484_Mag_1_4_50_3.mzML.
TOTAL_SCANS = 767
MS1_SCAN_COUNT = 20
MS2_SCAN_COUNT = 747
FULL_CYCLE_COUNT = 19
CYCLE_LENGTH = 39
MS2_PER_CYCLE = 38
INTERLEAVE_PHASE_COUNT = 4

# Survey-scan coverage is wider than the DIA fragmentation program.
MS1_MZ_MIN = 346.5140
MS1_MZ_MAX = 1515.0921
DIA_MZ_MIN = 399.4314
DIA_MZ_MAX = 1008.7084

# Isolation windows are ~5 Da wide, with adjacent targets spaced by ~4 Da.
ISOLATION_WINDOW_HALF_WIDTH = 2.5011367798
ISOLATION_WINDOW_WIDTH = 2 * ISOLATION_WINDOW_HALF_WIDTH
ISOLATION_TARGET_SPACING = 4.0018
ISOLATION_WINDOW_OVERLAP = 1.0005

# One acquisition cycle lasts about 0.05 min (~3 s) in this file.
RETENTION_TIME_START_MIN = 37.0004
RETENTION_TIME_END_MIN = 37.9990
RETENTION_TIME_PER_CYCLE_MIN = 0.0500

# The instrument cycles through these 4 DIA phase blocks in acquisition order.
INTERLEAVED_PHASES = (
    {
        "name": "A",
        "cycle_offset": 0,
        "target_min_mz": 554.0017,
        "target_max_mz": 702.0690,
        "window_min_mz": 551.5006,
        "window_max_mz": 704.5702,
    },
    {
        "name": "B",
        "cycle_offset": 1,
        "target_min_mz": 706.0708,
        "target_max_mz": 854.1381,
        "window_min_mz": 703.5697,
        "window_max_mz": 856.6393,
    },
    {
        "name": "C",
        "cycle_offset": 2,
        "target_min_mz": 858.1400,
        "target_max_mz": 1006.2073,
        "window_min_mz": 855.6388,
        "window_max_mz": 1008.7084,
    },
    {
        "name": "D",
        "cycle_offset": 3,
        "target_min_mz": 401.9326,
        "target_max_mz": 549.9999,
        "window_min_mz": 399.4314,
        "window_max_mz": 552.5010,
    },
)

# Helpful anchors for the opening interleaving / retention-time visualization.
PHASE_SEQUENCE = tuple(phase["name"] for phase in INTERLEAVED_PHASES)
PHASE_REPEAT_PERIOD_CYCLES = INTERLEAVE_PHASE_COUNT
EXAMPLE_TARGET_MZ = 818.1218
EXAMPLE_TARGET_WINDOW = (
    EXAMPLE_TARGET_MZ - ISOLATION_WINDOW_HALF_WIDTH,
    EXAMPLE_TARGET_MZ + ISOLATION_WINDOW_HALF_WIDTH,
)
EXAMPLE_TARGET_CYCLES = (1, 5, 9, 13, 17)


class AugmentedManim(Scene):
    def construct(self):
        pass
