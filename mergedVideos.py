from manim import *
import numpy as np
from manim import logger
import logging
logger.setLevel(logging.WARNING)

# ---------- Helpers ----------
def make_title(scene: Scene, text="Similarity Preservation in Spectral Hashing"):
    title = Text(text, font_size=32, color=YELLOW)
    scene.play(Write(title))
    scene.play(title.animate.to_edge(UP))
    return title

# Comprehensive merged scene that combines all the individual scenes
class SimilarityPreservationComplete(Scene):
    def construct(self):
        # ========== SECTION 1: Explain binning briefly ==========
        title = make_title(self, "Spectral Binning and Hashing")
        self.play(FadeOut(title))
        
        
        # ========== Data ==========
        # Create the two sets of vectors (simplified representations)
        
        # Create specific color orderings and positions for each spectrum
        # f1 and f2 should be very similar (same colors, similar positions)
        # f4 should be radically different from f1 (different colors, different positions)
        
        # Define colors for each spectrum
        f1_colors = [RED, PINK, GREEN, RED, RED, PINK, GREEN, PINK] # red + green + pink
        f2_colors = [RED, GREEN, GREEN, RED, RED, PINK, GREEN, PINK]  # Same as f1 (similar)
        f3_colors = [PINK, TEAL, ORANGE, BLUE, YELLOW, GREEN, RED, PURPLE]  # Different ordering
        f4_colors = [BLUE, BLUE, GRAY, BLUE, GRAY, GRAY_BROWN, GRAY, BLUE] # gray + blue (8 elements)
        
        spectrum_color_orders = [f1_colors, f2_colors, f3_colors, f4_colors]
        
        # Define positions for each spectrum
        # f1: positions with some gaps
        f1_positions = [1, 2, 4, 7, 9, 11, 14, 16]
        # f2: very similar to f1 (only slightly shifted, mostly same)
        f2_positions = [0, 2, 4, 7, 3, 12, 14, 16]  
        # f3: different pattern
        f3_positions = [1, 3, 5, 8, 10, 12, 15, 17]
        # f4: radically different positions from f1
        f4_positions = [1, 3, 6, 8, 10, 13, 15, 18]
        
        spectrum_positions = [f1_positions, f2_positions, f3_positions, f4_positions]
        
        # Define bar heights for the SPECTRUM visualization (varying heights for realism)
        spectrum_f1_heights = [0.5, 0.3, 0.55, 0.4, 0.45, 0.35, 0.5, 0.4]
        
        # Define bar heights for FEATURE VECTORS (uniform height to fit the rectangle)
        UNIFORM_HEIGHT = 0.6  # Single height for all bars in feature vectors
        f1_heights = [UNIFORM_HEIGHT] * 8
        f2_heights = [UNIFORM_HEIGHT] * 8
        f3_heights = [UNIFORM_HEIGHT] * 8
        f4_heights = [UNIFORM_HEIGHT] * 8
        # Create dense colored bars inside with less whitespace between them
        # t1 and t2 should be similar (corresponding to f1 and f2)
        # t4 should be different (corresponding to f4)
        
        # Define positions for hashed versions (more compact)
        t1_positions = [0, 1, 8, 3, 5, 7, 9, 10]
        t2_positions = [0, 1, 8, 2, 5, 7, 9, 10]  # Very similar to t1 (same positions)
        t3_positions = [5, 2, 1, 3, 6, 8, 7, 4]  # Different pattern
        t4_positions = [1, 2, 4, 5, 7, 8, 10, 11]  # Radically different from t1
        
        t_spectrum_positions = [t1_positions, t2_positions, t3_positions, t4_positions]
        
        # Heights for t-boxes (uniform height)
        t1_heights = [UNIFORM_HEIGHT] * 8
        t2_heights = [UNIFORM_HEIGHT] * 8
        t3_heights = [UNIFORM_HEIGHT] * 8
        t4_heights = [UNIFORM_HEIGHT] * 8
        
        t_spectrum_heights = [t1_heights, t2_heights, t3_heights, t4_heights]

        # Create a title for the spectrum scene
        spectrum_title = Text("Mass Spectrum Visualization", font_size=32, color=YELLOW).to_edge(UP, buff=0.5)
        self.play(Write(spectrum_title))
        self.wait(1)
        
        # Create a spectrum visualization using f1_heights, f1_positions, and f1_colors
        # Set up axes for the spectrum - centered, larger
        axes = Axes(
            x_range=[0, 20, 2],
            y_range=[0, 0.7, 0.1],
            x_length=10,
            y_length=4,
            axis_config={"include_numbers": False, "color": GRAY},
            tips=False
        ).to_edge(UP, buff=1.0)
        
        # Add labels
        x_label = Text("m/z", font_size=24).next_to(axes.x_axis, DOWN, buff=0.2)
        y_label = Text("Intensity", font_size=24).rotate(90 * DEGREES).next_to(axes.y_axis, LEFT, buff=0.3)
        
        # Create vertical lines (stems) for each peak
        spectrum_lines = VGroup()
        for i, pos in enumerate(f1_positions):
            height = spectrum_f1_heights[i]  # Use spectrum heights (varying)
            color = f1_colors[i]
            
            # Create a vertical line from the x-axis to the peak height
            start_point = axes.c2p(pos, 0)
            end_point = axes.c2p(pos, height)
            line = Line(start_point, end_point, color=color, stroke_width=4)
            spectrum_lines.add(line)
        
        # Display the spectrum without label initially
        self.play(Create(axes), Write(x_label), Write(y_label))
        self.play(Create(spectrum_lines))
        self.wait(4)
        
        # Group spectrum without label for now
        spectrum_group = VGroup(axes, x_label, y_label, spectrum_lines)
        self.play(
            spectrum_group.animate.scale(0.5).to_edge(UP, buff=0.8),
            FadeOut(spectrum_title)
        )
        self.wait(1)
        
        # Create an arrow pointing down from the spectrum
        arrow_to_f1 = Arrow(
            spectrum_group.get_bottom(),
            spectrum_group.get_bottom() + DOWN * 1.0,
            color=WHITE,
            buff=0.1
        )
        self.play(Create(arrow_to_f1))
        self.wait(1)
        
        # Create f1 box (slightly smaller than the spectrum)
        spectrum_width = spectrum_group.width * 0.9 
        f1_box = Rectangle(width=spectrum_width, height=0.7, color=GREEN, fill_opacity=0.0, stroke_width=2)
        f1_box.next_to(arrow_to_f1, DOWN, buff=0.2)
        
        # Get the color order, positions, and heights for f1
        colors_for_f1 = f1_colors
        colored_positions_f1 = f1_positions
        bar_heights_f1 = f1_heights
        
        # Total positions span from first to last colored bar
        min_pos_f1 = min(colored_positions_f1)
        max_pos_f1 = max(colored_positions_f1)
        num_total_bars_f1 = max_pos_f1 - min_pos_f1 + 1
        bar_width_f1 = (f1_box.width - 0.2) / num_total_bars_f1
        
        bars_f1 = VGroup()
        for j in range(min_pos_f1, max_pos_f1 + 1):
            x_pos = f1_box.get_left()[0] + 0.1 + (j - min_pos_f1) * bar_width_f1 + bar_width_f1/2
            
            if j in colored_positions_f1:
                # Colored bar with varying height
                bar_idx = colored_positions_f1.index(j)
                bar = Rectangle(
                    width=bar_width_f1 * 0.9,
                    height=bar_heights_f1[bar_idx],
                    color=colors_for_f1[bar_idx],
                    fill_opacity=0.8,
                    stroke_width=1
                ).move_to([x_pos, f1_box.get_center()[1], 0])
                bars_f1.add(bar)
            else:
                # Empty/whitespace bar - now clearly visible
                empty_bar = Rectangle(
                    width=bar_width_f1 * 0.9,
                    height=bar_heights_f1[0],  # Same height as other bars
                    color=GRAY,
                    fill_opacity=0.0,
                    stroke_width=1.5,
                    stroke_opacity=0.6
                ).move_to([x_pos, f1_box.get_center()[1], 0])
                bars_f1.add(empty_bar)
        
        f1_label_text = MathTex(r"f_1", font_size=30, color=GREEN).next_to(f1_box, DOWN, buff=0.15)
        
        # Don't create label yet - will add all three labels at once later
        f1_full = VGroup(f1_box, bars_f1, f1_label_text)
        
        # Display f1
        self.play(Create(f1_box), Create(bars_f1), Write(f1_label_text))
        self.wait(2)
        
        # Create arrow from f1 to t1
        arrow_f1_to_t1 = Arrow(
            f1_label_text.get_bottom(),
            f1_box.get_bottom() + DOWN * 1.5,
            color=WHITE,
            buff=0.1
        )
        self.play(Create(arrow_f1_to_t1))
        self.wait(1)
        
        # Create t1 box below f1 (smaller, hashed version)
        t1_box = Rectangle(width=spectrum_width * 0.67, height=0.7, color=RED, fill_opacity=0.0, stroke_width=2)
        t1_box.next_to(arrow_f1_to_t1, DOWN, buff=0.2)
        
        # Display the empty t1 box first
        self.play(Create(t1_box))
        self.wait(0.5)
        
        # Use t1 positions and heights from pre-defined arrays
        t1_positions_data = t1_positions
        t1_heights_data = t1_heights
        colors_for_t1 = f1_colors
        
        min_pos_t1 = min(t1_positions_data)
        max_pos_t1 = max(t1_positions_data)
        num_total_bars_t1 = max_pos_t1 - min_pos_t1 + 1
        bar_width_t1 = (t1_box.width - 0.2) / num_total_bars_t1
        
        # First, create the empty bars in t1 (all positions)
        empty_bars_t1 = VGroup()
        for j in range(min_pos_t1, max_pos_t1 + 1):
            x_pos = t1_box.get_left()[0] + 0.1 + (j - min_pos_t1) * bar_width_t1 + bar_width_t1/2
            empty_bar = Rectangle(
                width=bar_width_t1 * 0.9,
                height=t1_heights_data[0],  # Same height as other bars
                color=GRAY,
                fill_opacity=0.0,
                stroke_width=1.5,
                stroke_opacity=0.6
            ).move_to([x_pos, t1_box.get_center()[1], 0])
            empty_bars_t1.add(empty_bar)
        
        # Show the empty bar outlines
        self.play(Create(empty_bars_t1))
        self.wait(0.5)
        
        # Now animate the colored bars floating from f1 to t1
        # We need to match the colored bars from f1 to their positions in t1
        floating_bars = []
        target_bars = []
        
        # Track which bars in bars_f1 are colored (based on positions)
        colored_bar_counter = 0
        for j in range(min_pos_f1, max_pos_f1 + 1):
            if j in colored_positions_f1:
                # This is a colored bar - find it in bars_f1
                bar_idx_in_group = j - min_pos_f1
                bar_f1 = bars_f1[bar_idx_in_group]
                
                # Create a copy of the bar from f1
                bar_copy = bar_f1.copy()
                floating_bars.append(bar_copy)
                
                # Calculate the target position in t1
                # colored_bar_counter corresponds to the index in the color arrays
                target_pos_idx = t1_positions_data[colored_bar_counter]
                target_x = t1_box.get_left()[0] + 0.1 + (target_pos_idx - min_pos_t1) * bar_width_t1 + bar_width_t1/2
                
                # Create the target bar at the t1 position
                target_bar = Rectangle(
                    width=bar_width_t1 * 0.9,
                    height=t1_heights_data[colored_bar_counter],
                    color=colors_for_t1[colored_bar_counter],
                    fill_opacity=0.8,
                    stroke_width=1
                ).move_to([target_x, t1_box.get_center()[1], 0])
                target_bars.append(target_bar)
                
                colored_bar_counter += 1
        
        # Add all floating bars to the scene at once
        self.add(*floating_bars)
        
        # Animate all bars moving to their target positions simultaneously using ReplacementTransform
        # This way the target_bars become the actual objects in the scene
        animations = [ReplacementTransform(floating_bars[i], target_bars[i]) for i in range(len(floating_bars))]
        self.play(*animations, run_time=2)
        self.wait(1)
        
        # Collect all bars for t1 (now using the actual target_bars that are in the scene)
        bars_t1 = VGroup(*target_bars, empty_bars_t1)
        
        t1_label_text = MathTex(r"t_1", font_size=30, color=RED).next_to(t1_box, DOWN, buff=0.15)
        
        # Don't create label yet - will add all three labels at once later
        t1_full = VGroup(t1_box, bars_t1, t1_label_text)
        
        # Display t1 label
        self.play(Write(t1_label_text))
        self.wait(3)
        
        # Now add all three labels at once on the right
        spectrum_label = Text("Original Spectrum", font_size=24, color=BLUE).next_to(spectrum_group, RIGHT, buff=0.5)
        binned_label = Text("Binned Spectrum", font_size=24, color=BLUE).next_to(f1_box, RIGHT, buff=0.5)
        hashed_label = Text("Hashed Spectrum", font_size=24, color=BLUE).next_to(t1_box, RIGHT, buff=0.5)
        
        self.play(Write(spectrum_label), Write(binned_label), Write(hashed_label))
        self.wait(2)
        
        # Update groups to include labels (but keep spectrum_label separate since it will fade with spectrum_group)
        f1_full.add(binned_label)
        t1_full.add(hashed_label)
        
        
        # ========== SECTION 2: Similarity preservation ==========

        understanding_title = Text("Understanding Similarity Preservation", font_size=32, color=YELLOW).to_edge(UP, buff=0.5)
        
        # First fade out the original spectrum, its label, and arrow, then minimize binned/hashed, then show title
        self.play(FadeOut(spectrum_group), FadeOut(spectrum_label), FadeOut(arrow_to_f1))
        
        # Make f1 and t1 smaller and move them closer to the bottom
        combined_group = VGroup(f1_full, arrow_f1_to_t1, t1_full)
        self.play(
            combined_group.animate.scale(0.6).to_edge(DOWN, buff=0.5)
        )
        
        self.play(Write(understanding_title))
        self.wait(1)
        
        # Create explanation texts using VGroup and arrange
        explanation_texts = VGroup(
            Text("We have the unhashed, binned feature vectors, and the hashed, compressed vectors.", font_size=22),
            Text("How do we know that the hashing worked correctly?", font_size=22),
            Text("We need to prove that similar vectors in the original space remain similar in the hashed space.", font_size=22),
            Text("Alternatively, dissimilar vectors in the original space remain dissimilar in the hashed space.", font_size=22),
            Text("Let's illustrate this with a simple example.", font_size=22)
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT).next_to(understanding_title, DOWN, buff=0.5)
        
        # Display each explanation text sequentially
        for text in explanation_texts:
            self.play(Write(text))
            self.wait(2)
        
        # Wait a moment before proceeding
        self.wait(1)
        
        # Fade out all explanation texts and understanding_title
        self.play(FadeOut(explanation_texts), FadeOut(understanding_title))
        
        # Fade out the minimized binned/hashed group too
        self.play(FadeOut(combined_group))
        
        #       Animation Flow:
        # 1. Initial Box Display with Highlights
        # Shows f and t boxes with labels
        # Highlights f1/f4 and t1/t4 pairs
        # Shows curved arrows indicating relationships
        # Explains the concept with text
        # 2. Complete Fade Out → Dissimilarity Numerical Example
        # Everything fades out (boxes, labels, highlights, arrows, text)
        # Clean screen shows:
        # Title: "Example: Dissimilarity Preservation"
        # f1 and f4 numerical values
        # Explanation text
        # t1 and t4 numerical values
        # Explanation about preservation
        # All fade out
        # 3. Boxes Come Back
        # Bring back the f and t boxes with labels
        # Show highlights on f1/f2 and t1/t2
        # Show similarity arrows
        # 4. Complete Fade Out → Similarity Numerical Example
        # Everything fades out again
        # Clean screen shows:
        # Title: "Example: Similarity Preservation"
        # f1 and f2 numerical values
        # Explanation text
        # t1 and t2 numerical values
        # Explanation about preservation
        # All fade out

        
        spectrum_heights = [f1_heights, f2_heights, f3_heights, f4_heights]
        
        f_group = VGroup()
        for i, label in enumerate([r"f_1", "f_2", "f_3", "f_4"]):
            # Larger box for non-hashed vectors (slightly smaller width)
            box = Rectangle(width=3.0, height=0.7, color=GREEN, fill_opacity=0.0, stroke_width=2)
            
            # Get the color order, positions, and heights for this spectrum
            colors_for_this_spectrum = spectrum_color_orders[i]
            colored_positions = spectrum_positions[i]
            bar_heights = spectrum_heights[i]
            
            # Total positions span from first to last colored bar
            min_pos = min(colored_positions)
            max_pos = max(colored_positions)
            num_total_bars = max_pos - min_pos + 1
            bar_width = (box.width - 0.2) / num_total_bars
            
            bars = VGroup()
            for j in range(min_pos, max_pos + 1):
                x_pos = box.get_left()[0] + 0.1 + (j - min_pos) * bar_width + bar_width/2
                
                if j in colored_positions:
                    # Colored bar with uniform height
                    bar_idx = colored_positions.index(j)
                    bar = Rectangle(
                        width=bar_width * 0.9,
                        height=bar_heights[bar_idx],
                        color=colors_for_this_spectrum[bar_idx],
                        fill_opacity=0.8,
                        stroke_width=0
                    ).move_to([x_pos, box.get_center()[1], 0])
                    bars.add(bar)
                else:
                    # Empty/whitespace bar - now clearly visible
                    empty_bar = Rectangle(
                        width=bar_width * 0.9,
                        height=bar_heights[0],  # Same height as other bars
                        color=GRAY,
                        fill_opacity=0.0,
                        stroke_width=1.5,
                        stroke_opacity=0.6
                    ).move_to([x_pos, box.get_center()[1], 0])
                    bars.add(empty_bar)
            
            text = MathTex(label, font_size=30, color=GREEN).next_to(box, DOWN, buff=0.15)
            f_group.add(VGroup(box, bars, text))
        f_group.arrange(RIGHT, buff=0.3).to_edge(UP, buff=1.0)
        
        t_group = VGroup()
        for i, label in enumerate(["t_1", "t_2", "t_3", "t_4"]):
            # Smaller box for hashed vectors
            box = Rectangle(width=2.0, height=0.7, color=RED, fill_opacity=0.0, stroke_width=2)
            
            # Use the same color order as the corresponding f_box
            colors_for_this_spectrum = spectrum_color_orders[i]
            
            # Get positions and heights from pre-defined arrays
            colored_positions = t_spectrum_positions[i]
            bar_heights = t_spectrum_heights[i]
            
            # Total positions span from first to last colored bar
            min_pos = min(colored_positions)
            max_pos = max(colored_positions)
            num_total_bars = max_pos - min_pos + 1
            bar_width = (box.width - 0.2) / num_total_bars
            
            bars = VGroup()
            for j in range(min_pos, max_pos + 1):
                x_pos = box.get_left()[0] + 0.1 + (j - min_pos) * bar_width + bar_width/2
                
                if j in colored_positions:
                    # Same colored bars as in corresponding f_box with uniform height
                    bar_idx = colored_positions.index(j)
                    bar = Rectangle(
                        width=bar_width * 0.9,
                        height=bar_heights[bar_idx],
                        color=colors_for_this_spectrum[bar_idx],
                        fill_opacity=0.8,
                        stroke_width=0
                    ).move_to([x_pos, box.get_center()[1], 0])
                    bars.add(bar)
                else:
                    # Empty/whitespace bar - now clearly visible
                    empty_bar = Rectangle(
                        width=bar_width * 0.9,
                        height=bar_heights[0],  # Same height as other bars
                        color=GRAY,
                        fill_opacity=0.0,
                        stroke_width=1.5,
                        stroke_opacity=0.6
                    ).move_to([x_pos, box.get_center()[1], 0])
                    bars.add(empty_bar)
            
            text = MathTex(label, font_size=30, color=RED).next_to(box, DOWN, buff=0.15)
            t_group.add(VGroup(box, bars, text))
        t_group.arrange(RIGHT, buff=0.4).next_to(f_group, DOWN, buff=1.5)
        
        # Labels for the groups
        f_label = Text("Non-hashed Vectors (original)", font_size=24, color=GREEN).next_to(f_group, UP, buff=0.3)
        t_label = Text("Hashed Vectors (compressed)", font_size=24, color=RED).next_to(t_group, DOWN, buff=0.3)
        # above and below the groups.
        
        # Transform f1_full and t1_full into their positions in f_group and t_group
        self.play(
            ReplacementTransform(f1_full, f_group[0]),
            ReplacementTransform(t1_full, t_group[0])
        )
        self.wait(1)
        
        # Now display the rest of the vectors and labels
        self.play(Write(f_label), Create(f_group[1:]))
        self.play(Write(t_label), Create(t_group[1:]))
        
        # Highlight boxes 1 and 2 in each set (for similarity example)
        highlight_box_f1_sim = SurroundingRectangle(f_group[0], color=YELLOW, buff=0.1)
        highlight_box_f2_sim = SurroundingRectangle(f_group[1], color=YELLOW, buff=0.1)
        highlight_box_t1_sim = SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1)
        highlight_box_t2_sim = SurroundingRectangle(t_group[1], color=YELLOW, buff=0.1)
        
        self.play(
            Create(highlight_box_f1_sim),
            Create(highlight_box_f2_sim),
            Create(highlight_box_t1_sim),
            Create(highlight_box_t2_sim)
        )
        
        # Create similarity arrows between highlighted pairs (from bounding boxes)
        arrow_f_sim = CurvedArrow(
            highlight_box_f1_sim.get_bottom(), 
            highlight_box_f2_sim.get_bottom(), 
            color=YELLOW, 
            angle=0.3
        )
        sim_f = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_f_sim, DOWN, buff=0.1)
        
        arrow_t_sim = CurvedArrow(
            highlight_box_t1_sim.get_top(), 
            highlight_box_t2_sim.get_top(), 
            color=YELLOW, 
            angle=-0.3
        )

        self.play(Create(arrow_f_sim))
        self.play(Create(arrow_t_sim))
        self.play(Write(sim_f))
        self.wait(2)
        
        # Explanation text
        explanation = VGroup(
            Text("• If these two vectors are similar in the original space...", font_size=22),
            Text("• Then they should remain similarly similar in the hashed space", font_size=22),
            Text("• This pattern should hold for ALL pairs of vectors", font_size=22),
            Text("• If this is true, our hashing preserves similarity relationships", font_size=22)
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        
        explanation.next_to(t_label, DOWN, buff=0.5)
        self.play(Write(explanation[0]))
        for i in range(1, len(explanation)):
            self.play(Write(explanation[i]))
            self.wait(1)
        
        # Simplify even more
        conclusion = Text(
            "In other words: If similar items remain similar after hashing,\n"
            "then our compression method works correctly!",
            font_size=28,
            color=YELLOW
        ).move_to(explanation.get_center())
        
        self.play(FadeOut(explanation), run_time=0.8)
        self.play(Write(conclusion))
        self.wait(3)
        
        # Fade out EVERYTHING to show similarity numerical example
        self.play(
            FadeOut(f_label), FadeOut(t_label),
            FadeOut(f_group), FadeOut(t_group),
            FadeOut(highlight_box_t1_sim), 
            FadeOut(highlight_box_t2_sim),
            FadeOut(highlight_box_f1_sim),
            FadeOut(highlight_box_f2_sim),
            FadeOut(arrow_f_sim),
            FadeOut(arrow_t_sim),
            FadeOut(sim_f),
            FadeOut(conclusion)
        )
        
        # Fade out EVERYTHING to show dissimilarity numerical example
        # self.play(
        #     FadeOut(f_label), FadeOut(t_label),
        #     FadeOut(f_group), FadeOut(t_group),
        #     FadeOut(highlight_box_t1), 
        #     FadeOut(highlight_box_t4),
        #     FadeOut(highlight_box_f1),
        #     FadeOut(highlight_box_f4),
        #     FadeOut(arrow_f),
        #     FadeOut(arrow_t),
        #     FadeOut(sim_f),
        #     FadeOut(conclusion)
        # )
        
        # ========== SIMILARITY NUMERICAL EXAMPLE ==========
        sim_title = Text("Example: Similarity Preservation", font_size=28, color=YELLOW).to_edge(UP, buff=0.5)
        self.play(Write(sim_title))
        self.wait(1)
        
        # Show numerical values for f1 and f2 to demonstrate similarity
        f1_similar = np.array([0,0,0,1,1,1,0,0])
        f2_similar = np.array([0,0,1,1,1,1,0,0])  # Very close to f1, just one bit different
        
        # Create visual representation of the vectors with their values (larger and bolded)
        f1_sim_visual = MathTex(r"\mathbf{f_1 = " + str(f1_similar).replace('\n', '') + "}", font_size=36, color=GREEN).shift(UP * 2)
        f2_sim_visual = MathTex(r"\mathbf{f_2 = " + str(f2_similar).replace('\n', '') + "}", font_size=36, color=GREEN).next_to(f1_sim_visual, DOWN, buff=0.5)
        
        self.play(Write(f1_sim_visual))
        self.play(Write(f2_sim_visual))
        self.wait(1)
        
        # Add explanation text
        similar_text = Text("These vectors are very similar - only one position differs!", 
                           font_size=24, color=WHITE).next_to(f2_sim_visual, DOWN, buff=0.8)
        self.play(Write(similar_text))
        self.wait(2)
        
        # Show the hashed vector values (simplified representation)
        t1_similar = np.array([0,1,0,1])  # Simplified 4-dimensional representation
        t2_similar = np.array([0,1,1,1])  # Also similar pattern preserved

        t1_sim_visual = MathTex(r"\mathbf{t_1 = " + str(t1_similar).replace('\n', '') + "}", font_size=36, color=RED).next_to(similar_text, DOWN, buff=0.8)
        t2_sim_visual = MathTex(r"\mathbf{t_2 = " + str(t2_similar).replace('\n', '') + "}", font_size=36, color=RED).next_to(t1_sim_visual, DOWN, buff=0.5)

        self.play(Write(t1_sim_visual))
        self.play(Write(t2_sim_visual))
        self.wait(1)
        
        # Explanation about hashed space similarity
        similar_text2 = Text("And in the hashed space, they remain similar - the relationship is preserved!", 
                            font_size=24, color=WHITE).next_to(t2_sim_visual, DOWN, buff=0.8)
        self.play(Write(similar_text2))
        self.wait(2)
        
        # Add a brief explanation about preservation
        preservation_text = Text("This similarity preservation is exactly what we want from good hashing!", 
                               font_size=24, color=YELLOW).next_to(t2_sim_visual, DOWN, buff=0.8)
        self.play(ReplacementTransform(similar_text2, preservation_text))
        self.wait(3)
        
        # Fade out all similarity numerical examples
        self.play(
            FadeOut(sim_title),
            FadeOut(f1_sim_visual), FadeOut(f2_sim_visual),
            FadeOut(t1_sim_visual), FadeOut(t2_sim_visual),
            FadeOut(similar_text),
            FadeOut(preservation_text)
        )
        self.wait(1)
        
                
        # ========== BRING BACK THE BOXES ==========
        # Re-display the boxes and labels
        self.play(Write(f_label), Create(f_group))
        self.play(Write(t_label), Create(t_group))
        self.wait(1)
        
        # ========== DISSIMILARITY NUMERICAL EXAMPLE ==========
        # Transition to dissimilarity example
        transition_text = Text("Now let's examine a pair that should be dissimilar...", 
                              font_size=24, color=YELLOW).next_to(t_label, DOWN, buff=0.5)
        self.play(Write(transition_text))
        self.wait(1)
        
        # Highlight f1, f4, t1, t4 boxes
        highlight_box_f1_dissim = SurroundingRectangle(f_group[0], color=YELLOW, buff=0.1)
        highlight_box_f4_dissim = SurroundingRectangle(f_group[3], color=YELLOW, buff=0.1)
        highlight_box_t1_dissim = SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1)
        highlight_box_t4_dissim = SurroundingRectangle(t_group[3], color=YELLOW, buff=0.1)
        
        self.play(
            Create(highlight_box_f1_dissim), Create(highlight_box_f4_dissim),
            Create(highlight_box_t1_dissim), Create(highlight_box_t4_dissim)
        )
        
        # Create arrows showing dissimilarity within each space (from bounding boxes)
        arrow_f_dissim = CurvedArrow(
            highlight_box_f1_dissim.get_bottom(), 
            highlight_box_f4_dissim.get_bottom(), 
            color=YELLOW, 
            angle=0.3
        )
        arrow_t_dissim = CurvedArrow(
            highlight_box_t1_dissim.get_top(), 
            highlight_box_t4_dissim.get_top(), 
            color=YELLOW, 
            angle=-0.3
        )
        
        dissim_f_text = Text("dissimilarity", font_size=20, color=YELLOW).next_to(arrow_f_dissim, DOWN, buff=0.1)
        
        self.play(Create(arrow_f_dissim), Create(arrow_t_dissim))
        self.play(Write(dissim_f_text))
        self.wait(2)
        
        # Fade EVERYTHING out for numerical example
        self.play(
            FadeOut(transition_text),
            FadeOut(f_label), FadeOut(t_label),
            FadeOut(f_group), FadeOut(t_group),
            FadeOut(highlight_box_f1_dissim), FadeOut(highlight_box_f4_dissim),
            FadeOut(highlight_box_t1_dissim), FadeOut(highlight_box_t4_dissim),
            FadeOut(arrow_f_dissim), FadeOut(arrow_t_dissim),
            FadeOut(dissim_f_text)
        )
        self.wait(1)
        
        # Show clean numerical example for dissimilarity
        dissim_title = Text("Example: DIS-similarity Preservation", font_size=28, color=YELLOW).to_edge(UP, buff=0.5)
        self.play(Write(dissim_title))
        self.wait(1)
        
        # Show numerical values for f1 and f4 to demonstrate dissimilarity
        f1_values = np.array([0,0,0,1,1,1,0,0])
        f4_values = np.array([1,1,1,0,0,0,1,1])
        
        # Create visual representation showing dissimilarity in both spaces (larger and bolded)
        f1_dissim_visual = MathTex(r"\mathbf{f_1 = " + str(f1_values).replace('\n', '') + "}", font_size=36, color=GREEN).shift(UP * 2)
        f4_dissim_visual = MathTex(r"\mathbf{f_4 = " + str(f4_values).replace('\n', '') + "}", font_size=36, color=GREEN).next_to(f1_dissim_visual, DOWN, buff=0.5)
        
        self.play(Write(f1_dissim_visual))
        self.play(Write(f4_dissim_visual))
        self.wait(1)
        
        # Add explanation for dissimilarity
        dissimilar_text = Text("These two vectors are exact opposites of each other!", 
                              font_size=24, color=WHITE).next_to(f4_dissim_visual, DOWN, buff=0.8)
        self.play(Write(dissimilar_text))
        self.wait(2)
        
        # Show the hashed vector values (simplified representation)
        t1_values = np.array([0,1,0,1])  # Simplified 4-dimensional representation
        t4_values = np.array([1,0,1,0])  # Opposite pattern preserved
        
        t1_dissim_visual = MathTex(r"\mathbf{t_1 = " + str(t1_values).replace('\n', '') + "}", font_size=36, color=RED).next_to(dissimilar_text, DOWN, buff=0.8)
        t4_dissim_visual = MathTex(r"\mathbf{t_4 = " + str(t4_values).replace('\n', '') + "}", font_size=36, color=RED).next_to(t1_dissim_visual, DOWN, buff=0.5)
        
        self.play(Write(t1_dissim_visual))
        self.play(Write(t4_dissim_visual))
        self.wait(1)
        
        hashed_dissimilar_text = Text("In the hashed space, they remain dissimilar - the opposition is preserved!", 
                                     font_size=24, color=WHITE).next_to(t4_dissim_visual, DOWN, buff=0.8)
        self.play(Write(hashed_dissimilar_text))
        self.wait(2)
        
        # Final insight about the preservation principle
        preservation_insight = Text("This is the key: dissimilarity relationships are also maintained across both spaces!", 
                                font_size=24, color=YELLOW).next_to(t4_dissim_visual, DOWN, buff=0.8)
        self.play(ReplacementTransform(hashed_dissimilar_text, preservation_insight))
        self.wait(3)
        
        # Clean up the dissimilarity numerical example
        self.play(
            FadeOut(dissim_title),
            FadeOut(f1_dissim_visual), FadeOut(f4_dissim_visual),
            FadeOut(t1_dissim_visual), FadeOut(t4_dissim_visual),
            FadeOut(dissimilar_text),
            FadeOut(preservation_insight)
        )
        self.wait(1)
        
        
# High-quality rendering configuration
if __name__ == "__main__":
    # To render this scene in high quality, run:
    # manim -pqh mergedVideos.py SimilarityPreservationComplete
    pass