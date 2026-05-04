import re
import xml.etree.ElementTree as ET
import pandas as pd

import xml.etree.ElementTree as ET

def leer_xml_simple(ruta_archivo):
    """
    Abre un archivo XML, muestra su contenido completo y lo parsea
    para entender su estructura.
    """
    # 1. Leer y mostrar el contenido como texto plano
    print("📄 CONTENIDO DEL ARCHIVO (texto):")
    print("=" * 50)
    data = []
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        contenido = archivo.read()
        print(type(contenido))
        linea = contenido.split('\n')    
        
        print(linea[0])
        input("-------")
    # 2. Parsear el XML para ver su estructura jerárquica
    print("\n🌲 ESTRUCTURA DEL XML (etiquetas y atributos):")
    print("=" * 50)
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        #print(f"Etiqueta raíz: {root.tag}")
        
        # Recorrer todos los elementos
        for elem in root.iter():
            #print(f"  Etiqueta: {elem.tag}")
            if elem.attrib:
                print(f"    Atributos: {elem.attrib}")
            if elem.text and elem.text.strip():
                # Mostrar solo los primeros 100 caracteres del texto
                texto_corto = elem.text.strip()[:100]
                print(f"    Contenido: {texto_corto}{'...' if len(elem.text) > 100 else ''}")
    except ET.ParseError as e:
        print(f"❌ Error al analizar el XML: {e}")

# ----- USO -----
leer_xml_simple(r"D:\projectoBanc\app\procesar_xml\sms-20260503083252.xml")