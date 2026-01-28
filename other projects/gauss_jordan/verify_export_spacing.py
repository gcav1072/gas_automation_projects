import sys
import os
import numpy as np

# Add project path
sys.path.append(os.getcwd())

from latex_formatter import matrix_to_latex_export

def verify_export():
    try:
        from fractions import Fraction
        
        matrix = np.array([
            [Fraction(1, 2), Fraction(3, 1), Fraction(5, 2)],
            [Fraction(2, 3), Fraction(4, 1), Fraction(1, 6)]
        ], dtype=object)
        
        print("Testing matrix_to_latex_export header...")
        tex = matrix_to_latex_export(matrix)
        print("Generated LaTeX Segment:")
        print(tex)
        
        if r"\\[1.2em]" not in tex:
            print("FAILED: Row spacing [1.2em] not found.")
            return False

        print("Success! LaTeX spacing confirmed.")
        return True
        
    except Exception as e:
        print(f"Export Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_export():
        sys.exit(0)
    else:
        sys.exit(1)
