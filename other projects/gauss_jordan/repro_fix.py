import matplotlib.pyplot as plt

try:
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    # Removed the | from {ccc|c} -> {cccc}
    # r"$\left( \begin{array}{cccc} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} \right)$"
    
    latex_str = r"$\left( \begin{array}{cccc} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} \right)$"
    
    ax.text(0.5, 0.5, latex_str, fontsize=20)
    
    fig.canvas.draw()
    print("Success! No error with fix.")
except Exception as e:
    print(f"Caught expected error: {e}")
