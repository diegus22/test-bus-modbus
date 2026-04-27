# Test de Bus Modbus - Aviot

App Windows de diagnóstico para escanear todo el bus RS485 buscando sondas Modbus
y detectar problemas de instalación (sondas caídas, colisiones de ID, errores de
cableado, problemas de terminación).

## Compañera del Configurador Sondas Aviot

- **Configurador Sondas Aviot** → cambia el ID de UNA sonda aislada del bus.
- **Test de Bus Modbus Aviot** (esta) → escanea TODO el bus en producción para
  ver el estado real de todas las sondas conectadas.

## Cómo se usa

1. Conecta el adaptador USB-Modbus al portátil.
2. Conéctalo en paralelo al bus RS485 de la instalación (cable A+ y cable B−)
   en cualquier punto del bus. **NO desconectes ninguna sonda.**
3. Abre la app, pulsa **COMENZAR**.
4. Selecciona puerto y baudrate (típicamente `4800` para sondas Aviot).
5. Selecciona el rango de IDs a barrer (1-247 por defecto, 1-128 si quieres
   más rápido).
6. Pulsa **ESCANEAR BUS**.

## Lectura de resultados

| Color | Significado |
|---|---|
| ✅ Verde | Sonda detectada y leída correctamente |
| · Gris | Sin respuesta (no hay sonda en ese ID) |
| ⚠️ Amarillo | CRC inválido o ID inesperado → posible **colisión** (2 sondas con mismo ID) |
| ❌ Rojo | La sonda respondió con código de error Modbus |

## Build (Windows)

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --icon=aviot.ico --name=Test_Bus_Aviot ^
            --add-data "logo_aviot.png;." test_bus_aviot.py

REM Generar instalador (requiere Inno Setup):
ISCC.exe installer.iss
```

El instalador final (`Instalador_Test_Bus_Aviot.exe`) queda en `Output\`.

## Build (Linux/Mac, prueba)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python test_bus_aviot.py
```

## Notas técnicas

- Modbus RTU, función 0x03 (Read Holding Registers).
- Lee los registros 0x0000 y 0x0001 (humedad y temperatura) de cada sonda.
- Verifica CRC16 de la respuesta para detectar colisiones eléctricas.
- Timeout por sonda: 150ms (configurable en `send_recv`).

## Licencia

Ingeniatic Desarrollo S.L.
