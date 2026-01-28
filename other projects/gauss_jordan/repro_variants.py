import matplotlib.pyplot as plt

def test_latex(latex_str, name):
    try:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, latex_str, fontsize=20)
        fig.canvas.draw()
        print(f"Success: {name}")
        plt.close(fig)
    except Exception as e:
        print(f"Failed: {name} with error: {e}")
        plt.close(fig)

# Variant 1: Original but no | (failed before?? Let's re-verify)
# Note: The traceback says "ParseSyntaxException".
v1 = r"$\left( \begin{array}{cccc} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} \right)$"
test_latex(v1, "No Pipe")

# Variant 2: No space after \left(
v2 = r"$\left(\begin{array}{cccc} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array}\right)$"
test_latex(v2, "No Spaces \left")

# Variant 3: No \left \right, just ( )
v3 = r"$( \begin{array}{cccc} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} )$"
test_latex(v3, "Simple Parentheses")

# Variant 4: pmatrix (if supported)
v4 = r"$\begin{pmatrix} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \end{pmatrix}$"
test_latex(v4, "pmatrix")

# Variant 5: bmatrix
v5 = r"$\begin{bmatrix} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \end{bmatrix}$"
test_latex(v5, "bmatrix")

# Variant 6: Original WITH pipe to confirm it fails specifically due to pipe if others pass
v6 = r"$\left( \begin{array}{ccc|c} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} \right)$"
test_latex(v6, "Original with Pipe")
