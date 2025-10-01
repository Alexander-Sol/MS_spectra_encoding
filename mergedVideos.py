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


def create_empty_matrix_with_subscript_labels(position, prefix, color):
    matrix_group = VGroup()
    if prefix == "f":
        prefix_color = GREEN
    else:
        prefix_color = RED
    # matrix cells
    matrix = VGroup()
    for i in range(4):
        row = VGroup()
        for j in range(4):
            is_diag = (i == j)
            
            cell = Rectangle(width=1.2, height=1.0, color=WHITE, fill_opacity=0.3, stroke_color=WHITE)
            if is_diag:
                text = MathTex(r"1", font_size=27, color=BLACK)
            else:
                text = MathTex(f"cs({prefix}_{{{i+1}}},{prefix}_{{{j+1}}})", font_size=27, color=prefix_color)
            row.add(VGroup(cell, text))
        row.arrange(RIGHT, buff=0.05)
        matrix.add(row)
    matrix.arrange(DOWN, buff=0.05)

    # row labels
    row_labels = VGroup(*[
        MathTex(f"{prefix}_{{{i+1}}}", font_size=26, color=color) for i in range(4)
    ])
    row_labels.arrange(DOWN, buff=0.8).next_to(matrix, LEFT, buff=0.5)

    # column labels
    col_labels = VGroup(*[
        MathTex(f"{prefix}_{{{i+1}}}", font_size=26, color=color) for i in range(4)
    ])
    col_labels.arrange(RIGHT, buff=1).next_to(matrix, UP, buff=0.5)

    matrix_group.add(matrix, row_labels, col_labels)
    matrix_group.move_to(position)
    return matrix_group

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
        
        # Create the two sets of vectors (simplified representations)
        f_group = VGroup()
        for i, label in enumerate([r"f_1", "f_2", "f_3", "f_4"]):
            box = Rectangle(width=2.0, height=0.7, color=GREEN, fill_opacity=0.2)
            text = MathTex(label, font_size=30, color=GREEN)
            f_group.add(VGroup(box, text).arrange(ORIGIN, buff=0))
        f_group.arrange(RIGHT, buff=0.5).to_edge(UP, buff=1.0)
        
        t_group = VGroup()
        for i, label in enumerate(["t_1", "t_2", "t_3", "t_4"]):
            box = Rectangle(width=2.0, height=0.7, color=RED, fill_opacity=0.2)
            text = MathTex(label, font_size=30, color=RED)
            t_group.add(VGroup(box, text).arrange(ORIGIN, buff=0))
        t_group.arrange(RIGHT, buff=0.5).next_to(f_group, DOWN, buff=1.5)
        
        # Labels for the groups
        f_label = Text("Non-hashed Vectors (original)", font_size=24, color=GREEN).next_to(f_group, UP, buff=0.3)
        t_label = Text("Hashed Vectors (compressed)", font_size=24, color=RED).next_to(t_group, UP, buff=0.3)
        
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
            angle=0.5
        )
        sim_f = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_f, DOWN, buff=0.1)
        
        arrow_t = CurvedArrow(
            t_group[0].get_bottom(), 
            t_group[3].get_bottom(), 
            color=YELLOW, 
            angle=0.5
        )
        sim_t = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_t, DOWN, buff=0.1)
        
        self.play(Create(arrow_f), Write(sim_f))
        self.play(Create(arrow_t), Write(sim_t))
        self.wait(0.5)
        
        # Explanation text
        explanation = VGroup(
            Text("• If these two vectors are similar in the original space...", font_size=22),
            Text("• Then they should remain similarly similar in the hashed space", font_size=22),
            Text("• This pattern should hold for ALL pairs of vectors", font_size=22),
            Text("• If this is true, our hashing preserves similarity relationships", font_size=22)
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        
        explanation.to_edge(DOWN, buff=1)
        
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
        
        self.play(
            FadeOut(t_group),
            FadeOut(t_label),
            FadeOut(highlight_box_t1), FadeOut(highlight_box_t4),
            FadeOut(arrow_t),
            FadeOut(sim_t),
            FadeOut(conclusion)
        )
        
        # Show numerical values for f1 and f4 to demonstrate dissimilarity
        f1_values = np.array([0,0,0,1,1,1,0,0])
        f4_values = np.array([1,1,1,0,0,0,1,1])
        
        # Create visual representation of the vectors with their values
        f1_visual = Text(f"f₁ = {f1_values}", font_size=24, color=GREEN).move_to(LEFT * 4 + UP * 1)
        f4_visual = Text(f"f₄ = {f4_values}", font_size=24, color=GREEN).move_to(LEFT * 4 + DOWN * 1)
        
        self.play(Write(f1_visual), Write(f4_visual))
        self.wait(1)
        
        # Add explanation text
        dissimilar_text = Text("As you can see, these two vectors are exact opposites of each other!", 
                              font_size=22, color=WHITE).to_edge(DOWN, buff=1)
        self.play(Write(dissimilar_text))
        self.wait(2)
        
        # Bring back hashed vectors to show the complete comparison
        self.play(Write(t_label), Create(t_group))
        
        # Highlight the corresponding hashed vectors (t1 and t4)
        highlight_box_t1_dissim = SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1)
        highlight_box_t4_dissim = SurroundingRectangle(t_group[3], color=YELLOW, buff=0.1)
        
        self.play(Create(highlight_box_t1_dissim), Create(highlight_box_t4_dissim))
        
        # Create dotted connection lines to show correspondence
        dotted_line1 = DashedLine(f_group[0].get_center(), t_group[0].get_center(), 
                                 color=YELLOW, stroke_width=2, dash_length=0.1)
        dotted_line4 = DashedLine(f_group[3].get_center(), t_group[3].get_center(), 
                                 color=YELLOW, stroke_width=2, dash_length=0.1)
        
        self.play(Create(dotted_line1), Create(dotted_line4))
        
        # Show the hashed vector values (simplified representation)
        t1_values = np.array([0,1,0,1])  # Simplified 4-dimensional representation
        t4_values = np.array([1,0,1,0])  # Opposite pattern preserved
        
        t1_visual = Text(f"t₁ = {t1_values}", font_size=24, color=RED).move_to(RIGHT * 4 + UP * 1)
        t4_visual = Text(f"t₄ = {t4_values}", font_size=24, color=RED).move_to(RIGHT * 4 + DOWN * 1)
        
        self.play(Write(t1_visual), Write(t4_visual))
        self.wait(1)
        
        # Transform the explanation to discuss hashed space dissimilarity
        hashed_dissimilar_text = Text("And in the hashed space, they remain dissimilar - the opposition is preserved!", 
                                     font_size=22, color=WHITE).to_edge(DOWN, buff=1)
        self.play(Transform(dissimilar_text, hashed_dissimilar_text))
        self.wait(2)
        
        # Add a brief explanation about preservation
        preservation_text = Text("This dissimilarity preservation is exactly what we want from good hashing!", 
                               font_size=20, color=YELLOW).next_to(hashed_dissimilar_text, UP, buff=0.3)
        self.play(Write(preservation_text))
        self.wait(2)
        
        # Clean up the dissimilarity demonstration
        self.play(FadeOut(f1_visual), FadeOut(f4_visual), FadeOut(t1_visual), FadeOut(t4_visual), 
                 FadeOut(dissimilar_text), FadeOut(preservation_text))
        
        # Now smoothly transition from dissimilar (f1/f4, t1/t4) to similar (f1/f2, t1/t2) pairs
        transition_text = Text("Now let's examine a pair that should be similar...", 
                              font_size=24, color=YELLOW).to_edge(DOWN, buff=1)
        self.play(Write(transition_text))
        self.wait(1)
        
        # Smoothly move the highlighting from f4 to f2 and t4 to t2
        highlight_box_f2 = SurroundingRectangle(f_group[1], color=YELLOW, buff=0.1)
        highlight_box_t2 = SurroundingRectangle(t_group[1], color=YELLOW, buff=0.1)
        
        # Transform the highlights from dissimilar to similar pairs
        self.play(
            Transform(highlight_box_f4, highlight_box_f2),
            Transform(highlight_box_t4_dissim, highlight_box_t2),
            run_time=1.5
        )
        
        # Update the dotted connection lines to connect f1-t1 and f2-t2
        new_dotted_line2 = DashedLine(f_group[1].get_center(), t_group[1].get_center(), 
                                     color=YELLOW, stroke_width=2, dash_length=0.1)
        
        self.play(Transform(dotted_line4, new_dotted_line2), run_time=1.5)
        
        # Create new arrows showing similarity within each space
        arrow_f_new = CurvedArrow(
            f_group[0].get_bottom(), 
            f_group[1].get_bottom(), 
            color=YELLOW, 
            angle=0.3
        )
        arrow_t_new = CurvedArrow(
            t_group[0].get_bottom(), 
            t_group[1].get_bottom(), 
            color=YELLOW, 
            angle=0.3
        )
        
        sim_f_new = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_f_new, DOWN, buff=0.1)
        sim_t_new = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_t_new, DOWN, buff=0.1)
        
        self.play(Create(arrow_f_new), Create(arrow_t_new))
        self.play(Write(sim_f_new), Write(sim_t_new))
        
        self.play(Transform(transition_text, 
                           Text("Perfect! Now we're comparing similar pairs in both spaces", 
                               font_size=22, color=WHITE).to_edge(DOWN, buff=1)))
        self.wait(2)
        
        # Show numerical values for f1 and f2 to demonstrate similarity
        f1_similar = np.array([0,0,0,1,1,1,0,0])
        f2_similar = np.array([0,0,1,1,1,1,0,0])  # Very close to f1, just one bit different
        
        # Show corresponding hashed values
        t1_similar = np.array([0,1,0,1])  # Simplified 4-dimensional representation
        t2_similar = np.array([0,1,1,1])  # Also similar pattern preserved
        
        # Create visual representation showing similarity in both spaces
        f1_sim_visual = Text(f"f₁ = {f1_similar}", font_size=24, color=GREEN).move_to(LEFT * 4 + UP * 1.5)
        f2_sim_visual = Text(f"f₂ = {f2_similar}", font_size=24, color=GREEN).move_to(LEFT * 4 + UP * 0.5)
        
        t1_sim_visual = Text(f"t₁ = {t1_similar}", font_size=24, color=RED).move_to(RIGHT * 4 + UP * 1.5)
        t2_sim_visual = Text(f"t₂ = {t2_similar}", font_size=24, color=RED).move_to(RIGHT * 4 + UP * 0.5)
        
        self.play(Write(f1_sim_visual), Write(f2_sim_visual))
        self.play(Write(t1_sim_visual), Write(t2_sim_visual))
        self.wait(1)
        
        # Add explanation for similarity preservation
        similar_text = Text("These vectors are very similar in the original space - only one position differs!", 
                           font_size=20, color=WHITE).move_to(DOWN * 2)
        similar_text2 = Text("And in the hashed space, they remain similar - the relationship is preserved!", 
                            font_size=20, color=WHITE).next_to(similar_text, DOWN, buff=0.3)
        
        self.play(Transform(transition_text, similar_text))
        self.play(Write(similar_text2))
        self.wait(3)
        
        # Final insight about the preservation principle
        preservation_insight = Text("This is the key: similarity relationships are maintained across both spaces!", 
                                   font_size=22, color=YELLOW).next_to(similar_text2, DOWN, buff=0.5)
        self.play(Write(preservation_insight))
        self.wait(2)
        
        # Clean up the similarity demonstration
        self.play(FadeOut(f1_sim_visual), FadeOut(f2_sim_visual), FadeOut(t1_sim_visual), FadeOut(t2_sim_visual), 
                 FadeOut(transition_text), FadeOut(similar_text2), FadeOut(preservation_insight))
        self.play(FadeOut(highlight_box_f1), FadeOut(highlight_box_f4), FadeOut(highlight_box_t1_dissim), FadeOut(highlight_box_t2), 
                 FadeOut(arrow_f_new), FadeOut(arrow_t_new), FadeOut(sim_f_new), FadeOut(sim_t_new),
                 FadeOut(dotted_line1), FadeOut(dotted_line4))
        self.wait(1)
        
        # Now transition to explaining the full process
        # Step 1: Bring back the t_group (hashed vectors) to show the complete picture
        motivation_text = Text("Now let's understand the complete process...", font_size=26, color=YELLOW).to_edge(DOWN, buff=1)
        self.play(Write(motivation_text))
        self.wait(2)
        self.play(FadeOut(motivation_text))
        
        # Recreate the t_group (hashed vectors) and position them
        t_group = VGroup()
        for i, label in enumerate(["t₁", "t₂", "t₃", "t₄"]):
            box = Rectangle(width=2.0, height=0.7, color=RED, fill_opacity=0.2)
            text = Text(label, font_size=30, color=RED)
            t_group.add(VGroup(box, text).arrange(ORIGIN, buff=0))
        t_group.arrange(RIGHT, buff=0.5).next_to(f_group, DOWN, buff=1.5)
        
        t_label = Text("Hashed Vectors (compressed)", font_size=24, color=RED).next_to(t_group, UP, buff=0.3)
        
        self.play(Write(t_label), Create(t_group))
        self.wait(2)
        
        # Step 2: Explain the goal
        goal_text = Text("Our goal: Prove that similarity relationships are preserved after hashing", 
                        font_size=22, color=WHITE).to_edge(DOWN, buff=0.5)
        self.play(Write(goal_text))
        self.wait(3)
        self.play(FadeOut(goal_text))
        
        # Step 3: Show the pairwise computation process visually
        process_text = Text("Step 1: Compute ALL pairwise similarities within each group", 
                           font_size=24, color=YELLOW).to_edge(DOWN, buff=0.5)
        self.play(Write(process_text))
        
        # Highlight the f_group briefly
        f_highlight_all = SurroundingRectangle(f_group, color=GREEN, buff=0.2)
        self.play(Create(f_highlight_all))
        self.wait(1)
        self.play(FadeOut(f_highlight_all))
        
        # Highlight the t_group briefly  
        t_highlight_all = SurroundingRectangle(t_group, color=RED, buff=0.2)
        self.play(Create(t_highlight_all))
        self.wait(1)
        self.play(FadeOut(t_highlight_all))
        
        self.play(FadeOut(process_text))
        
        # Step 4: Show what we get from pairwise computations
        result_text = Text("This gives us two similarity matrices:", font_size=24, color=WHITE).move_to(ORIGIN)
        matrix_text1 = Text("• F_similarities = all possible pairs of 'f' vectors", font_size=20, color=GREEN).next_to(result_text, DOWN, buff=0.5)
        matrix_text2 = Text("• T_similarities = all possible pairs of 't' vectors", font_size=20, color=RED).next_to(matrix_text1, DOWN, buff=0.5)
        
        self.play(Write(result_text))
        self.play(Write(matrix_text1))
        self.play(Write(matrix_text2))
        self.wait(3)
        self.play(FadeOut(result_text), FadeOut(matrix_text1), FadeOut(matrix_text2))
        
        # Step 5: The key insight
        key_text = Text("Step 2: Compare corresponding pairs between the two matrices", 
                       font_size=24, color=YELLOW).to_edge(DOWN, buff=0.5)
        self.play(Write(key_text))
        
        # Visual demonstration: highlight corresponding pairs
        # Example: f1-f2 similarity vs t1-t2 similarity
        f1_f2_highlight = VGroup(
            SurroundingRectangle(f_group[0], color=YELLOW, buff=0.1),
            SurroundingRectangle(f_group[1], color=YELLOW, buff=0.1)
        )
        t1_t2_highlight = VGroup(
            SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1),
            SurroundingRectangle(t_group[1], color=YELLOW, buff=0.1)
        )
        
        self.play(Create(f1_f2_highlight), Create(t1_t2_highlight))
        
        # Draw connecting lines to show the correspondence
        connection_line1 = DashedLine(f_group[0].get_center(), t_group[0].get_center(), color=YELLOW, stroke_width=2)
        connection_line2 = DashedLine(f_group[1].get_center(), t_group[1].get_center(), color=YELLOW, stroke_width=2)
        
        self.play(Create(connection_line1), Create(connection_line2))
        
        comparison_text = Text("If similarity(f₁,f₂) ≈ similarity(t₁,t₂), then hashing worked!", 
                              font_size=24, color=WHITE).move_to(ORIGIN)
        self.play(Write(comparison_text))
        self.wait(4)
        
        # Clean up this example
        self.play(
            FadeOut(f1_f2_highlight), FadeOut(t1_t2_highlight),
            FadeOut(connection_line1), FadeOut(connection_line2),
            FadeOut(comparison_text), FadeOut(key_text)
        )
        
        # Final summary
        final_summary = VGroup(
            Text("This process validates that our hashing preserves", font_size=22, color=WHITE),
            Text("the relative similarity relationships between vectors", font_size=22, color=WHITE),
            Text("- crucial for maintaining spectral information!", font_size=22, color=YELLOW)
        ).arrange(DOWN, buff=0.3).move_to(DOWN * 1.5)
        
        self.play(Write(final_summary[0]))
        self.wait(1)
        self.play(Write(final_summary[1]))
        self.wait(1)
        self.play(Write(final_summary[2]))
        self.wait(4)
        
        # Clean up before next section
        self.play(FadeOut(f_group, f_label, t_group, t_label, final_summary))
        # ========== SECTION 4: Pairwise Computations ==========
        step4_title = Text("Step 4: Computing Pairwise Similarities", font_size=28).move_to(title.get_center())
        self.play(Write(step4_title))
        
        cosine_formula = MathTex(r"\text{Cosine similarity: } \cos(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{||\mathbf{a}|| \, ||\mathbf{b}||}", font_size=26).move_to(title.get_center() + DOWN * 1.8)
        self.play(Write(cosine_formula))
        self.wait(2)
        
        # Show cosine similarity function box
        box = Rectangle(width=2.5, height=1, color=WHITE, fill_opacity=0.2)
        label = Text("cosine_similarity", font_size=20, color=YELLOW)
        func = VGroup(box, label).move_to(ORIGIN + DOWN * 0.5)
        self.play(Create(func))
        
        # Demonstrate a few key computations
        f = ["f_1", "f_2", "f_3", "f_4"]
        t = ["t_1", "t_2", "t_3", "t_4"]
        
        sample_combinations = [("f_1", "f_2", "f"), ("f_3", "f_4", "f"), ("t_1", "t_2", "t"), ("t_3", "t_4", "t")]
        
        for vec1, vec2, vec_type in sample_combinations:
            # Input vectors
            input1 = MathTex(vec1, font_size=35, color=GREEN if vec_type == "f" else RED).move_to(LEFT * 4)
            input2 = MathTex(vec2, font_size=35, color=GREEN if vec_type == "f" else RED).move_to(LEFT * 4 + DOWN * 0.5)
            self.play(Write(input1), Write(input2), run_time=0.5)
            
            # Move to function
            self.play(input1.animate.move_to(func.get_left() + LEFT * 0.5), 
                     input2.animate.move_to(func.get_left() + LEFT * 0.5 + DOWN * 0.3), run_time=0.5)
            self.play(FadeOut(input1, input2))
            
            # Output
            output = MathTex(f"cs({vec1}, {vec2})", font_size=30, color=GREEN if vec_type == "f" else RED).move_to(func.get_right() + RIGHT * 0.5)
            self.play(Write(output), run_time=0.5)
            self.play(output.animate.move_to(RIGHT * 4), run_time=0.5)
            self.play(FadeOut(output), run_time=0.3)
        
        self.play(FadeOut(func, cosine_formula))
        
        # ========== SECTION 5: Similarity Matrices ==========
        step5_title = Text("Step 5: Building Similarity Matrices", font_size=28).move_to(title.get_center())
        self.play(Transform(step4_title, step5_title))
        
        # Create smaller matrices for better visibility
        m1 = create_empty_matrix_with_subscript_labels(LEFT * 3.5, "f", GREEN)
        m2 = create_empty_matrix_with_subscript_labels(RIGHT * 3.5, "t", RED)
        
        self.play(Create(m1), Create(m2))
        
        matrix_labels = VGroup(
            MathTex(r"cs(f_i, f_j)", font_size=40, color=GREEN).next_to(m1, DOWN, buff=0.3),
            MathTex(r"cs(t_i, t_j)", font_size=40, color=RED).next_to(m2, DOWN, buff=0.3)
        )
        self.play(Write(matrix_labels))
        self.wait(2)
        self.play(FadeOut(matrix_labels))
        
        # Scale and move matrices
        self.play(m1.animate.scale(0.7).move_to(LEFT * 4 + DOWN * 2),
                 m2.animate.scale(0.7).move_to(RIGHT * 4 + DOWN * 2))
        
        # ========== SECTION 6: Final Comparison ==========
        step6_title = Text("Step 6: Comparing Similarity Matrices", font_size=28).move_to(title.get_center())
        self.play(Transform(step4_title, step6_title))
        
        # Show comparison process
        comparison_box = Rectangle(width=2.5, height=1, color=WHITE, fill_opacity=0.2)
        comparison_label = Text("cosine_similarity", font_size=20, color=YELLOW)
        comparison_func = VGroup(comparison_box, comparison_label).move_to(ORIGIN + DOWN * 0.5)
        self.play(Create(comparison_func))
        
        # Demonstrate a few matrix comparisons
        matrix_f = m1[0]
        matrix_t = m2[0]
        
        # Use all upper triangular coordinates for a 4x4 matrix
        upper_tri_coords = []
        for i in range(4):
            for j in range(i+1, 4):
                upper_tri_coords.append((i, j))
        
        for i, j in upper_tri_coords:
            text_f = matrix_f[i][j][1]
            text_t = matrix_t[i][j][1]
            
            # Move values to comparison function
            self.play(text_f.animate.move_to(comparison_func.get_bottom() + LEFT * 0.6 + DOWN * 0.2),
                     text_t.animate.move_to(comparison_func.get_bottom() + RIGHT * 0.6 + DOWN * 0.2), run_time=0.8)
            
            self.play(FadeOut(text_f), FadeOut(text_t), run_time=0.3)
            
            # Show output
            output = MathTex(f"cs(cs(f_{{{i+1}}},f_{{{j+1}}}), cs(t_{{{i+1}}},t_{{{j+1}}}))", 
                           font_size=24, color=YELLOW).move_to(comparison_func.get_top() + UP * 0.2)
            self.play(Write(output), run_time=0.5)
            self.play(FadeOut(output), run_time=0.5)
            
            # Replace with empty cells
            empty_f = MathTex("", font_size=27).move_to(matrix_f[i][j][0].get_center())
            empty_t = MathTex("", font_size=27).move_to(matrix_t[i][j][0].get_center())
            matrix_f[i][j][1] = empty_f
            matrix_t[i][j][1] = empty_t
            self.add(empty_f, empty_t)
        
        # Final conclusion
        final_conclusion = VGroup( 
            Text("Similarity preservation validation complete!", font_size=28, color=YELLOW),
            Text("Our spectral hashing maintains the relative relationships", font_size=24, color=WHITE),
            Text("between vectors - crucial for accurate spectral analysis!", font_size=24, color=WHITE)
        ).arrange(DOWN, buff=0.4).move_to(UP * 1.5)
        
        self.play(Write(final_conclusion[0]))
        self.wait(1)
        self.play(Write(final_conclusion[1]))
        self.wait(1) 
        self.play(Write(final_conclusion[2]))
        self.wait(3)
        
        # Final fade out
        self.play(FadeOut(Group(*self.mobjects)), run_time=2)

# High-quality rendering configuration
if __name__ == "__main__":
    # To render this scene in high quality, run:
    # manim -pqh mergedVideos.py SimilarityPreservationComplete
    pass