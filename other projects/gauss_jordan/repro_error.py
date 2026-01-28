import matplotlib.pyplot as plt

try:
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    # This string matches what the user is generating:
    # r"$\left( \begin{array}{ccc|c} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} \right)$"
    
    latex_str = r"$\left( \begin{array}{ccc|c} 1 & 1 & 1 & 3 \\ 1 & 2 & 3 & 6 \\ 3 & 2 & 1 & 6 \\ \end{array} \right)$"
    
    ax.text(0.5, 0.5, latex_str, fontsize=20)
    
    # We need to trigger a draw for the error to happen usually
    fig.canvas.draw()
    print("Success! No error.")
except Exception as e:
    print(f"Caught expected error: {e}")
