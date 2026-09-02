# test_normalizacion_avanzada.py
from utils import normalizar_texto_transferencia

def probar_casos():
    """Prueba diferentes formatos de texto bancario"""
    
    casos = [
        # Caso 1: Tabulaciones
        """Transferencia	bancaria
Fecha:	15/03/2024
Ordenante:	ES12345678901234567890
Beneficiario:	ES98765432109876543210
Importe:	150.50	EUR
Concepto:	Pago servicios""",
        
        # Caso 2: Espacios múltiples
        "Transferencia    bancaria    Fecha:    15/03/2024    Ordenante:    ES12345678901234567890    Beneficiario:    ES98765432109876543210    Importe:    150.50    EUR    Concepto:    Pago servicios",
        
        # Caso 3: Formato SMS
        "BCO SANTANDER: Transferencia 15/03/24 150.50EUR de ES12345678901234567890 a ES98765432109876543210. Concepto: Pago servicios",
        
        # Caso 4: Formato email
        """Transferencia recibida
Fecha de operación: 15 de marzo de 2024
Ordenante: Juan Pérez (ES12345678901234567890)
Beneficiario: María García (ES98765432109876543210)
Importe: 150,50 euros
Concepto: Pago de servicios mensuales""",
        
        # Caso 5: Formato con puntos y comas
        "Transferencia: 15.03.2024 - De: ES12345678901234567890 - Para: ES98765432109876543210 - Cantidad: 150,50€ - Ref: Pago servicios",
        # caso mio
        """Banco Popular de Ahorro:  La Transferencia fue completada. 
 Fecha: 12/3/2026 
 Beneficiario: 9205XXXXXXXX7786 
 Ordenante: 9205XXXXXXXX9210 
 Monto: 10000.00 CUP 
 Nro. Transaccion: BR600CNNS7997"""
    ]
    
    for i, caso in enumerate(casos, 1):
        print(f"\n{'#'*80}")
        print(f"# CASO {i}")
        print(f"{'#'*80}")
        print("TEXTO ORIGINAL:")
        print(caso)
        print("\n" + "-"*40)
        
        resultado = normalizar_texto_transferencia(caso)
        
        print("\nRESULTADO NORMALIZADO:")
        print(resultado)
        print("\n" + "="*80)

if __name__ == "__main__":
    probar_casos()