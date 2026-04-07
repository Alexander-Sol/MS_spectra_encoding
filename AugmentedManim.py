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
        np.random.seed(42)

        # ── Layout constants ──────────────────────────────────────────
        L_CX = -3.3          # left graph center-x
        R_CX = 3.3           # right graph center-x
        GW, GH = 5.0, 3.8   # left graph width / height
        RW, RH = 4.0, 3.8   # right graph width / height

        # bottom-left origins (where axis lines meet)
        lo = np.array([L_CX - GW / 2, -GH / 2 - 0.3, 0])
        ro = np.array([R_CX - RW / 2, -RH / 2 - 0.3, 0])

        # ── Build left graph frame (m/z vs intensity) ─────────────────
        l_xaxis = Line(lo, lo + RIGHT * GW, stroke_width=2)
        l_yaxis = Line(lo, lo + UP * GH, stroke_width=2)
        l_xlabel = Text("m/z", font_size=22).next_to(l_xaxis, DOWN, buff=0.35)
        l_ylabel = (
            Text("Intensity", font_size=18)
            .rotate(PI / 2)
            .next_to(l_yaxis, LEFT, buff=0.25)
        )
        l_frame = VGroup(l_xaxis, l_yaxis, l_xlabel, l_ylabel)

        # ── Build right graph frame (RT vs intensity) ─────────────────
        r_xaxis = Line(ro, ro + RIGHT * RW, stroke_width=2)
        r_yaxis = Line(ro, ro + UP * RH, stroke_width=2)
        r_xlabel = Text("Retention Time", font_size=18).next_to(
            r_xaxis, DOWN, buff=0.35
        )
        r_ylabel = (
            Text("Intensity", font_size=18)
            .rotate(PI / 2)
            .next_to(r_yaxis, LEFT, buff=0.25)
        )
        r_frame = VGroup(r_xaxis, r_yaxis, r_xlabel, r_ylabel)

        self.play(Create(l_frame), Create(r_frame), run_time=1.5)
        self.wait(0.5)

        # ── RT-graph accumulation tracking ────────────────────────────
        # 8 cycles total (4 phases × 2 repeats), each cycle -> 1 blue + 1 red block
        n_blocks = 16
        bw = RW / n_blocks   # block width in RT graph
        rt_idx = 0

        phases = list(INTERLEAVED_PHASES) * 2   # A B C D A B C D

        for ci, phase in enumerate(phases):
            fast = ci >= 1
            t = 0.15 if fast else 0.7   # base run_time

            # ════════════════════════════════════════════════════════════
            #  MS1 SCAN  (blue)
            # ════════════════════════════════════════════════════════════

            # --- range labels on x-axis ---
            lbl_min = Text(f"{MS1_MZ_MIN:.0f}", font_size=15).move_to(
                lo + DOWN * 0.15, aligned_edge=UP
            )
            lbl_min.align_to(lo, LEFT)
            lbl_max = Text(f"{MS1_MZ_MAX:.0f}", font_size=15).move_to(
                lo + RIGHT * GW + DOWN * 0.15, aligned_edge=UP
            )
            lbl_max.align_to(lo + RIGHT * GW, RIGHT)

            # --- blue rect filling the graph area ---
            ms1_rect = Rectangle(
                width=GW,
                height=GH,
                fill_color=BLUE,
                fill_opacity=0.15,
                stroke_color=BLUE,
                stroke_width=1.5,
            ).move_to(lo + np.array([GW / 2, GH / 2, 0]))

            # --- random MS1-like spectrum ---
            bars = self._make_bars(lo, GW, GH, n=50 if not fast else 30, color=BLUE)

            self.play(FadeIn(lbl_min, lbl_max, ms1_rect), run_time=t)
            self.play(FadeIn(bars), run_time=t)
            self.play(FadeOut(bars), run_time=t)

            # --- move blank blue rect into the RT graph ---
            rt_h = RH * np.random.uniform(0.35, 0.75)
            rt_ms1 = Rectangle(
                width=bw * 0.88,
                height=rt_h,
                fill_color=BLUE,
                fill_opacity=0.4,
                stroke_color=BLUE,
                stroke_width=0.5,
            )
            rt_x = ro[0] + bw * (rt_idx + 0.5)
            rt_ms1.move_to(np.array([rt_x, ro[1], 0]), aligned_edge=DOWN)

            self.play(
                FadeOut(lbl_min, lbl_max),
                ReplacementTransform(ms1_rect, rt_ms1),
                run_time=t * 1.5,
            )
            rt_idx += 1

            # ════════════════════════════════════════════════════════════
            #  MS2 SCAN  (red, for current phase)
            # ════════════════════════════════════════════════════════════

            p_min = phase["window_min_mz"]
            p_max = phase["window_max_mz"]

            # --- range labels ---
            lbl2_min = Text(f"{p_min:.0f}", font_size=15).move_to(
                lo + DOWN * 0.15, aligned_edge=UP
            )
            lbl2_min.align_to(lo, LEFT)
            lbl2_max = Text(f"{p_max:.0f}", font_size=15).move_to(
                lo + RIGHT * GW + DOWN * 0.15, aligned_edge=UP
            )
            lbl2_max.align_to(lo + RIGHT * GW, RIGHT)

            # --- big red rect covering the full phase range ---
            ms2_rect = Rectangle(
                width=GW,
                height=GH,
                fill_color=RED,
                fill_opacity=0.10,
                stroke_color=RED,
                stroke_width=1.5,
            ).move_to(lo + np.array([GW / 2, GH / 2, 0]))

            # --- 38 sub-rects (one per isolation window) ---
            sw = GW / MS2_PER_CYCLE
            subs = VGroup()
            sub_bars = VGroup()
            for i in range(MS2_PER_CYCLE):
                sr = Rectangle(
                    width=sw * 0.85,
                    height=GH,
                    fill_color=RED,
                    fill_opacity=0.06,
                    stroke_color=RED_A,
                    stroke_width=0.3,
                ).move_to(lo + np.array([sw * (i + 0.5), GH / 2, 0]))
                subs.add(sr)

                sb = self._make_bars(
                    lo + np.array([sw * i + sw * 0.08, 0, 0]),
                    sw * 0.75,
                    GH,
                    n=5,
                    color=RED,
                )
                sub_bars.add(sb)

            self.play(FadeIn(lbl2_min, lbl2_max, ms2_rect), run_time=t)

            if not fast:
                # slow: show each isolation window appearing one-by-one
                for i in range(MS2_PER_CYCLE):
                    self.play(
                        FadeIn(subs[i], sub_bars[i]),
                        run_time=0.08,
                    )
                self.wait(0.3)
                self.play(FadeOut(sub_bars), run_time=t)
            else:
                self.play(FadeIn(subs, sub_bars), run_time=t)
                self.play(FadeOut(sub_bars), run_time=t * 0.5)

            # --- move red rect + subs to RT graph ---
            rt_h2 = RH * np.random.uniform(0.2, 0.55)
            rt_ms2 = Rectangle(
                width=bw * 0.88,
                height=rt_h2,
                fill_color=RED,
                fill_opacity=0.4,
                stroke_color=RED,
                stroke_width=0.5,
            )
            rt_x2 = ro[0] + bw * (rt_idx + 0.5)
            rt_ms2.move_to(np.array([rt_x2, ro[1], 0]), aligned_edge=DOWN)

            ms2_group = VGroup(ms2_rect, subs)
            self.play(
                FadeOut(lbl2_min, lbl2_max),
                ReplacementTransform(ms2_group, rt_ms2),
                run_time=t * 1.5,
            )
            rt_idx += 1

        self.wait(2)

    # ── helpers ────────────────────────────────────────────────────────

    def _make_bars(
        self,
        origin: np.ndarray,
        width: float,
        height: float,
        n: int = 30,
        color=BLUE,
    ) -> VGroup:
        """Random mass-spectrum-like vertical bars within a rectangular region."""
        bars = VGroup()
        xs = np.sort(np.random.uniform(0.03, 0.97, n))
        ys = np.random.exponential(0.25, n)
        ys = np.clip(ys, 0.02, None)
        if ys.max() > 0:
            ys /= ys.max()
        # sprinkle a few dominant peaks
        for _ in range(max(1, n // 10)):
            ys[np.random.randint(n)] = np.random.uniform(0.55, 1.0)

        for x_frac, y_frac in zip(xs, ys):
            h = height * y_frac * 0.85
            bar = Line(
                origin + np.array([width * x_frac, 0, 0]),
                origin + np.array([width * x_frac, h, 0]),
                stroke_width=1.2,
                color=color,
            )
            bars.add(bar)
        return bars
