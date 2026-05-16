# utils.py - Agregar estas funciones

import pytesseract
from PIL import Image
import io
import re

# Configurar ruta de Tesseract (ajusta según tu instalación)
# Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Linux/Mac: generalmente ya está en el PATH

def extraer_texto_de_imagen(imagen_bytes: bytes) -> str:
    """
    Extrae texto de una imagen usando OCR (Tesseract)
    
    Args:
        imagen_bytes: Bytes de la imagen (JPEG, PNG, etc.)
    
    Returns:
        str: Texto extraído de la imagen
    """
    try:
        # Abrir imagen desde bytes
        imagen = Image.open(io.BytesIO(imagen_bytes))
        
        # Configurar Tesseract para español (opcional)
        # Puedes usar 'spa' para español, 'eng' para inglés, o ambos 'spa+eng'
        texto = pytesseract.image_to_string(imagen, lang='spa+eng')
        
        # Limpiar texto
        texto = texto.strip()
        print(f"📸 Texto extraído de imagen:\n{texto}")
        
        return texto
    except Exception as e:
        print(f"❌ Error en OCR: {str(e)}")
        raise ValueError(f"No se pudo extraer texto de la imagen: {str(e)}")

def extraer_datos_transferencia_de_texto(texto: str) -> dict:
    """
    Extrae los datos de una transferencia desde texto (mejorado para OCR)
    """
    resultado = {
        "banco": "",
        "fecha": "",
        "beneficiario": "",
        "ordenante": "",
        "telefono_ordenante": "",
        "monto": 0.0,
        "moneda": "CUP",
        "numero_transaccion": "",
        "concepto": ""
    }
    
    # Normalizar texto
    texto = normalizar_texto_transferencia(texto)
    texto_lower = texto.lower()
    
    print(f"📝 Texto normalizado: {texto}")
    
    # 1. Buscar BANCO
    bancos = [
        "banco popular", "bpopular", "popular", 
        "banco metropolitano", "bmetropolitano", 
        "banco nacional", "bancario", "banco",
        "bpa", "bmet", "bna"
    ]
    for banco in bancos:
        if banco in texto_lower:
            match = re.search(r'(banco[^:.]*)[:. ]', texto_lower, re.IGNORECASE)
            if match:
                resultado["banco"] = match.group(1).strip().title()
            else:
                resultado["banco"] = "Banco Popular"
            break
    
    # 2. Buscar FECHA (más flexible para OCR)
    fecha_patterns = [
        r'fecha[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})',
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})',
    ]
    
    for pattern in fecha_patterns:
        fecha_match = re.search(pattern, texto, re.IGNORECASE)
        if fecha_match:
            grupos = fecha_match.groups()
            if len(grupos) == 3:
                dia, mes, año = grupos
                resultado["fecha"] = normalizar_fecha(f"{dia}/{mes}/{año}")
                break
    
    # 3. Buscar BENEFICIARIO (cuenta destino)
    beneficiario_patterns = [
        r'beneficiario[:\s]*([A-Z0-9*]+)',
        r'cuenta[:\s]*(\d{10,})',
        r'a la cuenta\s+(\d{10,})',
        r'destino[:\s]*(\d{10,})',
        r'para\s+(\d{10,})',
    ]
    
    for pattern in beneficiario_patterns:
        ben_match = re.search(pattern, texto, re.IGNORECASE)
        if ben_match:
            resultado["beneficiario"] = ben_match.group(1).strip()
            break
    
    # 4. Buscar ORDENANTE
    ordenante_patterns = [
        r'ordenante[:\s]*([A-Z0-9*]+)',
        r'de la cuenta\s+(\d{10,})',
        r'origen[:\s]*(\d{10,})',
        r'remitente[:\s]*(\d{10,})',
    ]
    
    ordenante_encontrado = False
    for pattern in ordenante_patterns:
        ord_match = re.search(pattern, texto, re.IGNORECASE)
        if ord_match:
            resultado["ordenante"] = ord_match.group(1).strip()
            ordenante_encontrado = True
            break
    
    # 5. Buscar TELÉFONO (para usar como ordenante si no hay cuenta)
    telefono_patterns = [
        r'telefono[:\s]*(\d{7,})',
        r'tel[.:]?\s*(\d{7,})',
        r'celular[:\s]*(\d{7,})',
        r'(\d{3}\s*\d{3}\s*\d{4})',  # Formato común
    ]
    
    if not ordenante_encontrado:
        for pattern in telefono_patterns:
            tel_match = re.search(pattern, texto, re.IGNORECASE)
            if tel_match:
                telefono = tel_match.group(1).strip()
                resultado["telefono_ordenante"] = telefono
                resultado["ordenante"] = f"tel:{telefono}"
                break
    
    # 6. Buscar MONTO
    monto_patterns = [
        r'monto[:\s]*([\d,.]+)\s*([A-Z]{3})',
        r'importe[:\s]*([\d,.]+)\s*([A-Z]{3})',
        r'([\d,.]+)\s*(CUP|USD|EUR|MLC)',
        r'(\d+[.,]\d+)\s*(€|\$|CUP)',
    ]
    
    for pattern in monto_patterns:
        monto_match = re.search(pattern, texto, re.IGNORECASE)
        if monto_match:
            grupos = monto_match.groups()
            if len(grupos) == 2:
                monto_str = grupos[0].replace(',', '')
                resultado["monto"] = round(float(monto_str), 2)
                moneda_raw = grupos[1].upper()
                if '€' in moneda_raw or 'EUR' in moneda_raw:
                    resultado["moneda"] = "EUR"
                elif '$' in moneda_raw or 'USD' in moneda_raw:
                    resultado["moneda"] = "USD"
                elif 'CUP' in moneda_raw:
                    resultado["moneda"] = "CUP"
                elif 'MLC' in moneda_raw:
                    resultado["moneda"] = "MLC"
            else:
                monto_str = grupos[0].replace(',', '')
                resultado["monto"] = round(float(monto_str), 2)
            break
    
    # 7. Buscar NÚMERO DE TRANSACCIÓN
    transaccion_patterns = [
        r'nro\.?\s*transaccion[:\s]*([A-Z0-9]+)',
        r'referencia[:\s]*([A-Z0-9]+)',
        r'operacion[:\s]*([A-Z0-9]+)',
        r'codigo[:\s]*([A-Z0-9]+)',
        r'([A-Z0-9]{8,})',
    ]
    
    for pattern in transaccion_patterns:
        ref_match = re.search(pattern, texto, re.IGNORECASE)
        if ref_match:
            resultado["numero_transaccion"] = ref_match.group(1).strip()
            break
    
    # 8. Buscar CONCEPTO
    concepto_patterns = [
        r'concepto[:\s]*([^.]+)',
        r'descripcion[:\s]*([^.]+)',
        r'motivo[:\s]*([^.]+)',
    ]
    
    for pattern in concepto_patterns:
        concepto_match = re.search(pattern, texto, re.IGNORECASE)
        if concepto_match:
            resultado["concepto"] = concepto_match.group(1).strip()
            break
    
    # Validar y asignar valores por defecto
    if not resultado["fecha"]:
        from datetime import datetime
        resultado["fecha"] = datetime.now().strftime("%d/%m/%Y")
    
    if not resultado["beneficiario"]:
        resultado["beneficiario"] = "XXXX"
    
    if not resultado["ordenante"]:
        resultado["ordenante"] = "XXXX"
    
    if not resultado["numero_transaccion"]:
        from datetime import datetime
        resultado["numero_transaccion"] = f"OCR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return resultado