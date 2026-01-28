import random

class CrosswordGenerator:
    def __init__(self, words, grid_size = 100):
        self.words = [w.upper() for w in words]
        self.grid_size = grid_size  # Start with a reasonably large grid
        self.grid = [[' ' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        self.start_locations = {}

    def generate(self):
        # Sort words by length descending
        sorted_words = sorted(self.words, key=len, reverse=True)
        
        if not sorted_words:
            return

        # Place the first word in the middle
        first_word = sorted_words[0]
        start_row = self.grid_size // 2
        start_col = (self.grid_size - len(first_word)) // 2
        
        if not self._place_word_at(first_word, start_row, start_col, 'horizontal'):
             return 

        # Try to place rest of the words
        for word in sorted_words[1:]:
             self._place_next_word(word)
        self._calculate_clue_numbers()

    def _calculate_clue_numbers(self):
        """Asigna números a las celdas de inicio en orden de lectura (arriba-abajo, izq-der)."""
        # 1. Obtenemos todas las palabras colocadas
        # self.placed_words tiene tuplas: (word, row, col, direction)
        
        # 2. Ordenamos por fila y luego por columna para que los números vayan en orden natural
        sorted_placed = sorted(self.placed_words, key=lambda x: (x[1], x[2]))
        
        current_number = 1
        self.start_locations = {} # Reiniciar

        for _, row, col, _ in sorted_placed:
            # Si esta casilla ya tiene número (cruce de dos inicios), no asignamos uno nuevo
            if (row, col) not in self.start_locations:
                self.start_locations[(row, col)] = current_number
                current_number += 1

    def _place_next_word(self, word):
        # Shuffle placed words to vary the layout if possible
        # Since we just iterate, maybe randomizing the order of checking placed words
        # helps distribution, though for deterministic output we might remove shuffle.
        current_placed = list(self.placed_words)
        # random.shuffle(current_placed) 
        
        for p_word, p_row, p_col, p_dir in current_placed:
            # Check intersections
            intersect_indices = self._find_intersections(word, p_word)
            
            for i_char, j_char in intersect_indices:
                # i_char is index in new 'word'
                # j_char is index in placed 'p_word'
                
                # If placed word is horizontal, new word must be vertical
                if p_dir == 'horizontal':
                    new_dir = 'vertical'
                    new_row = p_row - i_char
                    new_col = p_col + j_char
                else:
                    new_dir = 'horizontal'
                    new_row = p_row + j_char
                    new_col = p_col - i_char
                    
                if self._can_place(word, new_row, new_col, new_dir):
                    self._place_word_at(word, new_row, new_col, new_dir)
                    return 
                    
    def _find_intersections(self, word1, word2):
        intersections = []
        for i, char1 in enumerate(word1):
            for j, char2 in enumerate(word2):
                if char1 == char2:
                    intersections.append((i, j))
        return intersections

    def _can_place(self, word, row, col, direction):
        if row < 0 or row >= self.grid_size or col < 0 or col >= self.grid_size:
            return False
            
        if direction == 'horizontal':
            if col + len(word) > self.grid_size: return False
            # Check immediate limits (before and after)
            if col - 1 >= 0 and self.grid[row][col-1] != ' ': return False
            if col + len(word) < self.grid_size and self.grid[row][col+len(word)] != ' ': return False
            
            for i in range(len(word)):
                r, c = row, col + i
                # Check for conflict
                if self.grid[r][c] != ' ' and self.grid[r][c] != word[i]:
                    return False
                
                # Check neighbors (above and below)
                # We only need to check neighbors if the cell we are placing on is currently empty.
                # If it's an intersection (not empty), neighbors are allowed (it's the crossing word).
                if self.grid[r][c] == ' ':
                    if r - 1 >= 0 and self.grid[r-1][c] != ' ': return False
                    if r + 1 < self.grid_size and self.grid[r+1][c] != ' ': return False

        else: # vertical
            if row + len(word) > self.grid_size: return False
            # Check immediate limits
            if row - 1 >= 0 and self.grid[row-1][col] != ' ': return False
            if row + len(word) < self.grid_size and self.grid[row+len(word)][col] != ' ': return False

            for i in range(len(word)):
                r, c = row + i, col
                # Check for conflict
                if self.grid[r][c] != ' ' and self.grid[r][c] != word[i]:
                    return False
                
                # Check neighbors (left and right)
                if self.grid[r][c] == ' ':
                    if c - 1 >= 0 and self.grid[r][c-1] != ' ': return False
                    if c + 1 < self.grid_size and self.grid[r][c+1] != ' ': return False
        
        return True

    def _place_word_at(self, word, row, col, direction):
        self.placed_words.append((word, row, col, direction))
        chars = self._slice_word(word)
        if direction == 'horizontal':
            for i, char in enumerate(chars):
                self.grid[row][col + i] = char
        else:
            for i, char in enumerate(chars):
                self.grid[row + i][col] = char
        return True

    def _slice_word(self, word):
        """Explicitly slice word into characters."""
        return list(word)

    def display(self):
        # Find bounds to print only the relevant part
        if not self.placed_words:
            print("Empty Grid")
            return

        min_r, max_r = self.grid_size, 0
        min_c, max_c = self.grid_size, 0

        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] != ' ':
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)
        
        # Add a little padding
        min_r = max(0, min_r - 1)
        max_r = min(self.grid_size - 1, max_r + 1)
        min_c = max(0, min_c - 1)
        max_c = min(self.grid_size - 1, max_c + 1)

        print("-" * ((max_c - min_c + 1) * 2 + 3))
        for r in range(min_r, max_r + 1):
            row_str = ""
            for c in range(min_c, max_c + 1):
                row_str += self.grid[r][c] + " "
            print(f"| {row_str}|")
        print("-" * ((max_c - min_c + 1) * 2 + 3))

if __name__ == "__main__":
    words = ["PYTHON", "JAVA", "PROGRAMMING", "ALGORITHM", "CODING", "DEBUG", "SYNTAX", "COMPUTER", "LINTING", "COMPILE", "AGILE", "SCRUM"]
    print(f"Generating crossword with {len(words)} words...")
    cg = CrosswordGenerator(words)
    cg.generate()
    cg.display()
    print(f"Placed {len(cg.placed_words)} out of {len(words)} words.")