from datetime import datetime
import re


def procesar_mensaje_enzona_avanzado(mensaje):
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
    
    # Extraer banco
    banco_match = re.search(r'^(ENZONA)', mensaje, re.IGNORECASE)
    print(banco_match)
    
    
    if banco_match:
        resultado["banco"] = banco_match.group(1).upper()
    
    # Extraer importe y moneda (más flexible)
    # Patrones posibles: "Importe: 131.00 CUP" o "Importe:6000.00 CUP"
    importe_match = re.search(r'Importe:\s*([0-9]+\.?[0-9]*)\s*([A-Z]{3})', mensaje, re.IGNORECASE)
    
    if importe_match:
        resultado["monto"] = float(importe_match.group(1))
        resultado["moneda"] = importe_match.group(2).upper()
    
    # Extraer número de transacción (más flexible)
    # Patrones posibles: "No.: 3AAyFSEr5zCP" o "No.: btW3BGhGpnEH"
    transaccion_match = re.search(r'No\.:\s*([A-Za-z0-9]+)', mensaje)
    if transaccion_match:
        resultado["numero_transaccion"] = transaccion_match.group(1)
    
    # Extraer tipo de operación y asignar a concepto
    tipo_match = re.search(r'ENZONA\s+(pago recibido|transferencia recibida)', mensaje, re.IGNORECASE)
    if tipo_match:
        tipo = tipo_match.group(1).lower()
        if tipo == "pago recibido":
            resultado["concepto"] = "Pago recibido"
        elif tipo == "transferencia recibida":
            resultado["concepto"] = "Transferencia recibida"
    
    # Asignar máscara a campos faltantes
    resultado["fecha"] = get_Fecha_inexistente()
    resultado["beneficiario"] = "xxxx-xxxx-xxxx-xxxx"
    resultado["ordenante"] = "xxxx-xxxx-xxxx-xxxx"
    
    return resultado
def get_Fecha_inexistente():
    fecha_actual = datetime.now()
    fecha_formateada = fecha_actual.strftime("%d/%m/%Y")
    
    return fecha_formateada 

mensaje1 = "ENZONA pago recibido, Importe: 131.00 CUP No.: 3AAyFSEr5zCP"
mensaje2 = "ENZONA transferencia recibida Importe: 6000.00 CUP No.: btW3BGhGpnEH"

print(procesar_mensaje_enzona_avanzado(mensaje2))