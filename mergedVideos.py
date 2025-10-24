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
        # ========== SECTION 1: Title and Introduction ==========
        title = make_title(self, "Similarity Preservation in Spectral Hashing")
        self.play(FadeOut(title))
        pec_title = Text("Let's go over what we've already accomplished!", font_size=28).move_to(title.get_center())
        self.play(Write(pec_title))
        self.play(FadeOut(pec_title))
        spec_title = Text("Step 1: Original Spectra", font_size=28).move_to(title.get_center())
        self.play(Write(spec_title))
        
        spec_motivation = Text("Using 4 spectra, we'll show that", font_size=20).move_to(title.get_center())
        spec_motivation2 = Text("they can be proven to be similar in both their hashed and nonhashed versions.", font_size=20).next_to(spec_motivation, DOWN, buff=0.5)
        # self.play(Transform(spec_title, spec_motivation))
        self.play(FadeOut(spec_title))
        self.play(Write(spec_motivation))
        self.play(Write(spec_motivation2))
        self.wait(2)
        spectra_group = VGroup()
        for i, label in enumerate(["s_1", "s_2", "s_3", "s_4"]):
            box = Rectangle(width=1.5, height=0.8, color=BLUE)
            txt = MathTex(label, font_size=30)
            spectra_group.add(VGroup(box, txt).arrange(DOWN, buff=0.1))

        spectra_group.arrange(RIGHT, buff=0.5).shift(DOWN * 0.5)
        self.play(Create(spectra_group))
        self.wait(2)
        self.play(FadeOut(spec_motivation, spectra_group,spec_motivation2))
        
        # ========== SECTION 2: Feature Vectors ==========
        step2_title = Text("Step 2: Non-hashed Feature Vectors", font_size=28).move_to(title.get_center())
        self.play(Write(step2_title))
        non_hashed_group = VGroup()
        for i, label in enumerate(["f_1", "f_2", "f_3", "f_4"]):
            box = Rectangle(width=3, height=0.8, color=GREEN)
            lbl = MathTex(label, font_size=28)
            dim = Text("(8800-dim)", font_size=22, color=GRAY)
            non_hashed_group.add(VGroup(box, lbl, dim).arrange(DOWN, buff=0.05))

        non_hashed_group.arrange(RIGHT, buff=0.3).shift(UP * 0.5)
        self.play(Create(non_hashed_group))
        self.wait(1)
        self.play(FadeOut(step2_title))
        
        step3_title = Text("Step 3: Hashed Feature Vectors", font_size=28).move_to(title.get_center())
        self.play(Write(step3_title))

        hashed_group = VGroup()
        for i, label in enumerate(["t_1", "t_2", "t_3", "t_4"]):
            box = Rectangle(width=1.5, height=0.8, color=RED)
            lbl = MathTex(label, font_size=28)
            dim = Text("(400-dim)", font_size=22, color=GRAY)
            hashed_group.add(VGroup(box, lbl, dim).arrange(DOWN, buff=0.05))
        hashed_group.arrange(RIGHT, buff=0.3).shift(DOWN * 1.5)
        
        arrows = VGroup()
        for i in range(4):
            arrow = Arrow(
            non_hashed_group[i].get_bottom(),
            hashed_group[i].get_top(),
            color=YELLOW,
            stroke_width=2
            )
            arrows.add(arrow)

        self.play(Create(arrows))
        self.play(Create(hashed_group))
        unhashed_text = Text("Non-hashed Vectors", font_size=24).next_to(non_hashed_group, UP * 0.5, buff=0.5)
        hashed_text = Text("Hashed Vectors", font_size=24).next_to(hashed_group, DOWN * 0.5, buff=0.5)
        self.play(Write(hashed_text), Transform(step3_title, unhashed_text))
        self.wait(3)
        
        # Clear the screen for next section
        self.play(FadeOut(step3_title, unhashed_text, hashed_text, non_hashed_group, hashed_group, arrows))
        
        # ========== SECTION 3: Similarity Explanation ==========
        understanding_title = Text("Understanding Similarity Preservation", font_size=32, color=YELLOW).move_to(title.get_center())
        self.play(Write(understanding_title))
        self.wait(1)
        self.play(FadeOut(understanding_title))
        
        # Create a group to hold all explanation texts
        explanation_texts = []
        
        # First explanation text at the top
        expl1 = Text("We have the unhashed, binned feature vectors, and the hashed, compressed vectors.", font_size=22).to_edge(UP, buff=0.5)
        self.play(Write(expl1))
        explanation_texts.append(expl1)
        self.wait(2)
        # Second explanation text below the first
        expl2 = Text("How do we know that the hashing worked correctly?", font_size=22).next_to(expl1, DOWN, buff=0.3)
        self.play(Write(expl2))
        explanation_texts.append(expl2)
        self.wait(2)
        # Third explanation text below the second
        expl3 = Text("We need to prove that similar vectors in the original space remain similar in the hashed space.", font_size=22).next_to(expl2, DOWN, buff=0.3)
        self.play(Write(expl3))
        explanation_texts.append(expl3)
        self.wait(2)        
        # Fourth explanation text below the third
        expl4 = Text("Alternatively, dissimilar vectors in the original space remain dissimilar in the hashed space.", font_size=22).next_to(expl3, DOWN, buff=0.3)
        self.play(Write(expl4))
        explanation_texts.append(expl4)
        self.wait(2)
        # Fifth explanation text below the fourth
        expl5 = Text("Let's illustrate this with a simple example.", font_size=22).next_to(expl4, DOWN, buff=0.3)
        self.play(Write(expl5))
        explanation_texts.append(expl5)
        
        # Wait a moment before proceeding
        self.wait(3)
        
        # Fade out all explanation texts at once
        self.play(*[FadeOut(text) for text in explanation_texts])
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

        # Create the two sets of vectors (simplified representations)
        # Define colors for the bins (matching the image style)
        bin_colors = [BLUE, ORANGE, GREEN, RED, PURPLE, PINK, YELLOW, TEAL]
        
        # Create specific color orderings and positions for each spectrum
        # f1 and f2 should be very similar (same colors, similar positions)
        # f4 should be radically different from f1 (different colors, different positions)
        
        # Define colors for each spectrum
        f1_colors = [BLUE, ORANGE, GREEN, RED, PURPLE, PINK, YELLOW, TEAL]
        f2_colors = [BLUE, ORANGE, GREEN, RED, PURPLE, PINK, YELLOW, TEAL]  # Same as f1 (similar)
        f3_colors = [PINK, TEAL, ORANGE, BLUE, YELLOW, GREEN, RED, PURPLE]  # Different ordering
        f4_colors = [YELLOW, PINK, PURPLE, TEAL, RED, ORANGE, BLUE, GREEN]  # Radically different from f1
        
        spectrum_color_orders = [f1_colors, f2_colors, f3_colors, f4_colors]
        
        # Define positions for each spectrum
        # f1: positions with some gaps
        f1_positions = [0, 2, 4, 7, 9, 11, 14, 16]
        # f2: very similar to f1 (only slightly shifted, mostly same)
        f2_positions = [0, 2, 4, 7, 9, 12, 14, 16]  # Only position 11->12 changed
        # f3: different pattern
        f3_positions = [1, 3, 5, 8, 10, 12, 15, 17]
        # f4: radically different positions from f1
        f4_positions = [1, 3, 6, 8, 10, 13, 15, 18]
        
        spectrum_positions = [f1_positions, f2_positions, f3_positions, f4_positions]
        
        # Define bar heights for each spectrum
        # f1 and f2 should have very similar heights
        f1_heights = [0.5, 0.3, 0.55, 0.4, 0.45, 0.35, 0.5, 0.4]
        f2_heights = [0.5, 0.32, 0.53, 0.4, 0.45, 0.36, 0.5, 0.42]  # Very similar to f1
        f3_heights = [0.4, 0.5, 0.3, 0.45, 0.35, 0.5, 0.4, 0.55]
        f4_heights = [0.35, 0.45, 0.4, 0.5, 0.3, 0.55, 0.38, 0.48]  # Different from f1
        
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
                    # Colored bar with varying height
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
                    # Empty/whitespace bar (very faint outline to show the grid structure)
                    empty_bar = Rectangle(
                        width=bar_width * 0.9,
                        height=0.5,
                        color=GRAY,
                        fill_opacity=0.0,
                        stroke_width=0.5,
                        stroke_opacity=0.1
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
            
            # Create dense colored bars inside with less whitespace between them
            # t1 and t2 should be similar (corresponding to f1 and f2)
            # t4 should be different (corresponding to f4)
            
            # Define positions for hashed versions (more compact)
            t1_positions = [0, 1, 3, 4, 6, 7, 9, 10]  # Compact version of f1
            t2_positions = [0, 1, 3, 4, 6, 7, 9, 10]  # Very similar to t1 (same positions)
            t3_positions = [0, 2, 3, 5, 6, 8, 9, 11]  # Different pattern
            t4_positions = [1, 2, 4, 5, 7, 8, 10, 11]  # Radically different from t1
            
            t_spectrum_positions = [t1_positions, t2_positions, t3_positions, t4_positions]
            
            # Heights for t-boxes (similar to corresponding f-boxes)
            t1_heights = [0.5, 0.3, 0.55, 0.4, 0.45, 0.35, 0.5, 0.4]
            t2_heights = [0.5, 0.32, 0.53, 0.4, 0.45, 0.36, 0.5, 0.42]  # Very similar to t1
            t3_heights = [0.4, 0.5, 0.3, 0.45, 0.35, 0.5, 0.4, 0.55]
            t4_heights = [0.35, 0.45, 0.4, 0.5, 0.3, 0.55, 0.38, 0.48]  # Different from t1
            
            t_spectrum_heights = [t1_heights, t2_heights, t3_heights, t4_heights]
            
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
                    # Same colored bars as in corresponding f_box
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
                    # Empty/whitespace bar (very faint outline to show the grid structure)
                    empty_bar = Rectangle(
                        width=bar_width * 0.9,
                        height=0.5,
                        color=GRAY,
                        fill_opacity=0.0,
                        stroke_width=0.5,
                        stroke_opacity=0.1
                    ).move_to([x_pos, box.get_center()[1], 0])
                    bars.add(empty_bar)
            
            text = MathTex(label, font_size=30, color=RED).next_to(box, DOWN, buff=0.15)
            t_group.add(VGroup(box, bars, text))
        t_group.arrange(RIGHT, buff=0.4).next_to(f_group, DOWN, buff=1.5)
        
        # Labels for the groups
        f_label = Text("Non-hashed Vectors (original)", font_size=24, color=GREEN).next_to(f_group, UP, buff=0.3)
        t_label = Text("Hashed Vectors (compressed)", font_size=24, color=RED).next_to(t_group, DOWN, buff=0.3)
        # above and below the groups.
        # Display the vectors and labels
        self.play(Write(f_label), Create(f_group))
        self.play(Write(t_label), Create(t_group))
        
        # Highlight boxes 1 and 4 in each set
        highlight_box_f1 = SurroundingRectangle(f_group[0], color=YELLOW, buff=0.1)
        highlight_box_f4 = SurroundingRectangle(f_group[3], color=YELLOW, buff=0.1)
        highlight_box_t1 = SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1)
        highlight_box_t4 = SurroundingRectangle(t_group[3], color=YELLOW, buff=0.1)
        
        self.play(
            Create(highlight_box_f1),
            Create(highlight_box_f4),
            Create(highlight_box_t1),
            Create(highlight_box_t4)
        )
        
        # Create similarity arrows between highlighted pairs
        arrow_f = CurvedArrow(
            f_group[0].get_bottom(), 
            f_group[3].get_bottom(), 
            color=YELLOW, 
            angle=0.3
        )
        sim_f = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_f, DOWN, buff=0.1)
        
        arrow_t = CurvedArrow(
            t_group[0].get_top(), 
            t_group[3].get_top(), 
            color=YELLOW, 
            angle=-0.3
        )

        self.play(Create(arrow_f))
        self.play(Create(arrow_t))
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
        
        # Fade out EVERYTHING to show dissimilarity numerical example
        self.play(
            FadeOut(f_label), FadeOut(t_label),
            FadeOut(f_group), FadeOut(t_group),
            FadeOut(highlight_box_t1), 
            FadeOut(highlight_box_t4),
            FadeOut(highlight_box_f1),
            FadeOut(highlight_box_f4),
            FadeOut(arrow_f),
            FadeOut(arrow_t),
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
        
        # ========== DISSIMILARITY NUMERICAL EXAMPLE ==========
        dissim_title = Text("Example: DIS-similarity Preservation", font_size=28, color=YELLOW).to_edge(UP, buff=0.5)
        self.play(Write(dissim_title))
        self.wait(1)
        
        # Show numerical values for f1 and f4 to demonstrate dissimilarity
        f1_values = np.array([0,0,0,1,1,1,0,0])
        f4_values = np.array([1,1,1,0,0,0,1,1])
        
        # Create visual representation of the vectors with their values
        f1_visual = MathTex(r"f_1 = " + str(f1_values).replace('\n', ''), font_size=28, color=GREEN).shift(UP * 2)
        f4_visual = MathTex(r"f_4 = " + str(f4_values).replace('\n', ''), font_size=28, color=GREEN).next_to(f1_visual, DOWN, buff=0.5)
        
        self.play(Write(f1_visual))
        self.play(Write(f4_visual))
        self.wait(1)
        
        # Add explanation text
        dissimilar_text = Text("These two vectors are exact opposites of each other!", 
                              font_size=24, color=WHITE).next_to(f4_visual, DOWN, buff=0.8)
        self.play(Write(dissimilar_text))
        self.wait(2)
        
        # Show the hashed vector values (simplified representation)
        t1_values = np.array([0,1,0,1])  # Simplified 4-dimensional representation
        t4_values = np.array([1,0,1,0])  # Opposite pattern preserved

        t1_visual = MathTex(r"t_1 = " + str(t1_values).replace('\n', ''), font_size=28, color=RED).next_to(dissimilar_text, DOWN, buff=0.8)
        t4_visual = MathTex(r"t_4 = " + str(t4_values).replace('\n', ''), font_size=28, color=RED).next_to(t1_visual, DOWN, buff=0.5)

        self.play(Write(t1_visual))
        self.play(Write(t4_visual))
        self.wait(1)
        
        # Explanation about hashed space dissimilarity
        hashed_dissimilar_text = Text("In the hashed space, they remain dissimilar - the opposition is preserved!", 
                                     font_size=24, color=WHITE).next_to(t4_visual, DOWN, buff=0.8)
        self.play(Write(hashed_dissimilar_text))
        self.wait(2)
        
        # Add a brief explanation about preservation
        preservation_text = Text("This dissimilarity preservation is exactly what we want from good hashing!", 
                               font_size=24, color=YELLOW).next_to(hashed_dissimilar_text, DOWN, buff=0.5)
        self.play(Write(preservation_text))
        self.wait(3)
        
        # Fade out all dissimilarity numerical examples
        self.play(
            FadeOut(dissim_title),
            FadeOut(f1_visual), FadeOut(f4_visual),
            FadeOut(t1_visual), FadeOut(t4_visual),
            FadeOut(dissimilar_text),
            FadeOut(hashed_dissimilar_text),
            FadeOut(preservation_text)
        )
        self.wait(1)
        
        # ========== BRING BACK THE BOXES ==========
        # Re-display the boxes and labels
        self.play(Write(f_label), Create(f_group))
        self.play(Write(t_label), Create(t_group))
        self.wait(1)
        
        # ========== SIMILARITY NUMERICAL EXAMPLE ==========
        # Transition to similarity example
        transition_text = Text("Now let's examine a pair that should be similar...", 
                              font_size=24, color=YELLOW).next_to(t_label, DOWN, buff=0.5)
        self.play(Write(transition_text))
        self.wait(1)
        
        # Highlight f1, f2, t1, t2 boxes
        highlight_box_f1_sim = SurroundingRectangle(f_group[0], color=YELLOW, buff=0.1)
        highlight_box_f2_sim = SurroundingRectangle(f_group[1], color=YELLOW, buff=0.1)
        highlight_box_t1_sim = SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1)
        highlight_box_t2_sim = SurroundingRectangle(t_group[1], color=YELLOW, buff=0.1)
        
        self.play(
            Create(highlight_box_f1_sim), Create(highlight_box_f2_sim),
            Create(highlight_box_t1_sim), Create(highlight_box_t2_sim)
        )
        
        # Create arrows showing similarity within each space
        arrow_f_sim = CurvedArrow(
            f_group[0].get_bottom(), 
            f_group[1].get_bottom(), 
            color=YELLOW, 
            angle=0.3
        )
        arrow_t_sim = CurvedArrow(
            t_group[0].get_top(), 
            t_group[1].get_top(), 
            color=YELLOW, 
            angle=-0.3
        )
        
        sim_f_text = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_f_sim, DOWN, buff=0.1)
        
        self.play(Create(arrow_f_sim), Create(arrow_t_sim))
        self.play(Write(sim_f_text))
        self.wait(2)
        
        # Fade EVERYTHING out for numerical example
        self.play(
            FadeOut(transition_text),
            FadeOut(f_label), FadeOut(t_label),
            FadeOut(f_group), FadeOut(t_group),
            FadeOut(highlight_box_f1_sim), FadeOut(highlight_box_f2_sim),
            FadeOut(highlight_box_t1_sim), FadeOut(highlight_box_t2_sim),
            FadeOut(arrow_f_sim), FadeOut(arrow_t_sim),
            FadeOut(sim_f_text)
        )
        self.wait(1)
        
        # Show clean numerical example for similarity
        sim_title = Text("Example: Similarity Preservation", font_size=28, color=YELLOW).to_edge(UP, buff=0.5)
        self.play(Write(sim_title))
        self.wait(1)
        
        # Show numerical values for f1 and f2 to demonstrate similarity
        f1_similar = np.array([0,0,0,1,1,1,0,0])
        f2_similar = np.array([0,0,1,1,1,1,0,0])  # Very close to f1, just one bit different
        
        # Show corresponding hashed values
        t1_similar = np.array([0,1,0,1])  # Simplified 4-dimensional representation
        t2_similar = np.array([0,1,1,1])  # Also similar pattern preserved
        
        # Create visual representation showing similarity in both spaces
        f1_sim_visual = MathTex(r"f_1 = " + str(f1_similar).replace('\n', ''), font_size=28, color=GREEN).shift(UP * 2)
        f2_sim_visual = MathTex(r"f_2 = " + str(f2_similar).replace('\n', ''), font_size=28, color=GREEN).next_to(f1_sim_visual, DOWN, buff=0.5)
        
        self.play(Write(f1_sim_visual))
        self.play(Write(f2_sim_visual))
        self.wait(1)
        
        # Add explanation for similarity
        similar_text = Text("These vectors are very similar - only one position differs!", 
                           font_size=24, color=WHITE).next_to(f2_sim_visual, DOWN, buff=0.8)
        self.play(Write(similar_text))
        self.wait(2)
        
        t1_sim_visual = MathTex(r"t_1 = " + str(t1_similar).replace('\n', ''), font_size=28, color=RED).next_to(similar_text, DOWN, buff=0.8)
        t2_sim_visual = MathTex(r"t_2 = " + str(t2_similar).replace('\n', ''), font_size=28, color=RED).next_to(t1_sim_visual, DOWN, buff=0.5)
        
        self.play(Write(t1_sim_visual))
        self.play(Write(t2_sim_visual))
        self.wait(1)
        
        similar_text2 = Text("And in the hashed space, they remain similar - the relationship is preserved!", 
                            font_size=24, color=WHITE).next_to(t2_sim_visual, DOWN, buff=0.8)
        self.play(Write(similar_text2))
        self.wait(2)
        
        # Final insight about the preservation principle
        preservation_insight = Text("This is the key: similarity relationships are maintained across both spaces!", 
                                   font_size=24, color=YELLOW).next_to(similar_text2, DOWN, buff=0.5)
        self.play(Write(preservation_insight))
        self.wait(3)
        
        # Clean up the similarity numerical example
        self.play(
            FadeOut(sim_title),
            FadeOut(f1_sim_visual), FadeOut(f2_sim_visual),
            FadeOut(t1_sim_visual), FadeOut(t2_sim_visual),
            FadeOut(similar_text), FadeOut(similar_text2),
            FadeOut(preservation_insight)
        )
        self.wait(1)
        
# High-quality rendering configuration
if __name__ == "__main__":
    # To render this scene in high quality, run:
    # manim -pqh mergedVideos.py SimilarityPreservationComplete
    pass