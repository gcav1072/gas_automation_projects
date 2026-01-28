from fractions import Fraction

def format_fraction_tex(val):
    """Convierte una Fraction o número a string LaTeX."""
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return f"{val.numerator}"
        
        sign = "-" if val < 0 else ""
        num = abs(val.numerator)
        den = val.denominator
        
        # CAMBIO CLAVE: Usamos 'dfrac' en lugar de 'frac'.
        # 'dfrac' fuerza el tamaño grande de la fracción sin romper Matplotlib.
        return f"{sign}\\dfrac{{{num}}}{{{den}}}"
    else:
        return str(val).replace('.', ',')

def format_fraction_text(val):
    """Convierte una Fraction o número a string simple para texto."""
    if isinstance(val, Fraction):
        return str(val)
    else:
        return str(val)

def matrix_to_latex_export(matrix):
    """
    Genera el código LaTeX de la matriz para EXPORTACIÓN (archivo .tex).
    Incluye el separador vertical '|' para la matriz aumentada y usa 'dfrac'.
    Retorna el bloque matemático completo con delimitadores \ [ ... \ ].
    """
    rows, cols = matrix.shape
    
    # Formato de columnas: todas centradas, con barra antes de la última
    # Ejemplo para 4 cols: ccc|c
    if cols > 1:
        col_format = "c" * (cols - 1) + "|c"
    else:
        col_format = "c"
    
    latex_str = "\\[\n\\left( \\begin{array}{" + col_format + "} \n"
    
    for i in range(rows):
        row_tex = []
        for j in range(cols):
            val = matrix[i, j]
            row_tex.append(format_fraction_tex(val))
        
        latex_str += " & ".join(row_tex) + r" \\[1.2em] " + "\n"
        
    latex_str += "\\end{array} \\right)\n\\]"
    
    return latex_str

def matrix_to_text(matrix):
    """
    Genera una representación de texto alineada de la matriz.
    Ejemplo:
    [ 1   2 | 3 ]
    [ 4   5 | 6 ]
    """
    rows, cols = matrix.shape
    
    # 1. Convertir todo a string primero para medir anchos
    str_matrix = []
    col_widths = [0] * cols
    
    for r in range(rows):
        row_strs = []
        for c in range(cols):
            val = matrix[r, c]
            s = format_fraction_text(val)
            row_strs.append(s)
            col_widths[c] = max(col_widths[c], len(s))
        str_matrix.append(row_strs)
        
    # 2. Construir la string alineada
    lines = []
    for r in range(rows):
        line_parts = []
        for c in range(cols):
            # Alinear a la derecha
            val_str = str_matrix[r][c]
            width = col_widths[c]
            aligned = val_str.rjust(width)
            line_parts.append(aligned)
            
            # Agregar el separador vertical si es necesario
            if c == cols - 2: # Antes de la última columna
                 line_parts.append(" | ")
            elif c < cols - 2:
                 line_parts.append("  ") # Espacio normal entre columnas
                 
        # Unir toda la línea
        line_content = "".join(line_parts)
        lines.append(f"[ {line_content} ]")
        
    return "\n".join(lines)