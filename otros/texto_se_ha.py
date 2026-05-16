import re

def procesar_transferencia_sin_titular(mensaje):
    resultado = {
        "banco": "",
        "fecha": "",
        "beneficiario": "",
        "ordenante": "",
        "monto": 0.0,
        "moneda": "CUP",
        "numero_transaccion": "",
        "concepto": ""
    }
    
    # Extraer cuenta del beneficiario
    # Patrón: "a la cuenta XXXXXXXXXXXXXX"
    cuenta_match = re.search(r'a\s+la\s+cuenta\s+(\d+)', mensaje, re.IGNORECASE)
    if cuenta_match:
        resultado["beneficiario"] = cuenta_match.group(1)
    
    # Extraer monto y moneda
    # Patrón: "de 660.00 CUP" o "de 660.00CUP" (sin espacio)
    monto_match = re.search(r'de\s+([0-9.]+)\s*([A-Z]{3})', mensaje, re.IGNORECASE)
    if monto_match:
        resultado["monto"] = float(monto_match.group(1))
        resultado["moneda"] = monto_match.group(2).upper()
    
    # Extraer número de transacción
    # Patrón: "Nro. Transaccion XXXXXXXX"
    transaccion_match = re.search(r'Nro\.?\s*Transaccion\s+([A-Z0-9]+)', mensaje, re.IGNORECASE)
    if transaccion_match:
        resultado["numero_transaccion"] = transaccion_match.group(1)
    
    # Extraer fecha
    # Patrón: "Fecha: 24/4/2026"
    fecha_match = re.search(r'Fecha:\s*([0-9/]+)', mensaje, re.IGNORECASE)
    if fecha_match:
        resultado["fecha"] = fecha_match.group(1)
    
    # Campos que no están disponibles en este formato
    resultado["banco"] = "Transferencia"
    resultado["ordenante"] = "****"  # Máscara porque no viene información
    resultado["concepto"] = "Transferencia recibida"
    
    return resultado


# Versión más robusta con manejo de espacios variables
def procesar_transferencia_avanzado(mensaje):
    resultado = {
        "banco": "Transferencia",
        "fecha": "",
        "beneficiario": "",
        "ordenante": "****",
        "monto": 0.0,
        "moneda": "CUP",
        "numero_transaccion": "",
        "concepto": "Transferencia recibida"
    }
    
    # Limpiar el mensaje (eliminar saltos de línea y espacios extras)
    mensaje_limpio = ' '.join(mensaje.split())
    
    # Extraer cuenta beneficiario (más flexible)
    cuenta_match = re.search(r'cuenta\s+(\d+)', mensaje_limpio, re.IGNORECASE)
    if cuenta_match:
        resultado["beneficiario"] = cuenta_match.group(1)
    
    # Extraer monto (permite decimales con o sin puntos)
    monto_match = re.search(r'de\s+([0-9]+\.?[0-9]*)\s*([A-Z]{3})', mensaje_limpio, re.IGNORECASE)
    if monto_match:
        resultado["monto"] = float(monto_match.group(1))
        resultado["moneda"] = monto_match.group(2).upper()
    
    # Extraer número de transacción (permite varios formatos)
    transaccion_match = re.search(r'Nro\.?\s*Transaccion\s+([A-Za-z0-9]+)', mensaje_limpio, re.IGNORECASE)
    if transaccion_match:
        resultado["numero_transaccion"] = transaccion_match.group(1)
    
    # Extraer fecha (permite formatos dd/m/yyyy, dd/mm/yyyy)
    fecha_match = re.search(r'Fecha:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', mensaje_limpio, re.IGNORECASE)
    if fecha_match:
        resultado["fecha"] = fecha_match.group(1)
    
    return resultado


# Versión con expresión regular única (más eficiente)
def procesar_transferencia_regex_unico(mensaje):
    """
    Usa una sola expresión regular para extraer todos los datos
    """
    resultado = {
        "banco": "Transferencia",
        "fecha": "",
        "beneficiario": "",
        "ordenante": "****",
        "monto": 0.0,
        "moneda": "CUP",
        "numero_transaccion": "",
        "concepto": "Transferencia recibida"
    }
    
    # Patrón único que captura todos los campos
    patron = r'cuenta\s+(\d+).*?de\s+([0-9.]+)\s*([A-Z]{3}).*?Nro\.?\s*Transaccion\s+([A-Za-z0-9]+).*?Fecha:\s*([0-9/]+)'
    
    match = re.search(patron, mensaje, re.IGNORECASE | re.DOTALL)
    if match:
        resultado["beneficiario"] = match.group(1)
        resultado["monto"] = float(match.group(2))
        resultado["moneda"] = match.group(3).upper()
        resultado["numero_transaccion"] = match.group(4)
        resultado["fecha"] = match.group(5)
    
    return resultado


# Función para validar si el mensaje tiene este formato específico
def es_formato_transferencia_sin_titular(mensaje):
    """
    Valida si el mensaje coincide con el formato:
    "Se ha realizado una transferencia a la cuenta X de Y CUP. Nro. Transaccion Z. Fecha: W"
    """
    patron = r'Se ha realizado una transferencia a la cuenta \d+ de [\d.]+ [A-Z]{3}\. Nro\.?\s*Transaccion [A-Za-z0-9]+\. Fecha: [\d/]+\.'
    return bool(re.search(patron, mensaje, re.IGNORECASE))


# Ejemplo de uso
mensaje = "Se ha realizado una transferencia a la cuenta 9205129970539210 de 660.00 CUP.Nro. Transaccion BR600KHGA4997. Fecha: 24/4/2026."

print("=== Versión básica ===")
resultado1 = procesar_transferencia_sin_titular(mensaje)
print(resultado1)

print("\n=== Versión avanzada ===")
resultado2 = procesar_transferencia_avanzado(mensaje)
print(resultado2)

print("\n=== Versión con regex único ===")
resultado3 = procesar_transferencia_regex_unico(mensaje)
print(resultado3)

print("\n=== Validación de formato ===")
print(f"¿Es formato válido? {es_formato_transferencia_sin_titular(mensaje)}")









mensaje3 = "Se ha realizado una transferencia a la cuenta 9205129970539210 de 660.00 CUP.Nro. Transaccion BR600KHGA4997. Fecha: 24/4/2026."


print(texto_se_ha_realizado(mennsaje3))