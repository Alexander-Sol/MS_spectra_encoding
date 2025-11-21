from manim import *
import numpy as np

class AugmentedManim(Scene):
    def construct(self):
        # ===== NEW INTRODUCTORY SCENE =====
        # Scene 1: Full Mass Spectrum with MS1 and MS2 scans
        
        # Create title
        intro_title = Text("MS1 and MS2 Acquisition Method", color=PURPLE, font_size=32).to_edge(UP, buff=0.3)
        self.play(Write(intro_title))
        self.wait(1)
        
        # Create axes for full mass spectrum
        full_axes = Axes(
            x_range=[0, 1000, 100],
            y_range=[0, 100, 10],
            x_length=10,
            y_length=5,
            axis_config={"include_tip": True},
        )
        full_axes.shift(DOWN * 0.5)
        
        # Labels
        mz_label = Text("m/z", font_size=24).next_to(full_axes.x_axis, DOWN, buff=0.2)
        intensity_label = Text("Intensity", font_size=24).next_to(full_axes.y_axis, LEFT, buff=0.2)
        
        self.play(Create(full_axes), Write(mz_label), Write(intensity_label))
        self.wait(1)
        
        # Create a realistic looking mass spectrum with many peaks
        np.random.seed(42)
        peak_positions = np.random.uniform(100, 900, 40)
        peak_heights = np.random.uniform(20, 95, 40)
        
        spectrum_bars = VGroup()
        for x_pos, height in zip(peak_positions, peak_heights):
            bar = Line(
                start=full_axes.c2p(x_pos, 0),
                end=full_axes.c2p(x_pos, height),
                color=WHITE,
                stroke_width=2
            )
            spectrum_bars.add(bar)
        
        self.play(Create(spectrum_bars), run_time=2)
        self.wait(1)
        
        # Define the isolation window (e.g., from m/z 200 to 850)
        isolation_start = 200
        isolation_end = 850
        
        # Create MS1 scan label and highlight the isolation window
        ms1_label = Text("MS1 Scan (1 second)", color=BLUE, font_size=28).to_edge(UP, buff=1.2)
        
        # Create a rectangle to highlight the isolation window
        iso_window_rect = Rectangle(
            width=full_axes.c2p(isolation_end, 0)[0] - full_axes.c2p(isolation_start, 0)[0],
            height=full_axes.c2p(0, 100)[1] - full_axes.c2p(0, 0)[1],
            color=BLUE,
            fill_opacity=0.2,
            stroke_width=3
        )
        iso_window_rect.move_to(full_axes.c2p((isolation_start + isolation_end) / 2, 50))
        
        self.play(
            ReplacementTransform(intro_title, ms1_label),
            Create(iso_window_rect)
        )
        self.wait(2)
        
        # Fade out the MS1 highlight
        self.play(iso_window_rect.animate.set_fill(opacity=0.05), iso_window_rect.animate.set_stroke(width=1, opacity=0.3))
        self.wait(0.5)
        
        # Now divide the isolation window into 5 MS2 scans
        ms2_label = Text("5 MS2 Scans (200ms each)", color=RED, font_size=28).to_edge(UP, buff=1.2)
        self.play(ReplacementTransform(ms1_label, ms2_label))
        self.wait(1)
        
        # Create 5 equal divisions of the isolation window
        num_ms2_scans = 5
        scan_width = (isolation_end - isolation_start) / num_ms2_scans
        ms2_rects = VGroup()
        
        for i in range(num_ms2_scans):
            scan_start = isolation_start + i * scan_width
            scan_end = scan_start + scan_width
            
            rect = Rectangle(
                width=full_axes.c2p(scan_end, 0)[0] - full_axes.c2p(scan_start, 0)[0],
                height=full_axes.c2p(0, 100)[1] - full_axes.c2p(0, 0)[1],
                color=RED,
                fill_opacity=0.3,
                stroke_width=3
            )
            rect.move_to(full_axes.c2p((scan_start + scan_end) / 2, 50))
            ms2_rects.add(rect)
        
        # Animate each MS2 scan sequentially
        for i, rect in enumerate(ms2_rects):
            scan_num_label = Text(f"MS2 Scan {i+1}", color=RED, font_size=20).next_to(rect, UP, buff=0.1)
            self.play(Create(rect), Write(scan_num_label), run_time=0.8)
            self.wait(0.3)
            self.play(FadeOut(scan_num_label), run_time=0.3)
        
        self.wait(2)
        
        # Fade out the entire introductory scene
        self.play(
            FadeOut(ms2_label),
            FadeOut(spectrum_bars),
            FadeOut(full_axes),
            FadeOut(mz_label),
            FadeOut(intensity_label),
            FadeOut(iso_window_rect),
            FadeOut(ms2_rects),
            run_time=1.5
        )
        self.wait(1)
        
        # ===== ORIGINAL SCENE CONTINUES =====
        # Create axes for quadrant 1 only
        axes = Axes(
            x_range=[0, 12, 1],
            y_range=[0, 12, 1],
            axis_config={"include_tip": True},
        )
        
        # Add x-axis label
        x_label = Text("Small Window in Mass Spectrum (simplified)", font_size=20).next_to(axes.x_axis, DOWN, buff=0.2)
        
        # Display the axes, label, and title
        self.play(Create(axes), Write(x_label))
        self.wait(1.5)
        
        # MS1 scan - 3 bars equally spaced (blue)
        ms1_positions = [2, 6, 10]  # x positions
        ms1_heights = [6, 8, 5]  # y heights
        ms1_bars = VGroup()
        
        for x_pos, height in zip(ms1_positions, ms1_heights):
            bar = Line(
                start=axes.c2p(x_pos, 0),
                end=axes.c2p(x_pos, height),
                color=BLUE,
                stroke_width=6
            )
            ms1_bars.add(bar)
        
        # MS2 scan - 4 bars between MS1 bars (red)
        ms2_positions = [3, 4,5, 7, 8, 9, 11]  # x positions between MS1 bars
        ms2_heights = [3, 5, 4, 6, 4,3,7]  # y heights
        ms2_bars = VGroup()
        
        for x_pos, height in zip(ms2_positions, ms2_heights):
            bar = Line(
                start=axes.c2p(x_pos, 0),
                end=axes.c2p(x_pos, height),
                color=RED,
                stroke_width=6
            )
            ms2_bars.add(bar)
        
        # Animate MS1 bars
        self.play(Create(ms1_bars))
        self.wait(1.5)
        
        # Animate MS2 bars
        self.play(Create(ms2_bars))
        self.wait(1.5)
        
        # Create legend in top right
        legend_ms1_line = Line(ORIGIN, RIGHT * 0.5, color=BLUE, stroke_width=6)
        legend_ms1_text = Text("MS1", font_size=24).next_to(legend_ms1_line, RIGHT, buff=0.2)
        legend_ms1 = VGroup(legend_ms1_line, legend_ms1_text)
        
        legend_ms2_line = Line(ORIGIN, RIGHT * 0.5, color=RED, stroke_width=6)
        legend_ms2_text = Text("MS2", font_size=24).next_to(legend_ms2_line, RIGHT, buff=0.2)
        legend_ms2 = VGroup(legend_ms2_line, legend_ms2_text)
        
        legend = VGroup(legend_ms1, legend_ms2).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        legend.to_corner(UR, buff=0.5)
        
        self.play(FadeIn(legend))
        self.wait(1.5)
                # Add title at the top
        title = Text("Which MS1 does each MS2 scan correspond to?", color=PURPLE,font_size=28).to_edge(UP, buff=0.3)


        # Create purple arrows from MS2 bars to corresponding MS1 bars
        # MS2 bars at positions [3, 4, 5, 7, 8, 9, 11] correspond to MS1 bars at [2, 6, 10]
        # Bars at 3, 4, 5 -> MS1 at 2
        # Bars at 7, 8, 9 -> MS1 at 6
        # Bar at 11 -> MS1 at 10
        ms2_to_ms1_mapping = [
            (3, 2), (4, 2), (5, 2),  # First three MS2 bars -> first MS1 bar
            (7, 6), (8, 6), (9, 6),  # Next three MS2 bars -> second MS1 bar
            (11, 10)                  # Last MS2 bar -> third MS1 bar
        ]
        
        arrows = VGroup()
        for ms2_pos, ms1_pos in ms2_to_ms1_mapping:
            ms2_idx = ms2_positions.index(ms2_pos)
            ms1_idx = ms1_positions.index(ms1_pos)
            
            # Arrow from top of MS2 bar to top of MS1 bar
            arrow = CurvedArrow(
                start_point=axes.c2p(ms2_pos, ms2_heights[ms2_idx]),
                end_point=axes.c2p(ms1_pos, ms1_heights[ms1_idx]),
                color=PURPLE,
                stroke_width=3
            )
            arrows.add(arrow)
        self.play(Write(title))
        self.wait(1)
        self.play(Create(arrows), run_time=3.5)

        self.wait(2.5)
        self.play(FadeOut(arrows))
        aug_spectra_title = Text("Now, let's build an augmented spectrum", color=PURPLE, font_size=28).to_edge(UP, buff=0.3)
        self.play(ReplacementTransform(title, aug_spectra_title))
        self.wait(2.5)
        
        # Step 1: Pick an MS2 Spectra
        step_1 = Text("1. Pick an MS2 Spectra", color=PURPLE, font_size=28).to_edge(UP, buff=0.3)
        self.play(ReplacementTransform(aug_spectra_title, step_1))
        self.wait(1.5)
        
        # Highlight the middle MS2 bar (position index 3, which is position 7)
        ms2_idx_to_highlight = len(ms2_positions) // 2
        
        # Create a highlight around the selected MS2 bar
        highlight_rect = SurroundingRectangle(
            ms2_bars[ms2_idx_to_highlight],
            color=GOLD,
            buff=0.1
        )
        
        self.play(Create(highlight_rect))
        self.wait(2)
        
        # Step 2: Pick a width for MS2 spectra to choose (width = 2, so 2 on each side)
        step_2 = Text("2. Include neighboring MS2 spectra\n            (width = 2 on each side)", color=PURPLE, font_size=28).to_edge(UP, buff=0.3)

        self.play(ReplacementTransform(step_1, step_2))
        self.wait(1.5)
        
        # Choose 2 MS2 spectra on each side (total of 5 including the original)
        center_idx = len(ms2_positions) // 2
        width = 2
        selected_ms2_indices = list(range(max(0, center_idx - width), min(len(ms2_positions), center_idx + width + 1)))
        
        # Create a horizontal line on the x-axis showing the range of inclusion
        leftmost_pos = ms2_positions[selected_ms2_indices[0]]
        rightmost_pos = ms2_positions[selected_ms2_indices[-1]]
        
        range_line = Line(
            start=axes.c2p(leftmost_pos, 0),
            end=axes.c2p(rightmost_pos, 0),
            color=PURPLE,
            stroke_width=12
        )
        
        # Add arrow tips at both ends to show the range
        left_arrow = Arrow(
            start=axes.c2p(leftmost_pos, -0.8),
            end=axes.c2p(leftmost_pos, 0),
            color=PURPLE,
            buff=0,
            stroke_width=6,
            max_tip_length_to_length_ratio=0.4
        )
        
        right_arrow = Arrow(
            start=axes.c2p(rightmost_pos, -0.8),
            end=axes.c2p(rightmost_pos, 0),
            color=PURPLE,
            buff=0,
            stroke_width=6,
            max_tip_length_to_length_ratio=0.4
        )
        
        range_indicator = VGroup(range_line, left_arrow, right_arrow)
        
        self.play(Create(range_indicator))
        self.wait(1)
        
        # Create highlights around the neighboring MS2 bars
        neighbor_rects = VGroup()
        for idx in selected_ms2_indices:
            if idx != ms2_idx_to_highlight:
                rect = SurroundingRectangle(
                    ms2_bars[idx],
                    color=GOLD,
                    buff=0.2
                )
                neighbor_rects.add(rect)
        
        self.play(Create(neighbor_rects))
        self.wait(2)
        
        
        # Step 3: Pick the MS1 spectra corresponding to those
        step_3 = Text("3. Pick the MS1 spectra corresponding to those", color=PURPLE, font_size=28).to_edge(UP, buff=0.3)
        self.play(ReplacementTransform(step_2, step_3))
        self.wait(1.5)
        
        # For each selected MS2 spectra, highlight the corresponding MS1 spectra
        highlighted_ms1_indices = set()
        for idx in selected_ms2_indices:
            ms2_pos = ms2_positions[idx]
            # Find corresponding MS1 based on the mapping
            for ms2_map_pos, ms1_map_pos in ms2_to_ms1_mapping:
                if ms2_map_pos == ms2_pos:
                    ms1_idx = ms1_positions.index(ms1_map_pos)
                    highlighted_ms1_indices.add(ms1_idx)
                    break
        
        # Create highlights around the corresponding MS1 bars
        ms1_rects = VGroup()
        for ms1_idx in highlighted_ms1_indices:
            rect = SurroundingRectangle(
                ms1_bars[ms1_idx],
                color=GOLD,
                buff=0.3
            )
            ms1_rects.add(rect)
        
        self.play(Create(ms1_rects))
        self.wait(3)
        
        
    