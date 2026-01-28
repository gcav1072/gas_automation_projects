def map_letras(char: str) -> int:
    "Transforma una letra mayúscula a un número del 0 al 27"
    if not isinstance(char, str):
        raise TypeError("La cadena de texto solo debe tener caracteres alfabéticos")
    char_num = ord(char)
    if char_num == 209:
        return 14
    elif char_num in range(65, 79):
        return char_num - 65
    elif char_num in range(79,91):
        return char_num - 64
    else:
        raise ValueError("La cadena de texto solo debe tener caracteres alfabéticos")

def inv_map_letras(num: int) -> str:
    "Transforma un número del 0 al 26 a una letra mayúscula del alfabeto español"
    if not isinstance(num, int):
        raise TypeError("El número debe ser un entero")
    if num == 14:
        return "Ñ"
    elif num in range(14):
        return chr(num + 65)
    elif num in range(15, 27):
        return chr(num + 64)
    else:
        raise ValueError("El número debe estar entre 0 y 26")

def vigenere_encode(text: str, key: str, reverse: bool = False) -> str:
    """Aplica el algoritmo de Vigenere para encriptar un texto."""
    #Acomodando las cadenas de texto
    if not isinstance(text, str) or not isinstance(key, str):
        raise TypeError("La cadena de texto solo debe tener caracteres alfabéticos")
    if not isinstance(reverse, bool):
        raise TypeError("El parámetro reverse debe ser un booleano")
    text = text.upper()
    key = key.upper()
    #Codificando el texto
    encoded_text = ""
    key_idx = 0
    for caracter in text:
        if caracter.isalpha():
            key_idx %= len(key)
            j = key[key_idx]
            if not reverse:
                encoded_text += inv_map_letras((map_letras(caracter) + map_letras(j)) % 27)
            else:
                encoded_text += inv_map_letras((map_letras(caracter) - map_letras(j)) % 27)
            key_idx += 1
        else:
            encoded_text += caracter
    return encoded_text