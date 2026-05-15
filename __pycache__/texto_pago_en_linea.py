import re

def procesar_mensaje_plinea(mensaje):
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
    
    # Extraer banco (primeras palabras antes de ":")
    banco_match = re.search(r'^([^:]+):', mensaje)
    if banco_match:
        resultado["banco"] = banco_match.group(1).strip()
    
    # Extraer fecha
    fecha_match = re.search(r'Fecha:\s*([0-9/]+)', mensaje)
    if fecha_match:
        resultado["fecha"] = fecha_match.group(1).strip()
    
    # Extraer entidad y ponerla en beneficiario (máximo 12 caracteres)
    entidad_match = re.search(r'Entidad:\s*([^\n]+)', mensaje)
    if entidad_match:
        entidad = entidad_match.group(1).strip()
        # Limitar a 12 caracteres
        resultado["beneficiario"] = entidad[-12:]
    
    # Extraer ID de compra y ponerla en ordenante
    id_compra_match = re.search(r'Id Compra:\s*([0-9]+)', mensaje)
    if id_compra_match:
        resultado["ordenante"] = id_compra_match.group(1).strip()
    
    # Extraer importe (solo el primer Importe, no el Importe Pagado)
    importe_match = re.search(r'Importe:\s*([0-9.]+)\s*([A-Z]+)', mensaje)
    if importe_match:
        resultado["monto"] = float(importe_match.group(1))
        resultado["moneda"] = importe_match.group(2)
    
    # Extraer número de transacción
    transaccion_match = re.search(r'Nro\.?\s*Transaccion:\s*([^\n\.]+)', mensaje, re.IGNORECASE)
    if transaccion_match:
        resultado["numero_transaccion"] = transaccion_match.group(1).strip()
    
    return resultado

def contiene_texto(txt:str):
    patron_p_linea = r'^(?!.*ordenante).*Id Compra:.*$'
    
    return bool(re.search(patron_p_linea, mensaje, re.IGNORECASE | re.DOTALL))


# Ejemplo de uso
mensaje = ["""Banco Popular de Ahorro: Pago completado. 
    Fecha: 13/3/2026 
    Entidad: Lazaro AlbertoSaavedraGomez(Photo Laz 
    Id Compra: 5710140502 
    Importe: 100.00 CUP 
    Importe Pagado: 94.00 CUP 
    Nro. Transaccion: BR600CUUQU997."""
    , """Banco Bandec: Pago completado. 
    Fecha: 23/3/2026 
    Entidad: UEB LA IDEAL  (UEB LA IDEAL) 
    Id Compra: 7276400592 
    Importe: 560.00 CUP 
    Importe Pagado: 526.40 CUP 
    Nro. Transaccion: KW600KTOF6999."""]

for i in mensaje:
    resultado = procesar_mensaje_plinea(i)
    print(resultado)


resultado = contiene_texto(mensaje[0])
print(resultado)