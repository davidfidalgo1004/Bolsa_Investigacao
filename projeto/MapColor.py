def EncontrarCor(pcolor_value):
    if pcolor_value == 85:
        return "#2F4F4F"   # Estrada: cinza escuro
    if pcolor_value == 95:
        return "#1E90FF"   # Rio: azul
    if (pcolor_value % 10) == 9:
        return "#FFFFFF"   # Branco
    elif 1 <= pcolor_value < 9:
        return "#808080"   # Cinzento
    elif 11 <= pcolor_value < 19:
        return "#FF0000"   # Vermelho
    elif 21 <= pcolor_value < 29:
        return "#FFA500"   # Laranja
    elif 31 <= pcolor_value < 39:
        return "#8B4513"   # Castanho
    elif 41 <= pcolor_value < 49:
        return "#FFFF00"   # Amarelo
    elif 51 <= pcolor_value < 59 or 61 <= pcolor_value < 80:
        if pcolor_value == 55:
            return "#006400"   # Verde (floresta)
        else:
            return "#32CD32"
    elif 81 <= pcolor_value < 89 or 91 <= pcolor_value < 99:
        return "#00FF00"
    else:
        return "#000000"   # Preto
