"""
Agente Reactivo Simple para la Gestion de Inventario de una Farmacia
Autor: Cristian Garro Sabogal
       Maria Camila Jimenez Puerta
       Juan Esteban Urrea Cardona

Descripcion:
    Agente de tipo reactivo basado en una tabla condicion-accion.
    La interfaz permite demostrar el ciclo percibir, decidir y actuar
    sin ocultar la regla que se activa en cada percepcion.
"""

from __future__ import annotations

import datetime
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk


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
    accion: str
    descripcion: str


TABLA_CONDICION_ACCION = {
    ("consultar",): ReglaCondicionAccion(
        condicion=("consultar",),
        accion="accion_consultar_stock",
        descripcion="consultar inventario completo",
    ),
    ("consultar", "urgente"): ReglaCondicionAccion(
        condicion=("consultar", "urgente"),
        accion="accion_alerta_critico",
        descripcion="detectar medicamentos con stock critico",
    ),
    ("vender",): ReglaCondicionAccion(
        condicion=("vender",),
        accion="accion_vender",
        descripcion="registrar venta y descontar unidades",
    ),
    ("reabastecer",): ReglaCondicionAccion(
        condicion=("reabastecer",),
        accion="accion_reabastecer",
        descripcion="agregar unidades al inventario",
    ),
    ("vencer",): ReglaCondicionAccion(
        condicion=("vencer",),
        accion="accion_alerta_vencimiento",
        descripcion="revisar medicamentos vencidos o proximos a vencer",
    ),
    ("cerrar",): ReglaCondicionAccion(
        condicion=("cerrar",),
        accion="accion_reporte_cierre",
        descripcion="generar reporte y finalizar sesion",
    ),
}


def formato_cop(valor: int) -> str:
    return f"${valor:,.0f} COP".replace(",", ".")


def normalizar_medicamento(nombre: str) -> str:
    return nombre.strip().lower()


def leer_entero_desde_texto(valor: str, campo: str) -> int:
    try:
        numero = int(valor.strip())
    except ValueError as exc:
        raise ValueError(f"{campo} debe ser un numero entero.") from exc

    if numero <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    return numero


def validar_fecha(fecha: str) -> str:
    try:
        return datetime.date.fromisoformat(fecha.strip()).isoformat()
    except ValueError as exc:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD.") from exc


def percibir(entrada: str) -> tuple[str, ...]:
    """Convierte la entrada del operario en una percepcion normalizada."""
    return tuple(sorted(p.strip().lower() for p in entrada.split(",") if p.strip()))


def decidir(percepcion: tuple[str, ...]) -> ReglaCondicionAccion | None:
    """Busca una regla en la tabla condicion-accion."""
    return TABLA_CONDICION_ACCION.get(percepcion)


def obtener_estado(datos: dict) -> str:
    estados = []

    if datos["stock"] <= STOCK_CRITICO:
        estados.append("Stock critico")

    try:
        fecha_vence = datetime.date.fromisoformat(datos["vence"])
    except ValueError:
        estados.append("Fecha invalida")
    else:
        dias = (fecha_vence - datetime.date.today()).days
        if dias < 0:
            estados.append("Vencido")
        elif dias <= DIAS_ALERTA_VENCIMIENTO:
            estados.append(f"Por vencer: {dias} dias")

    return ", ".join(estados) if estados else "Normal"


def consultar_stock() -> str:
    lineas = [
        "INVENTARIO ACTUAL",
        f"{'Medicamento':<18} {'Stock':>8} {'Precio':>16} {'Vencimiento':>14} {'Estado':>22}",
        "-" * 86,
    ]

    for nombre, datos in sorted(inventario.items()):
        lineas.append(
            f"{nombre:<18} {datos['stock']:>8} {formato_cop(datos['precio']):>16} "
            f"{datos['vence']:>14} {obtener_estado(datos):>22}"
        )

    return "\n".join(lineas)


def consultar_stock_critico() -> str:
    criticos = [
        (nombre, datos)
        for nombre, datos in sorted(inventario.items())
        if datos["stock"] <= STOCK_CRITICO
    ]

    if not criticos:
        return "ALERTA DE STOCK CRITICO\nTodos los medicamentos tienen stock suficiente."

    lineas = ["ALERTA DE STOCK CRITICO"]
    for nombre, datos in criticos:
        lineas.append(f"- {nombre}: {datos['stock']} unidades restantes. Reabastecer.")
    return "\n".join(lineas)


def registrar_venta(medicamento: str, cantidad: int) -> str:
    medicamento = normalizar_medicamento(medicamento)

    if not medicamento:
        raise ValueError("Seleccione un medicamento para vender.")
    if medicamento not in inventario:
        raise ValueError(f"'{medicamento}' no existe en el inventario.")

    datos = inventario[medicamento]
    if cantidad > datos["stock"]:
        raise ValueError(f"Stock insuficiente. Disponible: {datos['stock']} unidades.")

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

    lineas = [
        f"Venta registrada: {cantidad} x {medicamento} = {formato_cop(total)}",
        f"Stock actual de {medicamento}: {datos['stock']} unidades.",
    ]

    if datos["stock"] <= STOCK_CRITICO:
        lineas.append("Resultado reactivo adicional: el medicamento quedo en stock critico.")

    return "\n".join(lineas)


def reabastecer_medicamento(
    medicamento: str,
    cantidad: int,
    precio: int | None = None,
    vence: str | None = None,
) -> str:
    medicamento = normalizar_medicamento(medicamento)

    if not medicamento:
        raise ValueError("Ingrese el nombre del medicamento.")

    existe = medicamento in inventario
    fecha_validada = validar_fecha(vence) if vence else None

    if not existe:
        if precio is None:
            raise ValueError("Para un medicamento nuevo debe ingresar el precio.")
        if fecha_validada is None:
            raise ValueError("Para un medicamento nuevo debe ingresar el vencimiento.")
        inventario[medicamento] = {"stock": 0, "precio": precio, "vence": fecha_validada}
    else:
        if precio is not None:
            inventario[medicamento]["precio"] = precio
        if fecha_validada is not None:
            inventario[medicamento]["vence"] = fecha_validada

    inventario[medicamento]["stock"] += cantidad
    stock_total = inventario[medicamento]["stock"]
    operacion = "creado y reabastecido" if not existe else "reabastecido"
    return f"Medicamento {operacion}: {medicamento}. Stock total: {stock_total} unidades."


def consultar_vencimientos() -> str:
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

    if not proximos:
        return f"ALERTA DE VENCIMIENTO\nNingun medicamento vence en {DIAS_ALERTA_VENCIMIENTO} dias."

    lineas = [f"ALERTA DE VENCIMIENTO ({DIAS_ALERTA_VENCIMIENTO} dias)"]
    for nombre, fecha, estado in proximos:
        lineas.append(f"- {nombre:<18} Vence: {fecha} | {estado}")
    return "\n".join(lineas)


def generar_reporte_cierre() -> str:
    total_ingresos = sum(venta["total"] for venta in reporte_ventas)
    lineas = [
        "REPORTE DE CIERRE DEL DIA",
        f"Fecha: {datetime.date.today().isoformat()}",
        f"Total de ventas: {len(reporte_ventas)} transacciones",
        f"Ingresos del dia: {formato_cop(total_ingresos)}",
    ]

    if reporte_ventas:
        lineas.append("")
        lineas.append("Detalle:")
        for venta in reporte_ventas:
            lineas.append(
                f"[{venta['hora']}] {venta['medicamento']:<18} "
                f"x{venta['cantidad']} = {formato_cop(venta['total'])}"
            )
    else:
        lineas.append("Sin ventas registradas.")

    lineas.append("")
    lineas.append("Sesion cerrada para efectos de la demostracion.")
    return "\n".join(lineas)


class AgenteFarmaciaApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Agente Reactivo - Farmacia Salud Plus")
        self.root.geometry("1180x780")
        self.root.minsize(1040, 700)

        self.percepcion_var = tk.StringVar(value="consultar")
        self.venta_medicamento_var = tk.StringVar()
        self.venta_cantidad_var = tk.StringVar(value="1")
        self.reabastecer_medicamento_var = tk.StringVar()
        self.reabastecer_cantidad_var = tk.StringVar(value="1")
        self.reabastecer_precio_var = tk.StringVar()
        self.reabastecer_vence_var = tk.StringVar()

        self.percibir_var = tk.StringVar(value="Esperando percepcion.")
        self.decidir_var = tk.StringVar(value="Sin regla evaluada.")
        self.actuar_var = tk.StringVar(value="Sin accion ejecutada.")
        self.estado_var = tk.StringVar(value="Agente listo.")

        self.configurar_estilos()
        self.construir_interfaz()
        self.actualizar_tablas()
        self.actualizar_controles_por_percepcion()

    def configurar_estilos(self) -> None:
        self.root.option_add("*Font", ("Segoe UI", 10))
        estilo = ttk.Style(self.root)

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure("App.TFrame", background="#f4f6f8")
        estilo.configure("Header.TFrame", background="#263238")
        estilo.configure(
            "HeaderTitle.TLabel",
            background="#263238",
            foreground="#ffffff",
            font=("Segoe UI", 18, "bold"),
        )
        estilo.configure(
            "HeaderText.TLabel",
            background="#263238",
            foreground="#d7dee2",
            font=("Segoe UI", 10),
        )
        estilo.configure("Section.TLabelframe", background="#f4f6f8")
        estilo.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        estilo.configure("Trace.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        estilo.configure("TraceTitle.TLabel", background="#ffffff", foreground="#51606a")
        estilo.configure(
            "TraceValue.TLabel",
            background="#ffffff",
            foreground="#172026",
            font=("Segoe UI", 10, "bold"),
            wraplength=500,
        )
        estilo.configure("Status.TLabel", background="#e8edf0", foreground="#263238")
        estilo.configure("Treeview", rowheight=26)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def construir_interfaz(self) -> None:
        contenedor = ttk.Frame(self.root, padding=16, style="App.TFrame")
        contenedor.pack(fill=tk.BOTH, expand=True)

        encabezado = ttk.Frame(contenedor, padding=(16, 12), style="Header.TFrame")
        encabezado.pack(fill=tk.X)
        ttk.Label(
            encabezado,
            text="Agente Reactivo Simple - Farmacia Salud Plus",
            style="HeaderTitle.TLabel",
        ).pack(anchor=tk.W)
        ttk.Label(
            encabezado,
            text="Demostracion de percepcion, regla condicion-accion y respuesta del agente",
            style="HeaderText.TLabel",
        ).pack(anchor=tk.W, pady=(4, 0))

        cuerpo = ttk.Frame(contenedor, style="App.TFrame")
        cuerpo.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        cuerpo.columnconfigure(0, weight=0)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        panel_izquierdo = ttk.Frame(cuerpo, style="App.TFrame")
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        panel_izquierdo.columnconfigure(0, weight=1)

        self.construir_panel_percepcion(panel_izquierdo)
        self.construir_panel_datos(panel_izquierdo)
        self.construir_panel_reglas(panel_izquierdo)

        panel_derecho = ttk.Frame(cuerpo, style="App.TFrame")
        panel_derecho.grid(row=0, column=1, sticky="nsew")
        panel_derecho.columnconfigure(0, weight=1)
        panel_derecho.rowconfigure(2, weight=1)

        self.construir_panel_traza(panel_derecho)
        self.construir_panel_resultado(panel_derecho)
        self.construir_panel_inventario(panel_derecho)

        ttk.Label(
            contenedor,
            textvariable=self.estado_var,
            padding=(10, 6),
            style="Status.TLabel",
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(10, 0))

    def construir_panel_percepcion(self, contenedor: ttk.Frame) -> None:
        panel = ttk.LabelFrame(contenedor, text="Entrada del agente", padding=10)
        panel.grid(row=0, column=0, sticky="ew")
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Percepcion del entorno").grid(row=0, column=0, sticky=tk.W)
        self.combo_percepcion = ttk.Combobox(
            panel,
            textvariable=self.percepcion_var,
            values=[
                "consultar",
                "consultar, urgente",
                "vender",
                "reabastecer",
                "vencer",
                "cerrar",
            ],
            state="readonly",
            width=30,
        )
        self.combo_percepcion.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.combo_percepcion.bind("<<ComboboxSelected>>", self.actualizar_controles_por_percepcion)

        ttk.Button(
            panel,
            text="Ejecutar ciclo",
            command=self.ejecutar_ciclo,
        ).grid(row=2, column=0, sticky="ew")

    def construir_panel_datos(self, contenedor: ttk.Frame) -> None:
        panel = ttk.LabelFrame(contenedor, text="Datos de la accion", padding=10)
        panel.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Venta").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(panel, text="Medicamento").grid(row=1, column=0, sticky=tk.W, pady=(6, 2))
        self.combo_venta = ttk.Combobox(
            panel,
            textvariable=self.venta_medicamento_var,
            state="readonly",
            width=24,
        )
        self.combo_venta.grid(row=1, column=1, sticky="ew", pady=(6, 2))

        ttk.Label(panel, text="Cantidad").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.spin_venta = ttk.Spinbox(
            panel,
            from_=1,
            to=9999,
            textvariable=self.venta_cantidad_var,
            width=10,
        )
        self.spin_venta.grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Separator(panel).grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(panel, text="Reabastecimiento").grid(row=4, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(panel, text="Medicamento").grid(row=5, column=0, sticky=tk.W, pady=(6, 2))
        self.combo_reabastecer = ttk.Combobox(
            panel,
            textvariable=self.reabastecer_medicamento_var,
            width=24,
        )
        self.combo_reabastecer.grid(row=5, column=1, sticky="ew", pady=(6, 2))
        self.combo_reabastecer.bind("<<ComboboxSelected>>", self.cargar_datos_reabastecimiento)

        ttk.Label(panel, text="Cantidad").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.spin_reabastecer = ttk.Spinbox(
            panel,
            from_=1,
            to=9999,
            textvariable=self.reabastecer_cantidad_var,
            width=10,
        )
        self.spin_reabastecer.grid(row=6, column=1, sticky=tk.W, pady=2)

        ttk.Label(panel, text="Precio").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.entry_precio = ttk.Entry(panel, textvariable=self.reabastecer_precio_var, width=12)
        self.entry_precio.grid(row=7, column=1, sticky=tk.W, pady=2)

        ttk.Label(panel, text="Vencimiento").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.entry_vence = ttk.Entry(panel, textvariable=self.reabastecer_vence_var, width=14)
        self.entry_vence.grid(row=8, column=1, sticky=tk.W, pady=2)

        self.widgets_venta = [self.combo_venta, self.spin_venta]
        self.widgets_reabastecer = [
            self.combo_reabastecer,
            self.spin_reabastecer,
            self.entry_precio,
            self.entry_vence,
        ]

    def construir_panel_reglas(self, contenedor: ttk.Frame) -> None:
        panel = ttk.LabelFrame(contenedor, text="Tabla condicion-accion", padding=10)
        panel.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        contenedor.rowconfigure(2, weight=1)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        self.tabla_reglas = ttk.Treeview(
            panel,
            columns=("condicion", "accion"),
            show="headings",
            height=7,
        )
        self.tabla_reglas.heading("condicion", text="Condicion")
        self.tabla_reglas.heading("accion", text="Accion")
        self.tabla_reglas.column("condicion", width=150, anchor=tk.W)
        self.tabla_reglas.column("accion", width=210, anchor=tk.W)
        self.tabla_reglas.grid(row=0, column=0, sticky="nsew")

        for regla in TABLA_CONDICION_ACCION.values():
            self.tabla_reglas.insert(
                "",
                tk.END,
                iid="|".join(regla.condicion),
                values=(", ".join(regla.condicion), regla.descripcion),
            )

    def construir_panel_traza(self, contenedor: ttk.Frame) -> None:
        panel = ttk.LabelFrame(contenedor, text="Ciclo del agente", padding=10)
        panel.grid(row=0, column=0, sticky="ew")
        panel.columnconfigure(0, weight=1)

        self.crear_paso_traza(panel, 0, "1. Percibir", self.percibir_var)
        self.crear_paso_traza(panel, 1, "2. Decidir", self.decidir_var)
        self.crear_paso_traza(panel, 2, "3. Actuar", self.actuar_var)

    def crear_paso_traza(
        self,
        contenedor: ttk.Frame,
        fila: int,
        titulo: str,
        variable: tk.StringVar,
    ) -> None:
        marco = ttk.Frame(contenedor, padding=10, style="Trace.TFrame")
        marco.grid(row=fila, column=0, sticky="ew", pady=(0 if fila == 0 else 8, 0))
        marco.columnconfigure(0, weight=1)
        ttk.Label(marco, text=titulo, style="TraceTitle.TLabel").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(marco, textvariable=variable, style="TraceValue.TLabel").grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

    def construir_panel_resultado(self, contenedor: ttk.Frame) -> None:
        panel = ttk.LabelFrame(contenedor, text="Resultado de la accion", padding=10)
        panel.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        panel.columnconfigure(0, weight=1)

        self.texto_resultado = tk.Text(
            panel,
            height=8,
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1,
            font=("Consolas", 10),
        )
        self.texto_resultado.grid(row=0, column=0, sticky="ew")
        self.texto_resultado.insert("1.0", "Ejecute una percepcion para observar la respuesta.")
        self.texto_resultado.configure(state=tk.DISABLED)

    def construir_panel_inventario(self, contenedor: ttk.Frame) -> None:
        panel = ttk.LabelFrame(contenedor, text="Estado del entorno", padding=10)
        panel.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        self.tabla_inventario = ttk.Treeview(
            panel,
            columns=("medicamento", "stock", "precio", "vence", "estado"),
            show="headings",
            height=8,
        )
        self.tabla_inventario.heading("medicamento", text="Medicamento")
        self.tabla_inventario.heading("stock", text="Stock")
        self.tabla_inventario.heading("precio", text="Precio")
        self.tabla_inventario.heading("vence", text="Vencimiento")
        self.tabla_inventario.heading("estado", text="Estado")
        self.tabla_inventario.column("medicamento", width=170, anchor=tk.W)
        self.tabla_inventario.column("stock", width=80, anchor=tk.CENTER)
        self.tabla_inventario.column("precio", width=130, anchor=tk.E)
        self.tabla_inventario.column("vence", width=120, anchor=tk.CENTER)
        self.tabla_inventario.column("estado", width=190, anchor=tk.W)
        self.tabla_inventario.tag_configure("normal", background="#ffffff")
        self.tabla_inventario.tag_configure("alerta", background="#fff4e5")
        self.tabla_inventario.tag_configure("critico", background="#fde8e8")
        self.tabla_inventario.bind("<<TreeviewSelect>>", self.usar_medicamento_seleccionado)
        self.tabla_inventario.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=self.tabla_inventario.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tabla_inventario.configure(yscrollcommand=scrollbar.set)

    def actualizar_controles_por_percepcion(self, _event: tk.Event | None = None) -> None:
        percepcion = self.percepcion_var.get().strip()
        es_venta = percibir(percepcion) == ("vender",)
        es_reabastecer = percibir(percepcion) == ("reabastecer",)

        self.cambiar_estado_widgets(self.widgets_venta, es_venta)
        self.cambiar_estado_widgets(self.widgets_reabastecer, es_reabastecer)

    def cambiar_estado_widgets(self, widgets: list[tk.Widget], activo: bool) -> None:
        estado = "normal" if activo else "disabled"
        for widget in widgets:
            if isinstance(widget, ttk.Combobox):
                widget.configure(state="readonly" if activo and widget is self.combo_venta else estado)
            else:
                widget.configure(state=estado)

    def cargar_datos_reabastecimiento(self, _event: tk.Event | None = None) -> None:
        medicamento = normalizar_medicamento(self.reabastecer_medicamento_var.get())
        datos = inventario.get(medicamento)
        if not datos:
            return

        self.reabastecer_precio_var.set(str(datos["precio"]))
        self.reabastecer_vence_var.set(datos["vence"])

    def usar_medicamento_seleccionado(self, _event: tk.Event | None = None) -> None:
        seleccion = self.tabla_inventario.selection()
        if not seleccion:
            return

        valores = self.tabla_inventario.item(seleccion[0], "values")
        if not valores:
            return

        medicamento = valores[0]
        self.venta_medicamento_var.set(medicamento)
        self.reabastecer_medicamento_var.set(medicamento)
        self.cargar_datos_reabastecimiento()

    def ejecutar_ciclo(self) -> None:
        entrada = self.percepcion_var.get().strip()
        percepcion = percibir(entrada)
        regla = decidir(percepcion)

        self.percibir_var.set(str(percepcion) if percepcion else "sin percepcion")
        self.marcar_regla(regla)

        if regla is None:
            self.decidir_var.set("No existe una regla para esa percepcion.")
            self.actuar_var.set("Solicitar una percepcion valida.")
            self.mostrar_resultado("Percepcion no reconocida. Seleccione una regla disponible.")
            self.estado_var.set("Percepcion no reconocida.")
            return

        condicion = ", ".join(regla.condicion)
        self.decidir_var.set(f"SI percepcion = ({condicion}) ENTONCES {regla.descripcion}")
        self.actuar_var.set(f"Ejecutar {regla.accion}")

        try:
            resultado = self.ejecutar_accion(regla.accion)
        except ValueError as exc:
            self.mostrar_resultado(str(exc))
            self.estado_var.set(str(exc))
            messagebox.showerror("Accion no ejecutada", str(exc))
            return

        self.mostrar_resultado(resultado)
        self.actualizar_tablas()
        self.estado_var.set(f"Ciclo ejecutado: {regla.accion}.")

    def ejecutar_accion(self, accion: str) -> str:
        if accion == "accion_consultar_stock":
            return consultar_stock()

        if accion == "accion_alerta_critico":
            return consultar_stock_critico()

        if accion == "accion_vender":
            cantidad = leer_entero_desde_texto(self.venta_cantidad_var.get(), "Cantidad")
            return registrar_venta(self.venta_medicamento_var.get(), cantidad)

        if accion == "accion_reabastecer":
            cantidad = leer_entero_desde_texto(self.reabastecer_cantidad_var.get(), "Cantidad")
            precio = self.leer_precio_opcional()
            vence = self.reabastecer_vence_var.get().strip() or None
            return reabastecer_medicamento(
                self.reabastecer_medicamento_var.get(),
                cantidad,
                precio,
                vence,
            )

        if accion == "accion_alerta_vencimiento":
            return consultar_vencimientos()

        if accion == "accion_reporte_cierre":
            return generar_reporte_cierre()

        raise ValueError("Accion no implementada.")

    def leer_precio_opcional(self) -> int | None:
        valor = self.reabastecer_precio_var.get().strip()
        if not valor:
            return None
        return leer_entero_desde_texto(valor, "Precio")

    def marcar_regla(self, regla: ReglaCondicionAccion | None) -> None:
        self.tabla_reglas.selection_remove(self.tabla_reglas.selection())
        if regla is None:
            return

        item_id = "|".join(regla.condicion)
        if self.tabla_reglas.exists(item_id):
            self.tabla_reglas.selection_set(item_id)
            self.tabla_reglas.focus(item_id)
            self.tabla_reglas.see(item_id)

    def mostrar_resultado(self, texto: str) -> None:
        self.texto_resultado.configure(state=tk.NORMAL)
        self.texto_resultado.delete("1.0", tk.END)
        self.texto_resultado.insert("1.0", texto)
        self.texto_resultado.configure(state=tk.DISABLED)

    def actualizar_tablas(self) -> None:
        self.actualizar_inventario()
        self.actualizar_comboboxes()

    def actualizar_comboboxes(self) -> None:
        medicamentos = sorted(inventario)
        self.combo_venta.configure(values=medicamentos)
        self.combo_reabastecer.configure(values=medicamentos)

        if medicamentos and not self.venta_medicamento_var.get():
            self.venta_medicamento_var.set(medicamentos[0])
        if medicamentos and not self.reabastecer_medicamento_var.get():
            self.reabastecer_medicamento_var.set(medicamentos[0])
            self.cargar_datos_reabastecimiento()

    def actualizar_inventario(self) -> None:
        self.tabla_inventario.delete(*self.tabla_inventario.get_children())

        for nombre, datos in sorted(inventario.items()):
            estado = obtener_estado(datos)
            etiqueta = "normal"
            if "Stock critico" in estado:
                etiqueta = "critico"
            elif estado != "Normal":
                etiqueta = "alerta"

            self.tabla_inventario.insert(
                "",
                tk.END,
                values=(
                    nombre,
                    datos["stock"],
                    formato_cop(datos["precio"]),
                    datos["vence"],
                    estado,
                ),
                tags=(etiqueta,),
            )


def agente_farmacia() -> None:
    root = tk.Tk()
    AgenteFarmaciaApp(root)
    root.mainloop()


if __name__ == "__main__":
    agente_farmacia()
