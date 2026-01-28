import matplotlib.pyplot as plt

def test_usetex():
    try:
        plt.rcParams['text.usetex'] = True
        fig = plt.figure()
        ax = fig.add_subplot(111)
        # Simple test
        ax.text(0.5, 0.5, r"$\begin{array}{cc} 1 & 2 \\ 3 & 4 \end{array}$", fontsize=20)
        fig.canvas.draw()
        print("[OK] usetex=True worked!")
    except Exception as e:
        print(f"[FAIL] usetex=True failed: {e}")
    finally:
        plt.close(fig)

if __name__ == "__main__":
    test_usetex()
