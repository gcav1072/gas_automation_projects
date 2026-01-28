import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import gauss_jordan
# Importa la función de formateo
from latex_formatter import matrix_to_latex_export 

# --- (Local functions removed in favor of latex_formatter.py) ---

# --------------------------------------------------------------------------

class ScrollableFrame(tk.Frame):
    """Un frame helper que permite hacer scroll vertical"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, bg="white")
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Habilitar scroll con rueda del ratón
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        self.canvas = canvas

class GaussJordanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gauss-Jordan Eliminator (Gabosoft)")
        self.root.geometry("900x700")

        # Input Frame
        input_frame = tk.Frame(root, pady=10)
        input_frame.pack()

        tk.Label(input_frame, text="Filas:").pack(side=tk.LEFT)
        self.entry_rows = tk.Entry(input_frame, width=5)
        self.entry_rows.pack(side=tk.LEFT, padx=5)
        self.entry_rows.insert(0, "3")

        tk.Label(input_frame, text="Cols:").pack(side=tk.LEFT)
        self.entry_cols = tk.Entry(input_frame, width=5)
        self.entry_cols.pack(side=tk.LEFT, padx=5)
        self.entry_cols.insert(0, "4")

        btn_gen = tk.Button(input_frame, text="Generar Matriz", command=self.generate_matrix_grid)
        btn_gen.pack(side=tk.LEFT, padx=10)

        # Matrix Entry Frame
        self.matrix_frame = tk.Frame(root)
        self.matrix_frame.pack(pady=10)
        self.entries = []

        # Operations Frame
        ops_frame = tk.Frame(root, pady=5)
        ops_frame.pack()
        
        btn_solve = tk.Button(ops_frame, text="Resolver Paso a Paso", command=self.solve, bg="#dddddd")
        btn_solve.pack(side=tk.LEFT, padx=10)
        
        btn_export = tk.Button(ops_frame, text="Exportar a LaTeX", command=self.export_latex, bg="#dddddd")
        btn_export.pack(side=tk.LEFT, padx=10)

        # --- REEMPLAZO DEL TEXT AREA POR SCROLLABLE FRAME ---
        container_frame = tk.Frame(root)
        container_frame.pack(pady=10, expand=True, fill=tk.BOTH)
        
        self.output_area = ScrollableFrame(container_frame)
        self.output_area.pack(fill="both", expand=True)

        self.generate_matrix_grid()

    def generate_matrix_grid(self):
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        self.entries = []

        try:
            rows = int(self.entry_rows.get())
            cols = int(self.entry_cols.get())
        except ValueError:
            messagebox.showerror("Error", "Filas y Cols deben ser enteros.")
            return

        for r in range(rows):
            row_entries = []
            for c in range(cols):
                e = tk.Entry(self.matrix_frame, width=8, justify='center')
                e.grid(row=r, column=c, padx=2, pady=2)
                # Decoración visual para la matriz aumentada
                if c == cols - 1:
                    e.config(bg="#f0f8ff") # Un azul muy suave para la columna b
                row_entries.append(e)
            self.entries.append(row_entries)
        
        self.cols_count = cols
        self.rows_count = rows

    def get_matrix_data(self):
        # Helper para obtener A y b de las entradas
        A = []
        b = []
        rows = len(self.entries)
        cols = len(self.entries[0])
        n_vars = cols - 1
        
        for r in range(rows):
            row_vals = []
            for c in range(n_vars):
                val = self.entries[r][c].get()
                if not val: val = "0"
                row_vals.append(val)
            A.append(row_vals)
            b_val = self.entries[r][cols-1].get()
            if not b_val: b_val = "0"
            b.append(b_val)
        return A, b

    def solve(self):
        # Limpiar resultados anteriores
        for widget in self.output_area.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            A, b = self.get_matrix_data()
            rows = len(A)

            # Lógica de cálculo
            sol, hist = gauss_jordan.gauss_jordan(A, b, verbose=False)
            
            # --- RENDERIZADO DE MATPLOTLIB (TEXT MODE) ---
            # Importar la nueva función de texto
            from latex_formatter import matrix_to_text

            for i, step in enumerate(hist):
                # 1. Obtener la matriz en TEXTO PLANO
                matrix_str = matrix_to_text(step['matrix'])
                
                # 2. Mensaje del paso
                step_msg = step['message']
                
                # 3. Calcular altura dinámica
                # Ajustamos la altura para texto monoespaciado
                # Aproximadamente 0.3 por línea de texto + margen
                num_lines = matrix_str.count('\n') + 1
                fig_height = 0.5 + (num_lines * 0.3)
                
                fig = Figure(figsize=(6, fig_height), dpi=100)
                fig.patch.set_facecolor('white')
                
                ax = fig.add_subplot(111)
                ax.axis('off')
                
                # A) TÍTULO
                ax.set_title(step_msg, fontsize=10, color='#333333', pad=4, loc='center', fontname="DejaVu Sans")
                
                # B) MATRIZ (TEXTO)
                # Usamos fuente monospace para alinear columnas
                ax.text(0.5, 0.4, matrix_str, 
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=12, 
                        color='black',
                        fontfamily='monospace')
                
                # 4. Empaquetar en Tkinter
                canvas = FigureCanvasTkAgg(fig, master=self.output_area.scrollable_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(pady=2, padx=10, fill=tk.X)
                
                # Separador sutil entre pasos
                tk.Frame(self.output_area.scrollable_frame, height=1, bg="#e0e0e0").pack(fill=tk.X, pady=4, padx=20)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            import traceback
            traceback.print_exc()

    def export_latex(self):
        try:
            # Pedir nombre de archivo
            filename = filedialog.asksaveasfilename(
                defaultextension=".tex",
                filetypes=[("LaTeX Files", "*.tex"), ("All Files", "*.*")]
            )
            if not filename:
                return

            A, b = self.get_matrix_data()
            sol, hist = gauss_jordan.gauss_jordan(A, b, verbose=False)
            
            from latex_formatter import matrix_to_latex_export

            latex_content = [
                r"\documentclass{article}",
                r"\usepackage[utf8]{inputenc}",
                r"\usepackage{amsmath}",
                r"\usepackage{amssymb}",
                r"\usepackage{geometry}",
                r"\geometry{a4paper, margin=1in}",
                r"\title{Resolución Gauss-Jordan}",
                r"\author{Gabriel Astudillo - Powered by Python}",
                r"\date{\today}",
                r"\begin{document}",
                r"\maketitle",  
                r"\section*{Pasos de Resolución}"
            ]

            for i, step in enumerate(hist):
                msg = step['message']
                matrix_tex = matrix_to_latex_export(step['matrix'])
                
                latex_content.append(r"\paragraph{Paso " + str(i+1) + ": " + msg + "}")
                latex_content.append(matrix_tex)
            
            latex_content.append(r"\end{document}")

            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(latex_content))
            
            messagebox.showinfo("Éxito", f"Archivo exportado correctamente a:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error Exportando", str(e))
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    root = tk.Tk()
    app = GaussJordanGUI(root)
    root.mainloop()