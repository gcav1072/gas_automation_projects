import tkinter as tk
import os
import sys
from tkinter import messagebox, simpledialog
from PIL import Image, ImageDraw, ImageFont
from crossword import CrosswordGenerator

class CrosswordGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Crucigramas")
        #self.root.geometry("1920x1080")
        if os.name == 'nt':
            self.root.state('zoomed')
        else:
            self.root.attributes('-zoomed', True)
        
        # Icono (opcional, si existiera)
        # try:
        #     icon_path = self.resource_path("icon.ico")
        #     self.root.iconbitmap(icon_path)
        # except:
        #     pass

        self.word_list = []
        self.generator = None
        self.cell_size = 75

        self._setup_ui()

    def _setup_ui(self):
        # --- Panel Izquierdo ---
        control_frame = tk.Frame(self.root, padx=10, pady=10, bg="#f0f0f0")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Entrada de palabras
        tk.Label(control_frame, text="Palabra o Frase:", bg="#f0f0f0").pack(anchor="w")
        self.entry_word = tk.Entry(control_frame)
        self.entry_word.pack(fill=tk.X, pady=5)
        self.entry_word.bind('<Return>', lambda event: self.entry_clue.focus())

        tk.Label(control_frame, text="Pista / Descripción:", bg="#f0f0f0").pack(anchor="w")
        self.entry_clue = tk.Entry(control_frame)
        self.entry_clue.pack(fill=tk.X, pady=5)
        self.entry_clue.bind('<Return>', lambda event: self.add_word())

        btn_add = tk.Button(control_frame, text="Añadir", command=self.add_word)
        btn_add.pack(fill=tk.X, pady=5)

        # Lista y Botones de Edición
        tk.Label(control_frame, text="Lista de palabras:", bg="#f0f0f0").pack(anchor="w", pady=10)
        
        self.listbox = tk.Listbox(control_frame, height=15)
        self.listbox.pack(fill=tk.X, pady=5)

        # Frame para botones Editar/Eliminar (NUEVO)
        btn_box = tk.Frame(control_frame, bg="#f0f0f0")
        btn_box.pack(fill=tk.X, pady=5)

        btn_edit = tk.Button(btn_box, text="Editar", command=self.edit_word)
        btn_edit.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        btn_del = tk.Button(btn_box, text="Eliminar", command=self.delete_word, bg="#ffdddd")
        btn_del.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        # Botones de Acción Principal
        tk.Frame(control_frame, height=20, bg="#f0f0f0").pack() # Espaciador visual

        btn_generate = tk.Button(control_frame, text="GENERAR CRUCIGRAMA", 
                               bg="#4caf50", fg="white", font=("Arial", 10, "bold"),
                               command=self.generate_crossword)
        btn_generate.pack(fill=tk.X, pady=10)

        # Opciones de Exportación
        format_frame = tk.LabelFrame(control_frame, text="Formato de exportación", bg="#f0f0f0")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.var_png = tk.BooleanVar(value=True)
        self.var_svg = tk.BooleanVar(value=False)
        
        tk.Checkbutton(format_frame, text="PNG", variable=self.var_png, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(format_frame, text="SVG", variable=self.var_svg, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(control_frame, text="Guardar Imágenes", command=self.save_images)
        btn_save.pack(fill=tk.X, pady=5)

        # --- Panel Derecho (Preview) ---
        preview_frame = tk.Frame(self.root, bg="white")
        preview_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(preview_frame, bg="white")
        scroll_x = tk.Scrollbar(preview_frame, orient="horizontal", command=self.canvas.xview)
        scroll_y = tk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # --- LÓGICA DE GESTIÓN DE PALABRAS ---

    def _add_single_word(self, word, clue=""):
        """Método auxiliar interno para añadir una palabra limpia a la lista."""
        word = word.upper().strip()
        clue = clue.strip()
        
        # Check duplication based on word only
        for item in self.word_list:
            if item['word'] == word:
                return False

        if word:
            self.word_list.append({'word': word, 'clue': clue})
            display_text = f"{word}: {clue}" if clue else word
            self.listbox.insert(tk.END, display_text)
            return True
        return False

    def add_word(self):
        raw_text = self.entry_word.get()
        raw_clue = self.entry_clue.get()
        
        # Validar si está vacío
        if not raw_text.strip():
            return

        # VALIDACIÓN 1: Solo letras y espacios en la palabra
        # Eliminamos espacios para verificar si el resto son letras
        if not raw_text.replace(" ", "").isalpha():
            messagebox.showerror("Error", "Ingrese una palabra u oración solo con letras y espacios")
            return

        # VALIDACIÓN 2: La pista no puede estar vacía
        if not raw_clue.strip():
             messagebox.showerror("Error", "Por favor, inserte una descripción válida para la palabra introducida")
             return

        # 1. Detectar si hay espacios (es una frase o varias palabras)
        if " " in raw_text:
            answer = messagebox.askyesnocancel(
                "Espacios detectados", 
                f"Has escrito '{raw_text}'. ¿Qué deseas hacer?\n\n"
                "• Sí: Unir todo (ej: HOLAMUNDO)\n"
                "• No: Separar en palabras (ej: HOLA, MUNDO)\n"
                "• Cancelar: No añadir nada"
            )

            if answer is None: # Cancelar
                return 
            
            if answer: # True -> Concatenar
                final_word = raw_text.replace(" ", "")
                if self._add_single_word(final_word, raw_clue):
                    self.entry_word.delete(0, tk.END)
                    self.entry_clue.delete(0, tk.END)
            
            else: # False -> Separar
                words = raw_text.split()
                added_any = False
                for w in words:
                    # Loop para pedir descripción obligatoria para cada palabra
                    while True:
                        new_clue = simpledialog.askstring("Descripción requerida", f"Ingrese la pista para la palabra '{w}':")
                        if new_clue is None: 
                            # Cancelar (Usuario le dio a Cancel o cerró ventana)
                            break 
                        
                        if not new_clue.strip():
                             messagebox.showerror("Error", "Por favor, inserte una descripción válida para la palabra introducida")
                             continue
                        
                        # Si es válido, intentamos añadir
                        if self._add_single_word(w, new_clue):
                            added_any = True
                        break # Salimos del while de esta palabra

                if added_any:
                    self.entry_word.delete(0, tk.END)
                    self.entry_clue.delete(0, tk.END)

        else:
            # 2. Caso normal (una sola palabra)
            if self._add_single_word(raw_text, raw_clue):
                self.entry_word.delete(0, tk.END)
                self.entry_clue.delete(0, tk.END)
                self.entry_word.focus()
            else:
                messagebox.showwarning("Duplicado", "Esa palabra ya está en la lista o está vacía.")

    def delete_word(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Atención", "Selecciona una palabra para eliminar.")
            return

        index = selection[0]
        # Eliminamos por índice para mantener sincronía
        del self.word_list[index]
        self.listbox.delete(index)

    def edit_word(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Atención", "Selecciona una palabra para editar.")
            return

        index = selection[0]
        item = self.word_list[index] # es un dict {'word': '...', 'clue': '...'}
        
        # Eliminamos de la lista
        del self.word_list[index]
        self.listbox.delete(index)
        
        self.entry_word.delete(0, tk.END)
        self.entry_word.insert(0, item['word'])
        
        self.entry_clue.delete(0, tk.END)
        self.entry_clue.insert(0, item.get('clue', ''))
        
        self.entry_word.focus()

    # --- LÓGICA DE GENERACIÓN Y DIBUJO ---

    def generate_crossword(self):
        if not self.word_list:
            messagebox.showerror("Error", "Añade al menos una palabra.")
            return

        # --- LÓGICA DE TAMAÑO DINÁMICO ---
        # Calculamos un tamaño seguro:
        # 1. Tomamos 50 como base mínima.
        # 2. Sumamos (número de palabras * 5) para dar espacio si hay muchas.
        # 3. Nos aseguramos de cubrir la palabra más larga multiplicada por 2.
        
        num_words = len(self.word_list)
        max_len = max(len(w) for w in self.word_list) if self.word_list else 0
        
        dynamic_size = max(50, num_words * 5, max_len * 3)
        
        # Instanciamos pasando solo las strings
        words_only = [item['word'] for item in self.word_list]
        self.generator = CrosswordGenerator(words_only, grid_size=dynamic_size)
        # ---------------------------------
        
        self.generator.generate()
        
        if not self.generator.placed_words:
            messagebox.showinfo("Resultado", "No se pudo colocar ninguna palabra (incluso con grid ampliado). Intenta simplificar la lista.")
            return
            
        self._draw_on_canvas()

    def _get_grid_bounds(self):
        grid = self.generator.grid
        size = self.generator.grid_size
        min_r, max_r = size, 0
        min_c, max_c = size, 0

        has_content = False
        for r in range(size):
            for c in range(size):
                if grid[r][c] != ' ':
                    has_content = True
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)
        
        if not has_content:
            return 0, 0, 0, 0
        return min_r, max_r, min_c, max_c

    def _draw_on_canvas(self):
        self.canvas.delete("all")
        grid = self.generator.grid
        min_r, max_r, min_c, max_c = self._get_grid_bounds()
        padding = 1 
        
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                char = grid[r][c]
                if char != ' ':
                    x = (c - min_c + padding) * self.cell_size
                    y = (r - min_r + padding) * self.cell_size
                    
                    self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size, fill="white", outline="black")
                    self.canvas.create_text(x + self.cell_size/2, y + self.cell_size/2 + 8, text=char, font=("Arial", 20, "bold"))
                    if (r, c) in self.generator.start_locations:
                        num = self.generator.start_locations[(r, c)]
                        # Lo dibujamos con un poco más de margen de la esquina
                        self.canvas.create_text(x + 15, y + 15, text=str(num), font=("Arial", 9), fill="black")
        
        total_w = (max_c - min_c + 2 * padding + 1) * self.cell_size
        total_h = (max_r - min_r + 2 * padding + 1) * self.cell_size
        self.canvas.configure(scrollregion=(0, 0, total_w, total_h))

    def save_images(self):
        if not self.generator or not self.generator.placed_words:
            messagebox.showwarning("Alerta", "Primero genera el crucigrama.")
            return
            
        if not self.var_png.get() and not self.var_svg.get():
             messagebox.showwarning("Alerta", "Selecciona al menos un formato de exportación.")
             return

        min_r, max_r, min_c, max_c = self._get_grid_bounds()
        rows = max_r - min_r + 3 
        cols = max_c - min_c + 3
        
        # Preparar pistas separadas
        word_to_clue = {item['word']: item.get('clue', '') for item in self.word_list}
        clues_horz = []
        clues_vert = []
        
        for word, row, col, direction in self.generator.placed_words:
            if (row, col) in self.generator.start_locations:
                num = self.generator.start_locations[(row, col)]
                clue_txt = word_to_clue.get(word, '')
                line = f"{num}. {clue_txt}"
                
                if direction == 'horizontal':
                    clues_horz.append((num, line))
                else:
                    clues_vert.append((num, line))
        
        # Ordenar cada lista por número
        clues_horz.sort(key=lambda x: x[0])
        clues_vert.sort(key=lambda x: x[0])
        
        list_horz = [x[1] for x in clues_horz]
        list_vert = [x[1] for x in clues_vert]
        
        # FACTOR DE ESCALA (Reducir 20%)
        SCALE = 0.8
        
        # Dimensiones base (antes de escalar)
        base_w = max(cols * self.cell_size, 800)
        grid_h = rows * self.cell_size
        
        # Calcular altura extra para texto (aprox)
        max_items = max(len(list_horz), len(list_vert))
        # Ajustamos alturas base
        clues_h = 60 + 40 + (max_items * 30) + 50 
        base_h = grid_h + clues_h

        # Aplicar escala
        scaled_w = int(base_w * SCALE)
        scaled_h = int(base_h * SCALE)
        scaled_grid_h = int(grid_h * SCALE)
        scaled_cell = int(self.cell_size * SCALE)

        if self.var_png.get():
            self._create_image_file(scaled_w, scaled_h, min_r, min_c, True, "crucigrama_resuelto.png", 
                                    list_horz, list_vert, scaled_grid_h, scaled_cell)
            self._create_image_file(scaled_w, scaled_h, min_r, min_c, False, "crucigrama_vacio.png", 
                                    list_horz, list_vert, scaled_grid_h, scaled_cell)

        if self.var_svg.get():
            self._create_svg_file(scaled_w, scaled_h, min_r, min_c, True, "crucigrama_resuelto.svg", 
                                  list_horz, list_vert, scaled_grid_h, scaled_cell)
            self._create_svg_file(scaled_w, scaled_h, min_r, min_c, False, "crucigrama_vacio.svg", 
                                  list_horz, list_vert, scaled_grid_h, scaled_cell)
        
        messagebox.showinfo("Éxito", "Imágenes guardadas correctamente.")

    def resource_path(self, relative_path):
        """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
        try:
            # PyInstaller crea una carpeta temporal en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def _get_font(self, size):
        """Intenta cargar una fuente que soporte tildes, buscando también en recursos empaquetados."""
        
        # 1. Intentar cargar fuente empaquetada (si existiera en la raiz del ejecutable)
        try:
            local_font = self.resource_path("DejaVuSans.ttf")
            return ImageFont.truetype(local_font, size)
        except IOError:
            pass

        # 2. Fuentes del sistema
        font_names = [
            "DejaVuSans.ttf", 
            "Arial.ttf", 
            "LiberationSans-Regular.ttf",
            "FreeSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        ]
        
        for font_path in font_names:
            try:
                return ImageFont.truetype(font_path, size)
            except IOError:
                continue
        
        # Fallback
        return ImageFont.load_default()

    def _create_image_file(self, width, height, offset_r, offset_c, with_letters, filename, c_horz=[], c_vert=[], grid_h=0, cell_size=60):
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        
        # Cargar Fuentes Escaladas (~80% de las originales: 32->26, 14->11, 28->22, 20->16, 16->13)
        font_main = self._get_font(26)
        font_small = self._get_font(11)
        font_title = self._get_font(22)
        font_subtitle = self._get_font(16)
        font_item = self._get_font(13)

        grid = self.generator.grid
        start_r, end_r, start_c, end_c = self._get_grid_bounds()
        padding = 1 
        
        # Centrar el grid en la imagen
        grid_width_pixels = (end_c - start_c + 1 + 2) * cell_size
        start_draw_x = (width - grid_width_pixels) // 2
        if start_draw_x < 0: start_draw_x = 0

        # 1. Dibujar Grid
        for r in range(start_r, end_r + 1):
            for c in range(start_c, end_c + 1):
                char = grid[r][c]
                if char != ' ':
                    col_idx = c - offset_c
                    row_idx = r - offset_r
                    
                    x0 = start_draw_x + (col_idx + padding) * cell_size
                    y0 = (row_idx + padding) * cell_size
                    x1 = x0 + cell_size
                    y1 = y0 + cell_size
                    
                    # Dibujar cuadro
                    draw.rectangle([x0, y0, x1, y1], outline="black", width=2)
                    
                    # Dibujar número
                    if (r, c) in self.generator.start_locations:
                        num = str(self.generator.start_locations[(r, c)])
                        draw.text((x0 + (cell_size * 0.15), y0 + (cell_size * 0.15)), num, fill="black", font=font_small)

                    # Dibujar letra
                    if with_letters:
                        # Centrado aproximado
                        draw.text((x0 + (cell_size * 0.35), y0 + (cell_size * 0.25)), char, fill="black", font=font_main)

        # 2. Dibujar Pistas en Columnas
        if c_horz or c_vert:
            y = grid_h + 20
            
            # Título Principal
            title_text = "PISTAS"
            bbox = draw.textbbox((0, 0), title_text, font=font_title)
            w_text = bbox[2] - bbox[0]
            draw.text(((width - w_text)/2, y), title_text, fill="black", font=font_title)
            
            y += 40
            col_width = width // 2
            
            # Columna Horizontal
            draw.text((20, y), "HORIZONTALES", fill="black", font=font_subtitle)
            y_cursor = y + 30
            for line in c_horz:
                draw.text((20, y_cursor), line, fill="black", font=font_item)
                y_cursor += 20
                
            # Columna Vertical
            draw.text((col_width + 20, y), "VERTICALES", fill="black", font=font_subtitle)
            y_cursor = y + 30
            for line in c_vert:
                draw.text((col_width + 20, y_cursor), line, fill="black", font=font_item)
                y_cursor += 20

        image.save(filename)

    def _create_svg_file(self, width, height, offset_r, offset_c, with_letters, filename, c_horz=[], c_vert=[], grid_h=0, cell_size=60):
        # Generar contenido SVG manualmente
        svg_content = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
        svg_content.append(f'<rect width="100%" height="100%" fill="white"/>')
        
        # Estilos CSS básicos para fuentes
        svg_content.append('<style>')
        svg_content.append('.txt-main { font-family: sans-serif; font-size: 26px; font-weight: bold; anchor: middle; }')
        svg_content.append('.txt-small { font-family: sans-serif; font-size: 11px; }')
        svg_content.append('.txt-title { font-family: sans-serif; font-size: 22px; font-weight: bold; }')
        svg_content.append('.txt-subtitle { font-family: sans-serif; font-size: 16px; font-weight: bold; }')
        svg_content.append('.txt-item { font-family: sans-serif; font-size: 13px; }')
        svg_content.append('</style>')

        grid = self.generator.grid
        start_r, end_r, start_c, end_c = self._get_grid_bounds()
        padding = 1 

        grid_width_pixels = (end_c - start_c + 1 + 2) * cell_size
        start_draw_x = (width - grid_width_pixels) // 2
        if start_draw_x < 0: start_draw_x = 0

        # 1. Dibujar Grid
        for r in range(start_r, end_r + 1):
            for c in range(start_c, end_c + 1):
                char = grid[r][c]
                if char != ' ':
                    col_idx = c - offset_c
                    row_idx = r - offset_r
                    
                    x0 = start_draw_x + (col_idx + padding) * cell_size
                    y0 = (row_idx + padding) * cell_size
                    
                    # Rectángulo
                    svg_content.append(f'<rect x="{x0}" y="{y0}" width="{cell_size}" height="{cell_size}" fill="white" stroke="black" stroke-width="2"/>')
                    
                    # Número
                    if (r, c) in self.generator.start_locations:
                        num = str(self.generator.start_locations[(r, c)])
                        nx = x0 + (cell_size * 0.15)
                        ny = y0 + (cell_size * 0.25) 
                        svg_content.append(f'<text x="{nx}" y="{ny}" class="txt-small" fill="black">{num}</text>')

                    # Letra
                    if with_letters:
                        lx = x0 + (cell_size * 0.5) 
                        ly = y0 + (cell_size * 0.7)
                        svg_content.append(f'<text x="{lx}" y="{ly}" class="txt-main" text-anchor="middle" fill="black">{char}</text>')

        # 2. Dibujar Pistas
        if c_horz or c_vert:
            y = grid_h + 30 
            # Título
            svg_content.append(f'<text x="{width/2}" y="{y}" class="txt-title" text-anchor="middle" fill="black">PISTAS</text>')
            
            y += 40
            col_width = width // 2
            
            # Horizontal (Left)
            svg_content.append(f'<text x="20" y="{y}" class="txt-subtitle" fill="black">HORIZONTALES</text>')
            y_cursor = y + 30
            for line in c_horz:
                # Escapar caracteres HTML básicos si fuera necesario
                clean_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                svg_content.append(f'<text x="20" y="{y_cursor}" class="txt-item" fill="black">{clean_line}</text>')
                y_cursor += 20
                
            # Vertical (Right)
            svg_content.append(f'<text x="{col_width + 20}" y="{y}" class="txt-subtitle" fill="black">VERTICALES</text>')
            y_cursor = y + 30
            for line in c_vert:
                clean_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                svg_content.append(f'<text x="{col_width + 20}" y="{y_cursor}" class="txt-item" fill="black">{clean_line}</text>')
                y_cursor += 20

        svg_content.append('</svg>')
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_content))

if __name__ == "__main__":
    root = tk.Tk()
    app = CrosswordGUI(root)
    root.mainloop()