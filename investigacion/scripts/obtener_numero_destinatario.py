import re



texto = "El titular del telefono 5354882197 le ha realizado una transferencia a la cuenta 9205129970539210 de 2000.00 CUP. Nro. Transaccion AY6008E43M999. Fecha: 17/3/2026."

# Expresión regular para teléfono y cuenta



patron = r'telefono\s+(\d+).*?cuenta\s+(\d+)'

# Buscar
match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)

if match:
    telefono = match.group(1)
    cuenta = match.group(2)
    print(f"📱 Teléfono: {telefono}")
    print(f"💳 Cuenta: {cuenta}")
else:
    print("No se encontraron coincidencias")
    
    
