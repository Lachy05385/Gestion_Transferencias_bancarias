import re








# Versión con expresión regular única (más eficiente)
def procesar_transferencia_sin_ordenante(mensaje):
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
    print('='*50)
    print(match)
    print('='*50)
    if match:
        resultado["beneficiario"] = match.group(1)
        resultado["monto"] = float(match.group(2))
        resultado["moneda"] = match.group(3).upper()
        resultado["numero_transaccion"] = match.group(4)
        resultado["fecha"] = match.group(5)
    
    return resultado

# Ejemplo de uso
mensaje = "Se ha realizado una transferencia a la cuenta 9205129970539210 de 660.00 CUP.Nro. Transaccion BR600KHGA4997. Fecha: 24/4/2026."


print("\n=== Versión con regex único ===")
resultado3 = procesar_transferencia_sin_ordenante(mensaje)
print(resultado3)