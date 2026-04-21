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
        self.wait(0.3)

        # ── Persistent target caption ─────────────────────────────────
        intro_caption = Text(
            f"Tracking target m/z ≈ {EXAMPLE_TARGET_MZ:.1f}   (isolated in Phase B)",
            font_size=20,
            color=YELLOW,
        ).to_edge(UP, buff=0.3)
        self.play(FadeIn(intro_caption))
        self.wait(0.2)

        # ── Persistent MS1 bracket ────────────────────────────────────
        ms1_bracket_group = self._mz_bracket(
            MS1_MZ_MIN,
            MS1_MZ_MAX,
            lo,
            GW,
            GH,
            label="MS1 survey scan range",
            color=BLUE,
            direction=UP,
            vertical_shift=UP * 0.6,
            label_direction=UP,
        )

        self.play(FadeIn(ms1_bracket_group))

        # ── RT-graph geometry (visually exaggerated MS1 width) ────────
        # Real MS1 scans are one of 39 scans per cycle, so they're almost
        # invisibly thin at true proportion. We bump the MS1 to a visible
        # fraction of each cycle so the narrative works.
        n_cycles_total = 12
        ms1_scan_units = 5      # visual width of an MS1 block, in "scan units"
        ms2_scan_units = MS2_PER_CYCLE
        cycle_units = ms1_scan_units + ms2_scan_units
        scan_uw = RW / (n_cycles_total * cycle_units)
        ms1_block_w = ms1_scan_units * scan_uw
        ms2_block_w = ms2_scan_units * scan_uw
        rt_x_cursor = ro[0]

        # ── Top-right legend (replaces per-block "38 MS2" / MS1 labels) ──
        legend_scale = 0.18
        legend_ms1_swatch = Rectangle(
            width=legend_scale * 1.4, height=legend_scale * 1.4,
            fill_color=BLUE, fill_opacity=0.55,
            stroke_color=BLUE, stroke_width=1.0,
        )
        legend_ms1_text = Text("MS1 survey scan", font_size=14).next_to(
            legend_ms1_swatch, RIGHT, buff=0.15
        )
        legend_ms1 = VGroup(legend_ms1_swatch, legend_ms1_text)

        legend_ms2_swatch = Rectangle(
            width=legend_scale * 1.4, height=legend_scale * 1.4,
            fill_color=RED, fill_opacity=0.45,
            stroke_color=RED, stroke_width=1.0,
        )
        legend_ms2_text = Text("Block of 38 MS2 scans", font_size=14).next_to(
            legend_ms2_swatch, RIGHT, buff=0.15
        )
        legend_ms2 = VGroup(legend_ms2_swatch, legend_ms2_text)

        legend = VGroup(legend_ms1, legend_ms2).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15
        ).to_corner(UR, buff=0.35)
        self.play(FadeIn(legend))

        # ── Target coordinates ────────────────────────────────────────
        target_x_left = self._mz_to_x(EXAMPLE_TARGET_MZ, lo, GW)
        target_sub_idx = int(round(
            (EXAMPLE_TARGET_MZ - INTERLEAVED_PHASES[1]["target_min_mz"])
            / ISOLATION_TARGET_SPACING
        ))
        target_frac = (target_sub_idx + 0.5) / MS2_PER_CYCLE

        # ── Main animation loop (A B C D × 3) ─────────────────────────
        phases = list(INTERLEAVED_PHASES) * 3
        phase_b_blocks = []
        rt_objects = VGroup()  # everything on the RT graph, for later shift

        for ci, phase in enumerate(phases):
            fast = ci >= 1
            t = 0.45 if fast else 0.7

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

            rt_ms1 = Rectangle(
                width=ms1_block_w * 0.9, height=RH,
                fill_color=BLUE, fill_opacity=0.35,
                stroke_color=BLUE, stroke_width=1.0,
            ).move_to([rt_x_cursor + ms1_block_w / 2, ro[1], 0], aligned_edge=DOWN)

            self.play(
                FadeOut(lbl_ms1_min, lbl_ms1_max),
                ReplacementTransform(ms1_rect, rt_ms1),
                run_time=t * 1.5,
            )
            rt_x_cursor += ms1_block_w
            rt_objects.add(rt_ms1)

            # ────────────────────────────────────────────────────────
            # MS2 SCAN  (red) — full-height red box, random peaks inside,
            # labelled "38 MS2 windows". Phase B also gets a yellow
            # target-m/z indicator so the viewer knows why it matters.
            # ────────────────────────────────────────────────────────
            p_min = phase["window_min_mz"]
            p_max = phase["window_max_mz"]
            x_l = self._mz_to_x(p_min, lo, GW)
            x_r = self._mz_to_x(p_max, lo, GW)

            lbl_ms2_min, lbl_ms2_max = self._range_labels(p_min, p_max, lo, GW)
            ms2_rect = self._mz_rect(
                p_min, p_max, lo, GW, GH,
                fill_color=RED, fill_opacity=0.12,
                stroke_color=RED, stroke_width=1.5,
            )
            new_ms2_bracket_group = self._phase_bracket(phase, lo, GW, GH)

            peaks_ms2 = self._make_bars_mz(
                p_min + 0.3, p_max - 0.3, lo, GW, GH,
                n=55, color=RED,
            )

            self.play(
                FadeIn(lbl_ms2_min, lbl_ms2_max, ms2_rect),
                FadeIn(new_ms2_bracket_group),
                run_time=t,
            )
            ms2_bracket_group = new_ms2_bracket_group
            self.play(FadeIn(peaks_ms2), run_time=t)

            # Phase-B target indicator on the left graph.
            target_extras = VGroup()
            phase_b_note = None
            if phase["name"] == "B":
                target_line = Line(
                    [target_x_left, lo[1], 0],
                    [target_x_left, lo[1] + GH, 0],
                    stroke_color=YELLOW,
                    stroke_width=2.5,
                )
                target_label = Text(
                    f"{EXAMPLE_TARGET_MZ:.1f}",
                    font_size=13,
                    color=YELLOW,
                ).move_to([target_x_left, lo[1] + GH + 0.22, 0])
                target_extras.add(target_line, target_label)

                if ci == 1:
                    # First Phase B: explain why this phase matters.
                    phase_b_note = Text(
                        "→ Phase B window contains our target m/z",
                        font_size=16,
                        color=YELLOW,
                    ).next_to(intro_caption, DOWN, buff=0.12)
                    self.play(
                        FadeIn(target_extras),
                        FadeIn(phase_b_note),
                        run_time=t * 0.8,
                    )
                    self.wait(0.6)
                else:
                    self.play(FadeIn(target_extras), run_time=t * 0.7)
                    self.wait(0.15)

            self.play(FadeOut(peaks_ms2), run_time=t * 0.5)
            if phase_b_note is not None:
                self.play(FadeOut(phase_b_note), run_time=t * 0.5)

            # ── RT MS2 block: full-height, peaks inside, optional target marker ──
            ms2_has_target = phase["name"] == "B"
            rt_ms2_group = self._make_rt_ms2_block(
                rt_x_cursor, ro, RH, ms2_block_w, scan_uw,
                has_target=ms2_has_target,
                target_frac=target_frac if ms2_has_target else None,
            )

            left_ms2_group = VGroup(ms2_rect, *target_extras)
            self.play(
                FadeOut(lbl_ms2_min, lbl_ms2_max, ms2_bracket_group),
                ReplacementTransform(left_ms2_group, rt_ms2_group),
                run_time=t * 1.5,
            )
            # A/B/C/D phase letter above the MS2 block
            phase_letter = Text(
                phase["name"], font_size=16, color=RED,
            ).move_to([rt_x_cursor + ms2_block_w / 2, ro[1] + RH + 0.18, 0])
            self.play(FadeIn(phase_letter), run_time=t * 0.4)
            rt_objects.add(phase_letter)

            rt_x_cursor += ms2_block_w
            rt_objects.add(rt_ms2_group)

            if phase["name"] == "B":
                # rt_ms2_group layout when has_target=True:
                #   [0] outer rect, [1] peaks, [2] target marker
                phase_b_blocks.append({
                    "ms1": rt_ms1,
                    "ms2_group": rt_ms2_group,
                    "target_marker": rt_ms2_group[2],
                })

        self.play(FadeOut(ms1_bracket_group))
        self.wait(0.3)

        # ── Transition: fade left graph, center RT graph ──────────────
        shift_vec = LEFT * (ro[0] + RW / 2)   # move RT graph center to x=0
        self.play(
            FadeOut(l_frame),
            FadeOut(intro_caption),
            r_frame.animate.shift(shift_vec),
            rt_objects.animate.shift(shift_vec),
            run_time=1.2,
        )
        self.wait(0.3)

        # ── Augmented-spectrum walkthrough ────────────────────────────
        augment_title = Text(
            "Constructing an Augmented Spectrum",
            font_size=26,
        ).to_edge(UP, buff=0.3)
        self.play(FadeIn(augment_title))

        # Step 1 — central MS2 scan (middle Phase B, width = 0).
        step1_caption = Text(
            f"Step 1: Select central MS2 scan  (m/z ≈ {EXAMPLE_TARGET_MZ:.1f}, width = 0)",
            font_size=18,
            color=YELLOW,
        ).next_to(augment_title, DOWN, buff=0.2)

        center_block = phase_b_blocks[1]
        center_highlight = SurroundingRectangle(
            center_block["target_marker"],
            color=YELLOW,
            stroke_width=3,
            buff=0.06,
        )

        self.play(FadeIn(step1_caption))
        self.play(Create(center_highlight))
        self.wait(1.5)

        # Step 2 — flanking MS2 scans (width = ±1).
        step2_caption = Text(
            "Step 2: Include neighbouring MS2 scans  (width = ±1)",
            font_size=18,
            color=ORANGE,
        ).next_to(augment_title, DOWN, buff=0.2)

        left_highlight = SurroundingRectangle(
            phase_b_blocks[0]["target_marker"],
            color=ORANGE,
            stroke_width=3,
            buff=0.06,
        )
        right_highlight = SurroundingRectangle(
            phase_b_blocks[2]["target_marker"],
            color=ORANGE,
            stroke_width=3,
            buff=0.06,
        )

        self.play(ReplacementTransform(step1_caption, step2_caption))
        self.play(Create(left_highlight), Create(right_highlight))
        self.wait(1.5)

        # Step 3 — corresponding MS1 survey scans (one per selected cycle).
        step3_caption = Text(
            "Step 3: Gather corresponding MS1 survey scans",
            font_size=18,
            color=BLUE_C,
        ).next_to(augment_title, DOWN, buff=0.2)

        ms1_highlights = VGroup(*[
            SurroundingRectangle(
                blk["ms1"],
                color=BLUE_C,
                stroke_width=3,
                buff=0.04,
            )
            for blk in phase_b_blocks
        ])

        self.play(ReplacementTransform(step2_caption, step3_caption))
        self.play(Create(ms1_highlights))
        self.wait(2.5)

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

    def _mz_bracket(
        self,
        mz_min: float,
        mz_max: float,
        lo: np.ndarray,
        GW: float,
        GH: float,
        label: str,
        color,
        direction=DOWN,
        vertical_shift=ORIGIN,
        label_direction=DOWN,
    ) -> VGroup:
        """Brace + label anchored to an m/z span just above the left plot."""
        rect = self._mz_rect(mz_min, mz_max, lo, GW, GH)
        brace = BraceBetweenPoints(
            rect.get_corner(UL),
            rect.get_corner(UR),
            direction=direction,
            buff=0.08,
        ).set_color(color)
        brace.shift(vertical_shift)
        text = Text(label, font_size=14, color=color).next_to(
            brace, label_direction, buff=0.08
        )
        return VGroup(brace, text)

    def _phase_bracket(
        self,
        phase: dict,
        lo: np.ndarray,
        GW: float,
        GH: float,
    ) -> VGroup:
        """Describe the active DIA phase and the span covered by its 38 windows."""
        return self._mz_bracket(
            phase["window_min_mz"],
            phase["window_max_mz"],
            lo,
            GW,
            GH,
            label=f"Phase {phase['name']} DIA span ({MS2_PER_CYCLE} MS2 windows)",
            color=RED,
            direction=UP,
            vertical_shift=UP*0.01,
            label_direction=UP,
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
        has_target: bool = False,
        target_frac: float = None,
    ) -> VGroup:
        """Full-height red RT block with random peak lines and optional target marker.

        Group layout:
            [0] outer rect
            [1] peak lines (VGroup)
            [2] target marker  (only present when has_target=True)
        """
        cx = x_start + total_w / 2

        outer = Rectangle(
            width=total_w * 0.98,
            height=height,
            fill_color=RED,
            fill_opacity=0.35,
            stroke_color=RED,
            stroke_width=1.2,
        ).move_to([cx, ro[1], 0], aligned_edge=DOWN)

        peaks = VGroup()
        n_peaks = 14
        x_lo = x_start + total_w * 0.04
        x_hi = x_start + total_w * 0.96
        xs = np.sort(np.random.uniform(x_lo, x_hi, n_peaks))
        ys = np.random.exponential(0.3, n_peaks)
        ys = np.clip(ys, 0.05, None)
        ys /= ys.max()
        for x, yf in zip(xs, ys):
            h = height * yf * 0.8
            peaks.add(Line(
                [x, ro[1], 0], [x, ro[1] + h, 0],
                stroke_width=1.0, color=WHITE,
            ))

        group = VGroup(outer, peaks)

        if has_target and target_frac is not None:
            target_x = x_start + total_w * target_frac
            target_marker = Line(
                [target_x, ro[1], 0],
                [target_x, ro[1] + height, 0],
                stroke_width=2.5,
                color=YELLOW,
            )
            group.add(target_marker)

        return group
