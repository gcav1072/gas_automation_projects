import matplotlib.pyplot as plt

def test(tex, desc):
    try:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, tex, fontsize=20)
        fig.canvas.draw()
        print(f"[OK] {desc}")
        plt.close(fig)
    except Exception as e:
        print(f"[FAIL] {desc}: {e}")
        plt.close(fig)

test(r"$1+1=2$", "Basic Path")
test(r"$\frac{1}{2}$", "Fraction")
test(r"$\sqrt{2}$", "Sqrt")
test(r"$\left( 1 \right)$", "Left/Right Parentheses")
test(r"$\begin{array}{cc} a & b \\ c & d \end{array}$", "Array Environment")
test(r"$\begin{pmatrix} a & b \\ c & d \end{pmatrix}$", "pmatrix Environment")
