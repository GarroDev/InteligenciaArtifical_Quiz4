"""
Agente Reactivo Simple para la Gestión de Inventario de una Farmacia
Autor: Cristian
Descripción:
    Agente de tipo reactivo basado en una tabla de condición-acción.
    Percibe entradas del operario y ejecuta la acción correspondiente
    sobre el inventario de medicamentos.
"""

import datetime

# ─────────────────────────────────────────────
#  ESTADO INTERNO DEL ENTORNO (inventario)
# ─────────────────────────────────────────────
inventario = {
    "ibuprofeno":   {"stock": 120, "precio": 1500,  "vence": "2026-11-01"},
    "amoxicilina":  {"stock": 8,   "precio": 3200,  "vence": "2025-06-15"},
    "paracetamol":  {"stock": 200, "precio": 800,   "vence": "2027-03-20"},
    "metformina":   {"stock": 45,  "precio": 2100,  "vence": "2026-02-28"},
    "loratadina":   {"stock": 60,  "precio": 1200,  "vence": "2026-09-10"},
}

reporte_ventas = []  # historial de transacciones del día
STOCK_CRITICO = 10   # umbral de alerta


# ─────────────────────────────────────────────
#  ACCIONES DEL AGENTE (6 acciones)
# ─────────────────────────────────────────────

def accion_consultar_stock():
    """Acción 1: Mostrar stock actual de todos los medicamentos."""
    print("\n📋  INVENTARIO ACTUAL")
    print(f"{'Medicamento':<18} {'Stock':>8}  {'Precio (COP)':>14}  {'Vencimiento':>12}")
    print("-" * 60)
    for nombre, datos in inventario.items():
        alerta = " ⚠️ " if datos["stock"] <= STOCK_CRITICO else "    "
        print(f"{nombre:<18}{alerta}{datos['stock']:>5}  {datos['precio']:>14,}  {datos['vence']:>12}")
    print()


def accion_alerta_critico():
    """Acción 2: Mostrar únicamente los medicamentos con stock crítico."""
    criticos = {k: v for k, v in inventario.items() if v["stock"] <= STOCK_CRITICO}
    if criticos:
        print("\n🚨  ALERTA DE STOCK CRÍTICO")
        for nombre, datos in criticos.items():
            print(f"  • {nombre}: {datos['stock']} unidades restantes — REABASTECER URGENTE")
    else:
        print("\n✅  Todos los medicamentos tienen stock suficiente.")
    print()


def accion_vender():
    """Acción 3: Registrar venta de un medicamento y actualizar stock."""
    medicamento = input("   Nombre del medicamento a vender: ").strip().lower()
    if medicamento not in inventario:
        print(f"   ❌  '{medicamento}' no existe en el inventario.\n")
        return

    try:
        cantidad = int(input("   Cantidad a vender: ").strip())
    except ValueError:
        print("   ❌  Cantidad inválida.\n")
        return

    datos = inventario[medicamento]
    if cantidad > datos["stock"]:
        print(f"   ❌  Stock insuficiente. Solo hay {datos['stock']} unidades.\n")
        return

    datos["stock"] -= cantidad
    total = cantidad * datos["precio"]
    reporte_ventas.append({
        "hora": datetime.datetime.now().strftime("%H:%M"),
        "medicamento": medicamento,
        "cantidad": cantidad,
        "total": total
    })
    print(f"   ✅  Venta registrada: {cantidad}x {medicamento} = ${total:,} COP")
    if datos["stock"] <= STOCK_CRITICO:
        print(f"   ⚠️   Stock bajo ({datos['stock']} unidades). Considere reabastecer.")
    print()


def accion_reabastecer():
    """Acción 4: Agregar unidades al inventario de un medicamento."""
    medicamento = input("   Nombre del medicamento a reabastecer: ").strip().lower()
    if medicamento not in inventario:
        agregar = input(f"   '{medicamento}' no existe. ¿Agregar como nuevo? (s/n): ").strip().lower()
        if agregar == "s":
            try:
                precio = int(input("   Precio por unidad (COP): ").strip())
                vence  = input("   Fecha de vencimiento (AAAA-MM-DD): ").strip()
                inventario[medicamento] = {"stock": 0, "precio": precio, "vence": vence}
            except ValueError:
                print("   ❌  Datos inválidos.\n")
                return
        else:
            return

    try:
        cantidad = int(input("   Cantidad a ingresar: ").strip())
    except ValueError:
        print("   ❌  Cantidad inválida.\n")
        return

    inventario[medicamento]["stock"] += cantidad
    print(f"   ✅  Reabastecido: +{cantidad} unidades de {medicamento}. "
          f"Stock total: {inventario[medicamento]['stock']}\n")


def accion_alerta_vencimiento():
    """Acción 5: Detectar medicamentos próximos a vencer (≤ 90 días)."""
    hoy   = datetime.date.today()
    umbral = hoy + datetime.timedelta(days=90)
    proximos = []

    for nombre, datos in inventario.items():
        try:
            fecha_vence = datetime.date.fromisoformat(datos["vence"])
            if fecha_vence <= umbral:
                dias_restantes = (fecha_vence - hoy).days
                proximos.append((nombre, fecha_vence, dias_restantes))
        except ValueError:
            pass

    print("\n📅  ALERTA DE VENCIMIENTO (próximos 90 días)")
    if proximos:
        for nombre, fecha, dias in sorted(proximos, key=lambda x: x[2]):
            estado = "🔴 VENCIDO" if dias < 0 else f"⚠️  {dias} días"
            print(f"  • {nombre:<18}  Vence: {fecha}  →  {estado}")
    else:
        print("  ✅  Ningún medicamento vence en los próximos 90 días.")
    print()


def accion_reporte_cierre():
    """Acción 6: Generar reporte del día y cerrar sesión del agente."""
    print("\n📊  REPORTE DE CIERRE DEL DÍA")
    print(f"  Fecha: {datetime.date.today()}")
    print(f"  Total de ventas: {len(reporte_ventas)} transacciones")

    if reporte_ventas:
        total_ingresos = sum(v["total"] for v in reporte_ventas)
        print(f"  Ingresos del día: ${total_ingresos:,} COP")
        print("\n  Detalle:")
        for v in reporte_ventas:
            print(f"    [{v['hora']}] {v['medicamento']:<18} x{v['cantidad']}  = ${v['total']:,} COP")
    else:
        print("  Sin ventas registradas.")

    print("\n  👋  Sesión cerrada. ¡Hasta mañana!\n")
    return False  # señal de cierre


# ─────────────────────────────────────────────
#  TABLA DE CONDICIÓN → ACCIÓN  (núcleo reactivo)
# ─────────────────────────────────────────────
TABLA_CONDICION_ACCION = {
    ("consultar",)                   : accion_consultar_stock,
    ("consultar", "urgente")         : accion_alerta_critico,
    ("vender",)                      : accion_vender,
    ("reabastecer",)                 : accion_reabastecer,
    ("vencer",)                      : accion_alerta_vencimiento,
    ("cerrar",)                      : accion_reporte_cierre,
}


# ─────────────────────────────────────────────
#  BUCLE PRINCIPAL DEL AGENTE
# ─────────────────────────────────────────────

def percibir(entrada: str) -> tuple:
    """Convierte la entrada del operario en una tupla de percepciones ordenadas."""
    tokens = tuple(sorted(
        p.strip().lower() for p in entrada.split(",") if p.strip()
    ))
    return tokens


def agente_farmacia():
    """Bucle principal: percibir → decidir → actuar."""
    print("=" * 60)
    print("  🏥  AGENTE REACTIVO — FARMACIA SALUD PLUS")
    print("=" * 60)
    print("  Percepciones disponibles:")
    print("    consultar          → Ver inventario completo")
    print("    consultar, urgente → Alertas de stock crítico")
    print("    vender             → Registrar venta")
    print("    reabastecer        → Ingresar unidades al stock")
    print("    vencer             → Ver medicamentos por vencer")
    print("    cerrar             → Reporte y cierre del día")
    print("=" * 60)

    activo = True
    while activo:
        try:
            entrada = input("\n  Percepción: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Sesión interrumpida.")
            break

        if not entrada:
            continue

        percepciones = percibir(entrada)
        accion = TABLA_CONDICION_ACCION.get(percepciones)

        if accion is None:
            print(f"  ❓  Percepción '{entrada}' no reconocida. Intente de nuevo.")
        else:
            resultado = accion()
            if resultado is False:   # accion_reporte_cierre retorna False
                activo = False


if __name__ == "__main__":
    agente_farmacia()