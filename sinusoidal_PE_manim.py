from manim import *
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────
D_SIN = 6
# Visualization-only wavelengths (log spaced) so the waves are drawable on [0, 1000]
VIS_LAMBDA_MIN = 5
VIS_LAMBDA_MAX = 2000

_i = np.arange(D_SIN)
WAVELENGTHS = (VIS_LAMBDA_MIN / (2 * np.pi)) * (VIS_LAMBDA_MAX / VIS_LAMBDA_MIN) ** (_i / (D_SIN - 1))

WAVE_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]

def sin_enc(wi, x):
    return np.sin(x / WAVELENGTHS[wi])


class SinusoidalPE(Scene):
    def construct(self):
        self._scene_1()

    def _cam_scale(self):
        return self.camera.frame.width / config.frame_width

    # ── Scene 1 ── The Question ───────────────────────────────────────
    def _scene_1(self):
        ax = Axes(
            x_range=[0, 1000, 100], y_range=[-1.5, 1.5, 0.5], # Adjusted y_range for waves
            x_length=10, y_length=4,
            axis_config={"include_tip": True},
        ).shift(DOWN * 0.5)
        
        # Original y_range for spectrum was [0, 100, 10]
        # We need to handle the transition or just use different axes for the waves.
        # Let's keep the ax for the spectrum and create a second set of axes or transform it.
        # Actually, the user says "After fading out everything but the bar at 600".
        
        spectrum_ax = Axes(
            x_range=[0, 1000, 100], y_range=[0, 100, 10],
            x_length=10, y_length=5,
            axis_config={"include_tip": True},
        ).shift(DOWN * 0.3)
        
        mz_lbl = Text("m/z", font_size=24).next_to(spectrum_ax.x_axis, DOWN, buff=0.2)
        int_lbl = Text("Intensity", font_size=24).next_to(spectrum_ax.y_axis, LEFT, buff=0.2)

        # Create a realistic looking mass spectrum with many peaks
        np.random.seed(42)
        peak_positions = np.random.uniform(100, 900, 40)
        peak_heights = np.random.uniform(20, 95, 40)

        # Force a large peak at 600 m/z
        peak_positions = np.append(peak_positions, 600)
        peak_heights = np.append(peak_heights, 95)
        
        bars = VGroup()
        for x_pos, height in zip(peak_positions, peak_heights):
            bar = Line(
                start=spectrum_ax.c2p(x_pos, 0),
                end=spectrum_ax.c2p(x_pos, height),
                color=WHITE,
                stroke_width=2
            )
            bars.add(bar)

        self.play(Create(spectrum_ax), Write(mz_lbl), Write(int_lbl))
        self.play(Create(bars), run_time=1.5)
        self.wait(1)

        # Find the bar at 600 m/z (it's the last one we added)
        bar_600 = bars[-1]
        dot_600 = Dot(spectrum_ax.c2p(600, 95), color=YELLOW, radius=0.08)
        lbl = Text("m/z = 600", font_size=22, color=YELLOW)\
            .next_to(dot_600, UP, buff=0.2)
        self.play(
            bar_600.animate.set_color(YELLOW).set_stroke(width=4),
            FadeIn(dot_600), Write(lbl),
        )

        question = Text(
            "How does the model know this peak is at m/z = 600?",
            font_size=28,
        ).to_edge(UP, buff=0.3)
        
        # Fade out all peaks except the one at 600 m/z
        others = VGroup(*[b for b in bars if b != bar_600])
        self.play(
            Write(question),
            FadeOut(others, run_time=1.5)
        )
        self.wait(1)

        # Now transition to waves.
        # We'll use a new set of axes for the waves but keep them aligned on x with spectrum_ax.
        wave_ax = Axes(
            x_range=[0, 1000, 100], y_range=[-1.5, 1.5, 1],
            x_length=10, y_length=3,
            axis_config={"include_tip": False},
        ).move_to(spectrum_ax.get_center())

        self.play(
            FadeOut(spectrum_ax),
            FadeOut(int_lbl),
            FadeOut(mz_lbl),
            FadeOut(dot_600),
            FadeOut(lbl),
            bar_600.animate.set_stroke(width=2, opacity=0.5), # Dim the bar
            Create(wave_ax)
        )

        formula_lbl = MathTex(r"\sin\left(\frac{\mathrm{m/z}}{\lambda_i}\right)", font_size=32).next_to(question, DOWN, buff=0.4)
        self.play(FadeIn(formula_lbl))

        # Draw waves from slow (index 6) to fast (index 0)
        # Note: sin(x/lambda) where lambda is large is slow.
        
        waves = VGroup()
        intersection_dots = VGroup()
        y_vals = []
        
        # Indices in descending order for slow to fast
        indices = list(range(D_SIN - 1, -1, -1))

        lambda_lbl = MathTex(rf"\lambda_{{{indices[0]}}}", font_size=30).next_to(formula_lbl, RIGHT, buff=1.5)
        # Using separate parts for (600, and y_val) to allow specific highlighting
        mz_part = Text("(600, ", font_size=24)
        val_part = Text("0.000)", font_size=24).next_to(mz_part, RIGHT, buff=0.1)
        coord_lbl = VGroup(mz_part, val_part).next_to(lambda_lbl, DOWN, buff=0.2)
        
        self.play(FadeIn(lambda_lbl), FadeIn(coord_lbl))
        
        for i, idx in enumerate(indices):
            color = WAVE_COLORS[idx]
            wl = WAVELENGTHS[idx]
            
            # Use use_smoothing=False and more points for faster waves if we include them
            wave = wave_ax.plot(
                lambda x: np.sin(x / wl),
                x_range=[0, 1000, 0.2],
                color=color,
                stroke_width=2,
                use_smoothing=False,
            )
            
            # Dot where it hits 600
            y_val = np.sin(600 / wl)
            y_vals.append(y_val)
            dot = Dot(wave_ax.c2p(600, y_val), color=color, radius=0.06)
            
            new_lambda_lbl = MathTex(rf"\lambda_{{{idx}}}", font_size=30).next_to(formula_lbl, RIGHT, buff=1.5)
            # Create a new val_part and VGroup for the update
            new_val_text = f"{y_val:.3f})"
            new_val_part = Text(new_val_text, font_size=24).next_to(mz_part, RIGHT, buff=0.1)
            new_coord_lbl = VGroup(mz_part, new_val_part)

            # Highlight circle for the new point
            highlight_circle = Circle(radius=0.15, color=YELLOW, stroke_width=3).move_to(dot.get_center())
            # Highlight circle ONLY for the updating value part
            val_highlight = Circle(radius=0.4, color=YELLOW, stroke_width=3).move_to(new_val_part.get_center()).scale(0.5)

            self.play(
                Create(wave),
                FadeIn(dot),
                Transform(lambda_lbl, new_lambda_lbl),
                Transform(val_part, new_val_part),
                Succession(
                    FadeIn(highlight_circle, scale=0.5),
                    FadeOut(highlight_circle, scale=1.5),
                ),
                Succession(
                    FadeIn(val_highlight, scale=0.5),
                    FadeOut(val_highlight, scale=1.5),
                ),
                Flash(dot, color=YELLOW, line_length=0.1, flash_radius=0.2),
                run_time=2.0
            )
            intersection_dots.add(dot)
            waves.add(wave)
            self.wait(0.2)

        self.wait(2)

        # Transition to vector form
        values_str = " \\\\ ".join(f"{y:.3f}" for y in y_vals)
        vec = MathTex(
            r"\mathbf{p}(600) = \begin{bmatrix}" + values_str + r"\end{bmatrix}",
            font_size=32,
        ).move_to(wave_ax.get_center())
        conclusion = Text(
            "Together, these values form the positional encoding vector.",
            font_size=26,
        ).next_to(vec, DOWN, buff=0.4)

        self.play(
            FadeOut(waves),
            FadeOut(intersection_dots),
            FadeOut(lambda_lbl),
            FadeOut(coord_lbl),
            FadeOut(formula_lbl),
            FadeOut(wave_ax),
            FadeOut(bar_600),
            FadeOut(question),
        )
        self.play(Write(vec))
        self.play(FadeIn(conclusion))
        self.wait(2)
        
        
        
