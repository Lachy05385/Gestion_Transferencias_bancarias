# test_flujo_completo.py
import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "lazaro1@example.com"
PASSWORD = "Lachy05385"

def obtener_token():
    """Obtener token JWT"""
    response = requests.post(
        f"{BASE_URL}/token",
        data={
            "username": EMAIL,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Token obtenido: {token[:50]}...")
        return token
    else:
        print(f"❌ Error obteniendo token: {response.json()}")
        return None

def enviar_transferencia(token):
    """Enviar transferencia con fecha problemática"""
    
    texto = """Banco Popular de Ahorro:  La Transferencia fue completada.   Fecha: 12/3/2026   Beneficiario: 9205XXXXXXXX7786   Ordenante: 9205XXXXXXXX9210   Monto: 10000.00 CUP   Nro. Transaccion: BR600CNNS7997"""
    
    print(f"\n📤 Enviando transferencia...")
    print(f"Texto: {texto}")
    
    response = requests.post(
        f"{BASE_URL}/transacciones/recibir",
        data={
            "texto": texto,
            "tipo": "RECIBIDA",
            "token": token,
            "descripcion": "Prueba con fecha 12/3/2026"
        }
    )
    
    print(f"📥 Status: {response.status_code}")
    
    if response.status_code == 200:
        transaccion = response.json()
        print("✅ Transacción creada exitosamente!")
        print(json.dumps(transaccion, indent=2))
    else:
        print(f"❌ Error: {response.json()}")
    
    return response

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBA COMPLETA")
    print("="*60)
    
    token = obtener_token()
    if token:
        enviar_transferencia(token)