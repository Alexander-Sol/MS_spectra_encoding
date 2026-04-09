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

# Fixed x-axis range for the left graph — never changes.
X_AXIS_MIN = 300.0
X_AXIS_MAX = 1600.0
X_AXIS_SPAN = X_AXIS_MAX - X_AXIS_MIN  # 1300.0


class AugmentedManim(Scene):
    def construct(self):
        np.random.seed(42)

        # ── Layout ────────────────────────────────────────────────────
        GW, GH = 5.2, 3.6   # left graph (m/z × intensity)
        RW, RH = 4.0, 3.6   # right graph (RT × intensity)

        # Bottom-left origin of each graph (where the two axes meet).
        # Extra vertical room for tick labels + "m/z" label below the axis.
        lo = np.array([-6.0, -2.4, 0])   # left origin
        ro = np.array([ 1.3, -2.4, 0])   # right origin

        # ── Left graph frame ──────────────────────────────────────────
        l_xaxis = Line(lo, lo + RIGHT * GW, stroke_width=2)
        l_yaxis = Line(lo, lo + UP * GH,    stroke_width=2)
        l_xlabel = Text("m/z", font_size=22).next_to(l_xaxis, DOWN, buff=0.65)
        l_ylabel = (
            Text("Intensity", font_size=18)
            .rotate(PI / 2)
            .next_to(l_yaxis, LEFT, buff=0.25)
        )

        # Permanent x-axis tick marks and labels.
        l_ticks = VGroup()
        l_tick_labels = VGroup()
        for mz in [400, 700, 1000, 1300, 1600]:
            x = self._mz_to_x(mz, lo, GW)
            l_ticks.add(Line([x, lo[1], 0], [x, lo[1] - 0.12, 0], stroke_width=1.5))
            l_tick_labels.add(
                Text(str(mz), font_size=12).move_to([x, lo[1] - 0.32, 0])
            )

        l_frame = VGroup(l_xaxis, l_yaxis, l_xlabel, l_ylabel, l_ticks, l_tick_labels)

        # ── Right graph frame ─────────────────────────────────────────
        r_xaxis = Line(ro, ro + RIGHT * RW, stroke_width=2)
        r_yaxis = Line(ro, ro + UP * RH,    stroke_width=2)
        r_xlabel = Text("Retention Time", font_size=18).next_to(r_xaxis, DOWN, buff=0.35)
        r_ylabel = (
            Text("Intensity", font_size=18)
            .rotate(PI / 2)
            .next_to(r_yaxis, LEFT, buff=0.25)
        )
        r_frame = VGroup(r_xaxis, r_yaxis, r_xlabel, r_ylabel)

        self.play(Create(l_frame), Create(r_frame), run_time=1.5)
        self.wait(0.5)

        # ── RT-graph geometry (proportional to scan count) ────────────
        # Each scan in the cycle gets one unit of RT-axis width.
        # 8 cycles × 39 scans/cycle = 312 scans total.
        n_scans_total = 8 * CYCLE_LENGTH            # 312
        scan_uw = RW / n_scans_total                # width per scan in RT graph
        ms2_block_w = MS2_PER_CYCLE * scan_uw       # width of a full MS2 phase block
        rt_x_cursor = ro[0]                         # current right-edge of placed blocks

        # ── Main animation loop  (A B C D  ×  2) ─────────────────────
        phases = list(INTERLEAVED_PHASES) * 2

        for ci, phase in enumerate(phases):
            fast = ci >= 1
            t = 0.15 if fast else 0.7

            # ────────────────────────────────────────────────────────
            # MS1 SCAN  (blue)
            # ────────────────────────────────────────────────────────
            lbl_ms1_min, lbl_ms1_max = self._range_labels(
                MS1_MZ_MIN, MS1_MZ_MAX, lo, GW
            )
            ms1_rect = self._mz_rect(
                MS1_MZ_MIN, MS1_MZ_MAX, lo, GW, GH,
                fill_color=BLUE, fill_opacity=0.15,
                stroke_color=BLUE, stroke_width=1.5,
            )
            bars_ms1 = self._make_bars_mz(
                MS1_MZ_MIN, MS1_MZ_MAX, lo, GW, GH,
                n=50 if not fast else 30, color=BLUE,
            )

            self.play(FadeIn(lbl_ms1_min, lbl_ms1_max, ms1_rect), run_time=t)
            self.play(FadeIn(bars_ms1), run_time=t)
            self.play(FadeOut(bars_ms1), run_time=t)

            # Build the RT-graph MS1 block (a simple blue bar).
            rt_h_ms1 = RH * np.random.uniform(0.35, 0.75)
            rt_ms1 = Rectangle(
                width=scan_uw * 0.9, height=rt_h_ms1,
                fill_color=BLUE, fill_opacity=0.5,
                stroke_color=BLUE, stroke_width=0.5,
            ).move_to([rt_x_cursor + scan_uw / 2, ro[1], 0], aligned_edge=DOWN)

            self.play(
                FadeOut(lbl_ms1_min, lbl_ms1_max),
                ReplacementTransform(ms1_rect, rt_ms1),
                run_time=t * 1.5,
            )
            rt_x_cursor += scan_uw

            # ────────────────────────────────────────────────────────
            # MS2 SCAN  (red)
            # ────────────────────────────────────────────────────────
            p_min = phase["window_min_mz"]
            p_max = phase["window_max_mz"]

            lbl_ms2_min, lbl_ms2_max = self._range_labels(p_min, p_max, lo, GW)

            ms2_rect = self._mz_rect(
                p_min, p_max, lo, GW, GH,
                fill_color=RED, fill_opacity=0.08,
                stroke_color=RED, stroke_width=1.5,
            )

            # 38 sub-rects at actual isolation-window m/z positions.
            subs = VGroup()
            sub_bars = VGroup()
            for i in range(MS2_PER_CYCLE):
                center_mz = phase["target_min_mz"] + i * ISOLATION_TARGET_SPACING
                win_min = center_mz - ISOLATION_WINDOW_HALF_WIDTH
                win_max = center_mz + ISOLATION_WINDOW_HALF_WIDTH
                sr = self._mz_rect(
                    win_min, win_max, lo, GW, GH,
                    fill_color=RED, fill_opacity=0.08,
                    stroke_color=WHITE, stroke_width=0.8,
                )
                subs.add(sr)
                sb = self._make_bars_mz(
                    win_min, win_max, lo, GW, GH,
                    n=5, color=RED,
                )
                sub_bars.add(sb)

            self.play(FadeIn(lbl_ms2_min, lbl_ms2_max, ms2_rect), run_time=t)

            if not fast:
                for i in range(MS2_PER_CYCLE):
                    self.play(FadeIn(subs[i], sub_bars[i]), run_time=0.08)
                self.wait(0.3)
                self.play(FadeOut(sub_bars), run_time=t)
            else:
                self.play(FadeIn(subs, sub_bars), run_time=t)
                self.play(FadeOut(sub_bars), run_time=t * 0.5)

            # Build the RT-graph MS2 block: red rect + 38 visible sub-divisions.
            rt_h_ms2 = RH * np.random.uniform(0.20, 0.55)
            rt_ms2_group = self._make_rt_ms2_block(
                rt_x_cursor, ro, rt_h_ms2, ms2_block_w, scan_uw
            )

            ms2_left_group = VGroup(ms2_rect, subs)
            self.play(
                FadeOut(lbl_ms2_min, lbl_ms2_max),
                ReplacementTransform(ms2_left_group, rt_ms2_group),
                run_time=t * 1.5,
            )
            rt_x_cursor += ms2_block_w

        self.wait(2)

    # ── coordinate helpers ────────────────────────────────────────────

    def _mz_to_x(self, mz: float, lo: np.ndarray, GW: float) -> float:
        """Absolute x position for a given m/z on the fixed 300-1500 scale."""
        return lo[0] + (mz - X_AXIS_MIN) / X_AXIS_SPAN * GW

    def _mz_rect(
        self,
        mz_min: float,
        mz_max: float,
        lo: np.ndarray,
        GW: float,
        GH: float,
        **rect_kwargs,
    ) -> Rectangle:
        """Rectangle spanning [mz_min, mz_max] on the fixed x-axis, full graph height."""
        x_l = self._mz_to_x(mz_min, lo, GW)
        x_r = self._mz_to_x(mz_max, lo, GW)
        w = x_r - x_l
        return Rectangle(width=w, height=GH, **rect_kwargs).move_to(
            [(x_l + x_r) / 2, lo[1] + GH / 2, 0]
        )

    def _range_labels(
        self,
        mz_min: float,
        mz_max: float,
        lo: np.ndarray,
        GW: float,
    ) -> tuple:
        """Pair of dynamic range labels placed below the x-axis at the rect edges."""
        x_l = self._mz_to_x(mz_min, lo, GW)
        x_r = self._mz_to_x(mz_max, lo, GW)
        y = lo[1] - 0.52
        lbl_min = Text(f"{mz_min:.1f}", font_size=13, color=YELLOW).move_to([x_l, y, 0])
        lbl_max = Text(f"{mz_max:.1f}", font_size=13, color=PURPLE).move_to([x_r, y, 0])
        
        # Vertical lines extending from the x-axis to the labels
        line_l = Line([x_l, lo[1], 0], [x_l, y + 0.15, 0], stroke_width=1, color=YELLOW)
        line_r = Line([x_r, lo[1], 0], [x_r, y + 0.15, 0], stroke_width=1, color=PURPLE)
        
        return VGroup(lbl_min, line_l), VGroup(lbl_max, line_r)

    # ── bar generators ────────────────────────────────────────────────

    def _make_bars_mz(
        self,
        mz_min: float,
        mz_max: float,
        lo: np.ndarray,
        GW: float,
        GH: float,
        n: int = 30,
        color=BLUE,
    ) -> VGroup:
        """Spectrum bars placed at correct m/z positions on the fixed scale."""
        bars = VGroup()
        margin = (mz_max - mz_min) * 0.04
        mz_vals = np.sort(
            np.random.uniform(mz_min + margin, mz_max - margin, n)
        )
        ys = np.random.exponential(0.25, n)
        ys = np.clip(ys, 0.02, None)
        ys /= ys.max()
        for _ in range(max(1, n // 10)):
            ys[np.random.randint(n)] = np.random.uniform(0.55, 1.0)

        for mz, y_frac in zip(mz_vals, ys):
            x = self._mz_to_x(mz, lo, GW)
            h = GH * y_frac * 0.85
            bars.add(
                Line([x, lo[1], 0], [x, lo[1] + h, 0], stroke_width=1.2, color=color)
            )
        return bars

    # ── RT-graph block builder ────────────────────────────────────────

    def _make_rt_ms2_block(
        self,
        x_start: float,
        ro: np.ndarray,
        height: float,
        total_w: float,
        scan_uw: float,
    ) -> VGroup:
        """Red RT block with MS2_PER_CYCLE visible sub-divisions (black borders)."""
        cx = x_start + total_w / 2

        outer = Rectangle(
            width=total_w * 0.98,
            height=height,
            fill_color=RED,
            fill_opacity=0.45,
            stroke_color=RED,
            stroke_width=1.0,
        ).move_to([cx, ro[1], 0], aligned_edge=DOWN)

        subs = VGroup()
        for i in range(MS2_PER_CYCLE):
            sub_cx = x_start + scan_uw * (i + 0.5)
            sub = Rectangle(
                width=scan_uw * 0.92,
                height=height,
                fill_opacity=0.0,
                stroke_color=BLACK,
                stroke_width=0.4,
            ).move_to([sub_cx, ro[1], 0], aligned_edge=DOWN)
            subs.add(sub)

        return VGroup(outer, subs)
