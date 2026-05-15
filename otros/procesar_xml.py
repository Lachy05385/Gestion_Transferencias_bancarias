import re
import xml.etree.ElementTree as ET

def extraer_pago_movil(texto_sms):
    """Extrae datos de mensajes de pago móvil de bancos venezolanos"""
    datos = {
        'banco': None,
        'monto': None,
        'referencia': None,
        'cedula_emisor': None,
        'telefono_emisor': None,
        'nombre_emisor': None,
        'fecha': None,
        'mensaje_original': texto_sms
    }
    
    # Limpiar el texto
    texto = texto_sms.replace('\n', ' ').strip()
    
    # Patrones comunes en pagos móviles (Venezuela)
    # Banesco:
    # "Pago Móvil recibido de CI: V12345678 por Bs. 250,00 Ref: 9876543210"
    patron_banesco = r'Pago Móvil recibido de CI:\s*([VE]?\d+)\s*por Bs\.?\s*([\d\.,]+)\s*Ref:\s*(\d+)'
    # Mercantil:
    # "Pagomovil: Bs 300,00 de 04141234567 Ref 123456"
    patron_mercantil = r'Pagomovil:\s*Bs\s*([\d\.,]+)\s*de\s*(\d{10,11})\s*Ref\s*(\d+)'
    # Provincial:
    # "Pago móvil de Bs 175,50 referencia 123456789"
    patron_provincial = r'Pago móvil de Bs\s*([\d\.,]+)\s*(?:referencia|ref\.?)\s*(\d+)'
    # Banco de Venezuela:
    # "Pago movil recibido: Bs. 100.000,00 Ref. 1234567890"
    patron_bdv = r'Pago movil recibido:\s*Bs\.?\s*([\d\.,]+)\s*Ref\.?\s*(\d+)'
    
    # Probar cada patrón
    match = re.search(patron_banesco, texto, re.IGNORECASE)
    if match:
        datos['banco'] = 'Banesco'
        datos['cedula_emisor'] = match.group(1)
        datos['monto'] = float(match.group(2).replace('.', '').replace(',', '.'))
        datos['referencia'] = match.group(3)
        return datos
    
    match = re.search(patron_mercantil, texto, re.IGNORECASE)
    if match:
        datos['banco'] = 'Mercantil'
        datos['telefono_emisor'] = match.group(2)
        datos['monto'] = float(match.group(1).replace(',', '.'))
        datos['referencia'] = match.group(3)
        return datos
    
    match = re.search(patron_provincial, texto, re.IGNORECASE)
    if match:
        datos['banco'] = 'Provincial'
        datos['monto'] = float(match.group(1).replace(',', '.'))
        datos['referencia'] = match.group(2)
        return datos
    
    match = re.search(patron_bdv, texto, re.IGNORECASE)
    if match:
        datos['banco'] = 'Banco de Venezuela'
        datos['monto'] = float(match.group(1).replace('.', '').replace(',', '.'))
        datos['referencia'] = match.group(2)
        return datos
    
    # Patrón genérico para cualquier pago móvil que contenga monto y referencia
    patron_generico = r'(?:monto|total|bs\.?)\s*:?\s*([\d\.,]+).*?(?:referencia|ref\.?|nº)\s*:?\s*(\d+)'
    match = re.search(patron_generico, texto, re.IGNORECASE)
    if match:
        datos['banco'] = 'Desconocido'
        datos['monto'] = float(match.group(1).replace(',', '.'))
        datos['referencia'] = match.group(2)
        return datos
    
    return datos

def procesar_xml_pagos_movil(archivo_xml):
    tree = ET.parse(archivo_xml)
    root = tree.getroot()
    
    # Buscar elementos que contengan mensajes SMS
    # Pueden ser <payment> o <sms> o <message>
    mensajes = []
    for elem in root.findall('.//payment') or root.findall('.//sms') or root.findall('.//message'):
        if elem.text:
            mensajes.append(elem.text)
    
    resultados = []
    for msg in mensajes:
        datos = extraer_pago_movil(msg)
        if datos['monto']:  # Solo si se pudo extraer al menos el monto
            resultados.append(datos)
    
    return resultados

# Ejemplo:
pagos = procesar_xml_pagos_movil('mensajes.xml')
for p in pagos:
    print(f"{p['banco']}: {p['monto']} Bs - Ref {p['referencia']}")