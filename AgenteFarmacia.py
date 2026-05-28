"""
Agente Reactivo Simple para la Gestion de Inventario de una Farmacia
Autor: Cristian Garro Sabogal
       Maria Camila Jimenez Puerta
       Juan Esteban Urrea Cardona

Descripcion:
    Agente de tipo reactivo basado en una tabla condicion-accion.
    El agente percibe una entrada del operario, busca una regla aplicable
    y ejecuta la accion asociada sobre el inventario de medicamentos.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Callable


inventario = {
    "ibuprofeno": {"stock": 120, "precio": 1500, "vence": "2026-11-01"},
    "amoxicilina": {"stock": 8, "precio": 3200, "vence": "2025-06-15"},
    "paracetamol": {"stock": 200, "precio": 800, "vence": "2027-03-20"},
    "metformina": {"stock": 45, "precio": 2100, "vence": "2026-02-28"},
    "loratadina": {"stock": 60, "precio": 1200, "vence": "2026-09-10"},
}

reporte_ventas = []
STOCK_CRITICO = 10
DIAS_ALERTA_VENCIMIENTO = 90


@dataclass(frozen=True)
class ReglaCondicionAccion:
    condicion: tuple[str, ...]
    accion: Callable[[], bool | None]
    descripcion: str


def formato_cop(valor: int) -> str:
    return f"${valor:,.0f} COP".replace(",", ".")


def leer_entero(mensaje: str) -> int:
    valor = input(mensaje).strip()
    try:
        numero = int(valor)
    except ValueError as exc:
        raise ValueError("Debe ingresar un numero entero.") from exc

    if numero <= 0:
        raise ValueError("El numero debe ser mayor que cero.")
    return numero


def validar_fecha(fecha: str) -> str:
    try:
        return datetime.date.fromisoformat(fecha).isoformat()
    except ValueError as exc:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD.") from exc


def accion_consultar_stock() -> None:
    """Accion 1: mostrar stock actual de todos los medicamentos."""
    print("\nINVENTARIO ACTUAL")
    print(f"{'Medicamento':<18} {'Stock':>8} {'Precio':>16} {'Vencimiento':>14} {'Estado':>18}")
    print("-" * 82)

    for nombre, datos in sorted(inventario.items()):
        estado = "Stock critico" if datos["stock"] <= STOCK_CRITICO else "Normal"
        print(
            f"{nombre:<18} {datos['stock']:>8} {formato_cop(datos['precio']):>16} "
            f"{datos['vence']:>14} {estado:>18}"
        )
    print()


def accion_alerta_critico() -> None:
    """Accion 2: mostrar medicamentos con stock critico."""
    criticos = {
        nombre: datos
        for nombre, datos in sorted(inventario.items())
        if datos["stock"] <= STOCK_CRITICO
    }

    print("\nALERTA DE STOCK CRITICO")
    if not criticos:
        print("Todos los medicamentos tienen stock suficiente.\n")
        return

    for nombre, datos in criticos.items():
        print(f"- {nombre}: {datos['stock']} unidades restantes. Reabastecer.")
    print()


def accion_vender() -> None:
    """Accion 3: registrar venta y actualizar stock."""
    medicamento = input("Nombre del medicamento a vender: ").strip().lower()
    if medicamento not in inventario:
        print(f"'{medicamento}' no existe en el inventario.\n")
        return

    try:
        cantidad = leer_entero("Cantidad a vender: ")
    except ValueError as exc:
        print(f"{exc}\n")
        return

    datos = inventario[medicamento]
    if cantidad > datos["stock"]:
        print(f"Stock insuficiente. Disponible: {datos['stock']} unidades.\n")
        return

    datos["stock"] -= cantidad
    total = cantidad * datos["precio"]
    reporte_ventas.append(
        {
            "hora": datetime.datetime.now().strftime("%H:%M"),
            "medicamento": medicamento,
            "cantidad": cantidad,
            "total": total,
        }
    )

    print(f"Venta registrada: {cantidad} x {medicamento} = {formato_cop(total)}")
    if datos["stock"] <= STOCK_CRITICO:
        print(f"Resultado reactivo adicional: stock critico ({datos['stock']} unidades).")
    print()


def accion_reabastecer() -> None:
    """Accion 4: agregar unidades al inventario."""
    medicamento = input("Nombre del medicamento a reabastecer: ").strip().lower()
    if not medicamento:
        print("Debe ingresar un medicamento.\n")
        return

    if medicamento not in inventario:
        respuesta = input("No existe en inventario. Desea crearlo? (s/n): ").strip().lower()
        if respuesta != "s":
            print("Operacion cancelada.\n")
            return

        try:
            precio = leer_entero("Precio por unidad (COP): ")
            vence = validar_fecha(input("Fecha de vencimiento (AAAA-MM-DD): ").strip())
        except ValueError as exc:
            print(f"{exc}\n")
            return

        inventario[medicamento] = {"stock": 0, "precio": precio, "vence": vence}

    try:
        cantidad = leer_entero("Cantidad a ingresar: ")
    except ValueError as exc:
        print(f"{exc}\n")
        return

    inventario[medicamento]["stock"] += cantidad
    stock_total = inventario[medicamento]["stock"]
    print(f"Reabastecimiento registrado: {medicamento}. Stock total: {stock_total}\n")


def accion_alerta_vencimiento() -> None:
    """Accion 5: detectar medicamentos vencidos o proximos a vencer."""
    hoy = datetime.date.today()
    umbral = hoy + datetime.timedelta(days=DIAS_ALERTA_VENCIMIENTO)
    proximos = []

    for nombre, datos in sorted(inventario.items()):
        try:
            fecha_vence = datetime.date.fromisoformat(datos["vence"])
        except ValueError:
            proximos.append((nombre, datos["vence"], "Fecha invalida"))
            continue

        if fecha_vence <= umbral:
            dias = (fecha_vence - hoy).days
            if dias < 0:
                estado = f"Vencido hace {abs(dias)} dias"
            elif dias == 0:
                estado = "Vence hoy"
            else:
                estado = f"Vence en {dias} dias"
            proximos.append((nombre, fecha_vence.isoformat(), estado))

    print(f"\nALERTA DE VENCIMIENTO ({DIAS_ALERTA_VENCIMIENTO} dias)")
    if not proximos:
        print("Ningun medicamento vence dentro del umbral definido.\n")
        return

    for nombre, fecha, estado in proximos:
        print(f"- {nombre:<18} Vence: {fecha} | {estado}")
    print()


def accion_reporte_cierre() -> bool:
    """Accion 6: generar reporte del dia y cerrar sesion."""
    total_ingresos = sum(venta["total"] for venta in reporte_ventas)

    print("\nREPORTE DE CIERRE DEL DIA")
    print(f"Fecha: {datetime.date.today().isoformat()}")
    print(f"Total de ventas: {len(reporte_ventas)} transacciones")
    print(f"Ingresos del dia: {formato_cop(total_ingresos)}")

    if reporte_ventas:
        print("\nDetalle:")
        for venta in reporte_ventas:
            print(
                f"[{venta['hora']}] {venta['medicamento']:<18} "
                f"x{venta['cantidad']} = {formato_cop(venta['total'])}"
            )
    else:
        print("Sin ventas registradas.")

    print("\nSesion cerrada.\n")
    return False


TABLA_CONDICION_ACCION = {
    ("consultar",): ReglaCondicionAccion(
        condicion=("consultar",),
        accion=accion_consultar_stock,
        descripcion="consultar inventario completo",
    ),
    ("consultar", "urgente"): ReglaCondicionAccion(
        condicion=("consultar", "urgente"),
        accion=accion_alerta_critico,
        descripcion="detectar medicamentos con stock critico",
    ),
    ("vender",): ReglaCondicionAccion(
        condicion=("vender",),
        accion=accion_vender,
        descripcion="registrar venta y descontar unidades",
    ),
    ("reabastecer",): ReglaCondicionAccion(
        condicion=("reabastecer",),
        accion=accion_reabastecer,
        descripcion="agregar unidades al inventario",
    ),
    ("vencer",): ReglaCondicionAccion(
        condicion=("vencer",),
        accion=accion_alerta_vencimiento,
        descripcion="revisar medicamentos vencidos o proximos a vencer",
    ),
    ("cerrar",): ReglaCondicionAccion(
        condicion=("cerrar",),
        accion=accion_reporte_cierre,
        descripcion="generar reporte y finalizar sesion",
    ),
}


def percibir(entrada: str) -> tuple[str, ...]:
    """Convierte la entrada del operario en una percepcion normalizada."""
    return tuple(sorted(p.strip().lower() for p in entrada.split(",") if p.strip()))


def decidir(percepcion: tuple[str, ...]) -> ReglaCondicionAccion | None:
    """Busca una regla en la tabla condicion-accion."""
    return TABLA_CONDICION_ACCION.get(percepcion)


def actuar(regla: ReglaCondicionAccion) -> bool | None:
    """Ejecuta la accion asociada a la regla seleccionada."""
    return regla.accion()


def mostrar_reglas_disponibles() -> None:
    print("Percepciones disponibles:")
    print("  consultar           -> Ver inventario completo")
    print("  consultar, urgente  -> Ver medicamentos con stock critico")
    print("  vender              -> Registrar venta")
    print("  reabastecer         -> Ingresar unidades al stock")
    print("  vencer              -> Ver medicamentos vencidos o proximos a vencer")
    print("  cerrar              -> Reporte y cierre del dia")


def mostrar_traza(percepcion: tuple[str, ...], regla: ReglaCondicionAccion | None) -> None:
    print("\nCICLO DEL AGENTE")
    print(f"1. Percibir: {percepcion if percepcion else 'sin percepcion'}")

    if regla is None:
        print("2. Decidir: no existe regla para esa percepcion")
        print("3. Actuar: solicitar una percepcion valida\n")
        return

    condicion = ", ".join(regla.condicion)
    print(f"2. Decidir: SI percepcion = ({condicion}) ENTONCES {regla.descripcion}")
    print(f"3. Actuar: ejecutar {regla.accion.__name__}\n")


def agente_farmacia() -> None:
    """Bucle principal del agente: percibir, decidir y actuar."""
    print("=" * 72)
    print("AGENTE REACTIVO SIMPLE - FARMACIA SALUD PLUS")
    print("=" * 72)
    print("Tipo de agente: reactivo simple basado en reglas condicion-accion.")
    print("Objetivo: responder a cambios del inventario segun la percepcion recibida.")
    print("-" * 72)
    mostrar_reglas_disponibles()
    print("=" * 72)

    activo = True
    while activo:
        try:
            entrada = input("\nPercepcion del entorno: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesion interrumpida.")
            break

        if not entrada:
            print("Ingrese una percepcion para que el agente pueda reaccionar.")
            continue

        percepcion = percibir(entrada)
        regla = decidir(percepcion)
        mostrar_traza(percepcion, regla)

        if regla is None:
            mostrar_reglas_disponibles()
            continue

        resultado = actuar(regla)
        if resultado is False:
            activo = False


if __name__ == "__main__":
    agente_farmacia()
