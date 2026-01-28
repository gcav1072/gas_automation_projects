class CifradoVigenere:
    """Clase para manejar el cifrado Vigenère con alfabeto español."""
    
    ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
    LONG_ALFABETO = 27
    
    @classmethod
    def _validar_entrada(cls, texto: str, clave: str):
        if not isinstance(texto, str) or not isinstance(clave, str):
            raise TypeError("Texto y clave deben ser cadenas")
        if not clave:
            raise ValueError("La clave no puede estar vacía")
        if not any(c.isalpha() for c in clave):
            raise ValueError("La clave debe contener al menos una letra")
    
    @classmethod
    def cifrar(cls, texto: str, clave: str) -> str:
        """Cifra un texto usando Vigenère."""
        return cls._procesar(texto, clave, cifrar=True)
    
    @classmethod
    def descifrar(cls, texto: str, clave: str) -> str:
        """Descifra un texto cifrado con Vigenère."""
        return cls._procesar(texto, clave, cifrar=False)
    
    @classmethod
    def _procesar(cls, texto: str, clave: str, cifrar: bool) -> str:
        cls._validar_entrada(texto, clave)
        
        # Filtrar y normalizar clave
        clave_chars = [c.upper() for c in clave if c.isalpha()]
        clave_len = len(clave_chars)
        
        resultado = []
        clave_idx = 0
        
        for char in texto:
            if char.isalpha():
                # Preservar caso original
                es_minuscula = char.islower()
                char_upper = char.upper()
                
                if char_upper not in cls.ALFABETO:
                    resultado.append(char)
                    continue
                
                # Obtener índices
                idx_texto = cls.ALFABETO.index(char_upper)
                idx_clave = cls.ALFABETO.index(clave_chars[clave_idx % clave_len])
                clave_idx += 1
                
                # Aplicar operación
                if cifrar:
                    nuevo_idx = (idx_texto + idx_clave) % cls.LONG_ALFABETO
                else:
                    nuevo_idx = (idx_texto - idx_clave) % cls.LONG_ALFABETO
                
                # Convertir de vuelta a carácter
                nuevo_char = cls.ALFABETO[nuevo_idx]
                resultado.append(nuevo_char.lower() if es_minuscula else nuevo_char)
            else:
                resultado.append(char)
        
        return ''.join(resultado)

# Uso
cifrado = CifradoVigenere.cifrar("Quiero alguien que me que me quiera y sea plana xd :3", "gorgojo")
descifrado = CifradoVigenere.descifrar(cifrado, "gorgojo")
print(cifrado)
print(descifrado)