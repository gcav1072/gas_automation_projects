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

# Variant 1: \pmatrix without begin/end? (Plain TeX style)
v1 = r"$\pmatrix{ 1 & 2 \cr 3 & 4 }$"
test_latex(v1, "Plain TeX pmatrix")

# Variant 2: \matrix
v2 = r"$\matrix{ 1 & 2 \cr 3 & 4 }$"
test_latex(v2, "Plain TeX matrix")

# Variant 3: Maybe Matplotlib has a specific way?
