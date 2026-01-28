import numpy as np
from fractions import Fraction
import sys

def format_matrix(matrix, message="Matrix state:"):
    """
    Returns a string representation of the matrix with Fraction values.
    """
    lines = [f"--- {message} ---"]
    rows, cols = matrix.shape
    
    # Calculate column widths for nice alignment
    col_widths = []
    for j in range(cols):
        max_len = 0
        for i in range(rows):
            val_str = str(matrix[i, j])
            max_len = max(max_len, len(val_str))
        col_widths.append(max_len)
    
    for i in range(rows):
        row_str = []
        for j in range(cols):
            val = matrix[i, j]
            # Add a separator line for the augmented part
            if j == cols - 1:
                row_str.append("|")
            row_str.append(f"{str(val):>{col_widths[j]}}")
        lines.append("  ".join(row_str))
    
    return "\n".join(lines)

def print_matrix(matrix, message="Matrix state:"):
    print(format_matrix(matrix, message))
    print()

def to_fraction_matrix(A, b):
    """
    Converts input A and b into a single augmented numpy matrix of Fractions.
    """
    A_frac = np.array([[Fraction(x) for x in row] for row in A], dtype=object)
    b_frac = np.array([Fraction(x) for x in b], dtype=object)
    
    # Reshape b to be a column vector if it's 1D
    if b_frac.ndim == 1:
        b_frac = b_frac.reshape(-1, 1)
        
    return np.hstack((A_frac, b_frac))

def gauss_jordan(A, b, verbose=True):
    """
    Performs Gauss-Jordan elimination on system Ax = b.
    Returns (solution, history) tuple.
    history is a list of descriptions and matrix snapshots.
    """
    matrix = to_fraction_matrix(A, b)
    rows, cols = matrix.shape
    n_vars = cols - 1
    
    history = []
    
    def record_step(mat, msg):
        # Store a copy of the matrix and the message
        step_data = {
            "matrix": mat.copy(),
            "message": msg,
            "formatted": format_matrix(mat, msg)
        }
        history.append(step_data)
        if verbose:
            print(step_data["formatted"])
            print()

    record_step(matrix, "Matriz Inicial Aumentada")
    
    pivot_row = 0
    
    for col in range(n_vars):
        if pivot_row >= rows:
            break
            
        # Optimization: If the current element is 1, keep it as pivot to avoid unnecessary swaps
        if matrix[pivot_row, col] == 1:
            pivot_idx = pivot_row
        else:
            # Find pivot (partial pivoting for stability/validity)
            # We look for the largest absolute value in the current column from pivot_row downwards
            current_column = matrix[pivot_row:, col]
            # We need to manually handle absolute values for Fractions
            max_val = -1
            pivot_idx = -1
            
            for i, val in enumerate(current_column):
                abs_val = abs(val)
                if abs_val > max_val:
                    max_val = abs_val
                    pivot_idx = i + pivot_row
                
        # If the column is all zeros (or close enough), move to next column
        if matrix[pivot_idx, col] == 0:
            continue
            
        # Swap rows if necessary
        if pivot_idx != pivot_row:
            matrix[[pivot_row, pivot_idx]] = matrix[[pivot_idx, pivot_row]]
            record_step(matrix, f"Intercambiar F{pivot_row+1} ↔ F{pivot_idx+1}")
            
        # Normalize the pivot row
        pivot_val = matrix[pivot_row, col]
        if pivot_val != 1:
            matrix[pivot_row] = matrix[pivot_row] / pivot_val
            record_step(matrix, f"F{pivot_row+1} / {pivot_val} → F{pivot_row+1}")
            
        # Eliminate other rows
        for i in range(rows):
            if i != pivot_row:
                factor = matrix[i, col]
                if factor != 0:
                    matrix[i] -= factor * matrix[pivot_row]
                    record_step(matrix, f"F{i+1} - ({factor}) · F{pivot_row+1} → F{i+1}")
        
        pivot_row += 1
        
    # User-friendly Analysis of the final matrix
    # Check for Inconsistency: [0 ... 0 | non-zero]
    # Check for Indeterminacy: Rank < Variables (free variables)
    
    rank = 0
    inconsistent = False
    
    for i in range(rows):
        row = matrix[i, :-1]
        aug_val = matrix[i, -1]
        
        is_all_zeros = all(x == 0 for x in row)
        
        if is_all_zeros and aug_val != 0:
            inconsistent = True
        
        if not is_all_zeros:
            rank += 1
            
    if inconsistent:
        msg = "RESULTADO: Sistema Incompatible (SI) - No tiene solucion."
        if verbose: print(f"\n{msg}")
        history.append({"matrix": matrix.copy(), "message": msg, "formatted": msg})
        return None, history
    elif rank < n_vars:
        msg = f"RESULTADO: Sistema Compatible Indeterminado (SCI) - Infinitas soluciones.\nGrados de libertad: {n_vars - rank}"
        if verbose: print(f"\n{msg}")
        history.append({"matrix": matrix.copy(), "message": msg, "formatted": msg})
        return None, history
    else:
        msg = "RESULTADO: Sistema Compatible Determinado (SCD) - Solucion Unica"
        if verbose: print(f"\n{msg}")
        history.append({"matrix": matrix.copy(), "message": msg, "formatted": msg})
        
        solution = matrix[:n_vars, -1]
        if verbose:
            for i, val in enumerate(solution):
                print(f"x{i+1} = {val}")
        return solution, history

def main():
    print("=== Calculadora Gauss-Jordan Paso a Paso ===")
    print("Ejemplos predefinidos disponibles.")
    
    # Example 1: Unique Solution
    A_scd = [[2, 1, -1],
             [5, 2, 2],
             [3, 1, 1]]
    b_scd = [8, 12, 5]
    
    # Example 2: Inconsistent
    A_si = [[1, 1, 1],
            [1, 1, 1],
            [2, 3, 4]]
    b_si = [2, 3, 5]
    
    # Example 3: Infinite Solutions
    A_sci = [[1, 1, 1],
             [2, 2, 2],
             [3, 3, 3]]
    b_sci = [2, 4, 6]

    def ask_choice():
        print("\nSelecciona un caso de prueba:")
        print("1. Sistema con Solucion Unica (SCD)")
        print("2. Sistema Incompatible (SI)")
        print("3. Sistema Indeterminado (SCI)")
        print("4. Ingresar manualmente")
        return input("Opcion: ")

    choice = ask_choice()
    
    if choice == '1':
        print("\n--- Ejecutando Caso SCD ---")
        gauss_jordan(A_scd, b_scd)
    elif choice == '2':
        print("\n--- Ejecutando Caso SI ---")
        gauss_jordan(A_si, b_si)
        
    elif choice == '3':
        print("\n--- Ejecutando Caso SCI ---")
        gauss_jordan(A_sci, b_sci)
    elif choice == '4':
        try:
            n = int(input("Numero de ecuaciones (filas): "))
            m = int(input("Numero de incógnitas (columnas): "))
            
            print(f"Introduce la matriz de coeficientes A ({n}x{m}) fila por fila (separando numeros por espacios):")
            A = []
            for i in range(n):
                row = list(map(str, input(f"Fila {i+1}: ").strip().split()))
                if len(row) != m:
                    raise ValueError(f"Se esperaban {m} numeros.")
                A.append(row)
                
            print(f"Introduce el vector de terminos independientes b ({n} valores):")
            b = list(map(str, input("b: ").strip().split()))
            if len(b) != n:
                 raise ValueError(f"Se esperaban {n} numeros.")
                 
            gauss_jordan(A, b)
            
        except Exception as e:
            print(f"Error en entrada: {e}")
    else:   
        print("Opcion invalida.")

if __name__ == "__main__":
    main()
