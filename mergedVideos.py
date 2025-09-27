from manim import *
import numpy as np
from manim import logger
import logging
logger.setLevel(logging.WARNING)

# ---------- Helpers ----------
def make_title(scene: Scene, text="Similarity Preservation in Spectral Hashing"):
    title = Text(text, font_size=40)
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
        
        spec_title = Text("Step 1: Original Spectra", font_size=28).move_to(title.get_center())
        self.play(Write(spec_title))
        
        spec_motivation = Text("Using 4 spectra, we'll prove that", font_size=20).move_to(title.get_center())
        spec_motivation2 = Text("they are similar in both their hashed and nonhashed versions.", font_size=20).next_to(spec_motivation, DOWN, buff=0.5)
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
        self.play(FadeOut(spec_motivation, spectra_group,spec_motivation2,title))
        
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
        
        # Explanation sequence
        explanation_texts = []
        
        expl1 = Text("We have the unhashed, binned feature vectors, and the hashed, compressed vectors.", font_size=20).to_edge(UP, buff=1.0)
        self.play(Write(expl1))
        explanation_texts.append(expl1)
        
        expl2 = Text("How do we know that the hashing worked correctly?", font_size=20).next_to(expl1, DOWN, buff=0.3)
        self.play(Write(expl2))
        explanation_texts.append(expl2)
        
        expl3 = Text("We need to prove that similar vectors in the original space remain similar in the hashed space.", font_size=20).next_to(expl2, DOWN, buff=0.3)
        self.play(Write(expl3))
        explanation_texts.append(expl3)
        
        expl4 = Text("Alternatively, dissimilar vectors in the original space remain dissimilar in the hashed space.", font_size=20).next_to(expl3, DOWN, buff=0.3)
        self.play(Write(expl4))
        explanation_texts.append(expl4)
        
        expl5 = Text("Let's illustrate this with a simple example.", font_size=20).next_to(expl4, DOWN, buff=0.3)
        self.play(Write(expl5))
        explanation_texts.append(expl5)
        
        self.wait(2)
        self.play(*[FadeOut(text) for text in explanation_texts])
        
        # Vector visualization
        f_group = VGroup()
        for i, label in enumerate([r"f_1", r"f_2", r"f_3", r"f_4"]):
            box = Rectangle(width=2.0, height=0.7, color=GREEN, fill_opacity=0.2)
            text = MathTex(label, font_size=30, color=GREEN)
            f_group.add(VGroup(box, text).arrange(ORIGIN, buff=0))
        f_group.arrange(RIGHT, buff=0.5).to_edge(UP, buff=1.0)
        
        t_group = VGroup()
        for i, label in enumerate([r"t_1", r"t_2", r"t_3", r"t_4"]):
            box = Rectangle(width=2.0, height=0.7, color=RED, fill_opacity=0.2)
            text = MathTex(label, font_size=30, color=RED)
            t_group.add(VGroup(box, text).arrange(ORIGIN, buff=0))
        t_group.arrange(RIGHT, buff=0.5).next_to(f_group, DOWN, buff=1.5)
        
        f_label = Text("Non-hashed Vectors (original)", font_size=24, color=GREEN).next_to(f_group, UP, buff=0.3)
        t_label = Text("Hashed Vectors (compressed)", font_size=24, color=RED).next_to(t_group, UP, buff=0.3)
        
        self.play(Write(f_label), Create(f_group))
        self.play(Write(t_label), Create(t_group))
        
        # Highlight similar pairs (f1, f2) and (t1, t2)
        highlight_box_f1 = SurroundingRectangle(f_group[0], color=YELLOW, buff=0.1)
        highlight_box_f2 = SurroundingRectangle(f_group[1], color=YELLOW, buff=0.1)
        highlight_box_t1 = SurroundingRectangle(t_group[0], color=YELLOW, buff=0.1)
        highlight_box_t2 = SurroundingRectangle(t_group[1], color=YELLOW, buff=0.1)
        
        self.play(Create(highlight_box_f1), Create(highlight_box_f2), Create(highlight_box_t1), Create(highlight_box_t2))
        
        # Show similarity arrows
        arrow_f = CurvedArrow(f_group[0].get_bottom(), f_group[1].get_bottom(), color=YELLOW, angle=0.3)
        sim_f = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_f, DOWN, buff=0.1)
        
        arrow_t = CurvedArrow(t_group[0].get_bottom(), t_group[1].get_bottom(), color=YELLOW, angle=0.3)
        sim_t = Text("similarity", font_size=20, color=YELLOW).next_to(arrow_t, DOWN, buff=0.1)
        
        self.play(Create(arrow_f), Write(sim_f))
        self.play(Create(arrow_t), Write(sim_t))
        
        # Show example values
        f1_similar = np.array([0,0,0,1,1,1,0,0])
        f2_similar = np.array([0,0,1,1,1,1,0,0])
        
        f1_sim_visual = MathTex(f"f_1 = {f1_similar}", font_size=24, color=GREEN).move_to(LEFT * 4 + UP * 0.5)
        f2_sim_visual = MathTex(f"f_2 = {f2_similar}", font_size=24, color=GREEN).move_to(LEFT * 4 + DOWN * 0.5)
        
        self.play(Write(f1_sim_visual), Write(f2_sim_visual))
        
        similar_text = Text("These vectors are very similar - only one position differs!", font_size=22, color=WHITE).to_edge(DOWN, buff=1)
        self.play(Write(similar_text))
        self.wait(3)
        
        # Clean up for next section
        self.play(FadeOut(f1_sim_visual, f2_sim_visual, similar_text, highlight_box_f1, highlight_box_f2, 
                         highlight_box_t1, highlight_box_t2, arrow_f, sim_f, arrow_t, sim_t))
        
        # Final explanation
        conclusion = Text("If similar items remain similar after hashing,\nthen our compression method works correctly!", 
                         font_size=26, color=YELLOW).move_to(DOWN * 1.5)
        self.play(Write(conclusion))
        self.wait(3)
        self.play(FadeOut(conclusion, f_group, t_group, f_label, t_label))
        
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