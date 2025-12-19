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
        # Create x-axis only (no y-axis) - moved way down
        x_axis = Line(
            start=LEFT * 5.5,
            end=RIGHT * 5.5,
            color=WHITE,
            stroke_width=2
        )
        x_axis.shift(DOWN * 2.5)
        
        # Add arrow tip to x-axis
        x_arrow_tip = Triangle(color=WHITE, fill_opacity=1).scale(0.1)
        x_arrow_tip.rotate(-PI/2)
        x_arrow_tip.next_to(x_axis, RIGHT, buff=0)
        
        # Add x-axis label
        x_label = Text("Time", font_size=24).next_to(x_axis, DOWN, buff=0.3)
        
        # Display the axis and label
        self.play(Create(x_axis), Create(x_arrow_tip), Write(x_label))
        self.wait(1.5)
        
        # Define MS2 groups - each group belongs to an MS1 scan
        # Group 1: MS2 scans 1-3 belong to MS1 scan 1
        # Group 2: MS2 scans 4-6 belong to MS1 scan 2  
        # Group 3: MS2 scan 7-9 belongs to MS1 scan 3
        
        # Bar dimensions
        bar_width = 0.6
        bar_height = 1.5  # Shorter bars to leave room for arrows
        bar_spacing = 0.15  # Spacing within group
        group_spacing = 0.8  # Larger spacing between MS1 groups
        
        # Calculate positions for the 3 groups of 3 bars each
        # Start position for first bar
        start_x = -4.5
        
        ms2_bars = VGroup()
        ms2_positions = []  # Store center x positions for arrows
        ms2_to_ms1_idx = []  # Store which MS1 each MS2 belongs to
        
        current_x = start_x
        for group_idx in range(3):  # 3 MS1 groups
            for bar_idx in range(3):  # 3 MS2 bars per group
                bar = Rectangle(
                    width=bar_width,
                    height=bar_height,
                    color=RED,
                    fill_color=RED,
                    fill_opacity=0.8,
                    stroke_width=2
                )
                # Position bar so bottom sits on x-axis
                bar.move_to([current_x, x_axis.get_center()[1] + bar_height/2, 0])
                ms2_bars.add(bar)
                ms2_positions.append(current_x)
                ms2_to_ms1_idx.append(group_idx)
                
                current_x += bar_width + bar_spacing
            
            # Add extra spacing between groups (minus the bar_spacing we already added)
            current_x += group_spacing - bar_spacing
        
        # Create MS1 labels and braces at the top - with more space above bars for arrows
        ms1_labels = ["MS1₁", "MS1₂", "MS1₃"]
        
        ms1_braces = VGroup()
        ms1_texts = VGroup()
        brace_y_position = x_axis.get_center()[1] + bar_height + 1.5  # More space above bars for arrows
        
        # Calculate brace positions based on actual bar positions
        group_starts = [0, 3, 6]  # Starting indices for each group
        for i, (label, start_idx) in enumerate(zip(ms1_labels, group_starts)):
            # Get the leftmost and rightmost bar positions in this group
            left_x = ms2_positions[start_idx] - bar_width/2
            right_x = ms2_positions[start_idx + 2] + bar_width/2
            
            # Create horizontal brace facing down (tip points down toward bars)
            brace = Brace(
                Line(
                    start=[left_x, brace_y_position, 0],
                    end=[right_x, brace_y_position, 0]
                ),
                direction=UP,  # Changed to UP so brace tip points DOWN
                color=BLUE
            )
            brace.shift(DOWN * 0.15)  # Shift bracket down
            
            # MS1 label above the brace
            ms1_text = Text(label, color=BLUE, font_size=22).next_to(brace, UP, buff=0.1)
            
            ms1_braces.add(brace)
            ms1_texts.add(ms1_text)
        
        # Store heights for arrow calculations (all same now)
        ms2_heights = [bar_height] * 9
        
        # Animate MS2 bars first
        self.play(Create(ms2_bars))
        self.wait(1.5)
        
        # Animate MS1 braces and labels
        self.play(Create(ms1_braces), Write(ms1_texts))
        self.wait(1.5)
        
        # Create legend in top right
        legend_ms1_rect = Rectangle(width=0.5, height=0.3, color=BLUE, fill_color=BLUE, fill_opacity=0.8)
        legend_ms1_text = Text("MS1", font_size=24).next_to(legend_ms1_rect, RIGHT, buff=0.2)
        legend_ms1 = VGroup(legend_ms1_rect, legend_ms1_text)
        
        legend_ms2_rect = Rectangle(width=0.5, height=0.3, color=RED, fill_color=RED, fill_opacity=0.8)
        legend_ms2_text = Text("MS2", font_size=24).next_to(legend_ms2_rect, RIGHT, buff=0.2).shift(DOWN * 0.15)
        legend_ms2 = VGroup(legend_ms2_rect, legend_ms2_text)
        
        legend = VGroup(legend_ms1, legend_ms2).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        legend.to_corner(UR, buff=0.5)
        
        self.play(FadeIn(legend))
        self.wait(1.5)
        
        # Add title at the top
        title = Text("Which MS1 does each MS2 scan correspond to?", color=PURPLE, font_size=28).to_edge(UP, buff=0.3)
        
        # Create mapping from MS2 bar index to MS1 index for arrows
        ms2_to_ms1_mapping = []
        for bar_idx, ms1_idx in enumerate(ms2_to_ms1_idx):
            ms2_to_ms1_mapping.append((bar_idx, ms1_idx))
        
        # Create purple arrows pointing upward from MS2 bars to their parent MS1 braces
        arrows = VGroup()
        for ms2_bar_idx, ms1_idx in ms2_to_ms1_mapping:
            # Arrow from top of MS2 bar upward to the bottom of the corresponding MS1 brace
            brace_bottom = ms1_braces[ms1_idx].get_bottom()
            ms2_bar_top = ms2_bars[ms2_bar_idx].get_top()
            
            arrow = Arrow(
                start=ms2_bar_top + UP * 0.1,
                end=[ms2_bar_top[0], brace_bottom[1] - 0.1, 0],
                color=PURPLE,
                stroke_width=3,
                buff=0.05,
                max_tip_length_to_length_ratio=0.15
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
        
        # Highlight the middle MS2 bar (position index 4, which is in the middle)
        ms2_idx_to_highlight = len(ms2_positions) // 2
        
        # Create a highlight around the selected MS2 bar
        highlight_rect = SurroundingRectangle(
            ms2_bars[ms2_idx_to_highlight],
            color=GOLD,
            buff=0.0
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
        leftmost_bar = ms2_bars[selected_ms2_indices[0]]
        rightmost_bar = ms2_bars[selected_ms2_indices[-1]]
        x_axis_y = x_axis.get_center()[1]
        
        range_line = Line(
            start=[leftmost_bar.get_center()[0], x_axis_y, 0],
            end=[rightmost_bar.get_center()[0], x_axis_y, 0],
            color=PURPLE,
            stroke_width=12
        )
        
        # Add arrow tips at both ends to show the range
        left_arrow = Arrow(
            start=[leftmost_bar.get_center()[0], x_axis_y - 0.5, 0],
            end=[leftmost_bar.get_center()[0], x_axis_y, 0],
            color=PURPLE,
            buff=0,
            stroke_width=6,
            max_tip_length_to_length_ratio=0.4
        )
        
        right_arrow = Arrow(
            start=[rightmost_bar.get_center()[0], x_axis_y - 0.5, 0],
            end=[rightmost_bar.get_center()[0], x_axis_y, 0],
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
                    buff=0.1
                )
                neighbor_rects.add(rect)
        
        self.play(Create(neighbor_rects))
        self.wait(2)
        
        
        # Step 3: Pick the MS1 spectra corresponding to those
        step_3 = Text("3. Pick the MS1 spectra corresponding to those", color=PURPLE, font_size=28).to_edge(UP, buff=0.3)
        self.play(ReplacementTransform(step_2, step_3))
        self.wait(1.5)
        
        # For each selected MS2 spectra, highlight the corresponding MS1 braces
        highlighted_ms1_indices = set()
        for idx in selected_ms2_indices:
            # The ms2_to_ms1_idx list maps each MS2 bar index to its MS1 index
            highlighted_ms1_indices.add(ms2_to_ms1_idx[idx])
        
        # Create highlights around the corresponding MS1 braces and labels
        ms1_highlights = VGroup()
        for ms1_idx in highlighted_ms1_indices:
            # Highlight the brace and label together
            brace_and_label = VGroup(ms1_braces[ms1_idx], ms1_texts[ms1_idx])
            rect = SurroundingRectangle(
                brace_and_label,
                color=GOLD,
                buff=0.15
            )
            ms1_highlights.add(rect)
        
        self.play(Create(ms1_highlights))
        self.wait(3)
        
        
    