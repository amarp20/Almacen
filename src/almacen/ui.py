from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from .storage import (
    FIXED_PALLETS,
    create_default_data_file,
    load_inventory,
    load_withdrawal_logs,
    next_equipment_id,
    save_inventory,
    save_withdrawal_logs,
)


class InventoryApp:
    def __init__(self) -> None:
        create_default_data_file()
        self.inventory = load_inventory()
        self.withdrawal_logs = load_withdrawal_logs()
        self.inventory.setdefault("equipment_types", [])
        self.inventory.setdefault("pallets", [])
        self.withdrawal_logs.setdefault("withdrawals", [])

        self.root = tk.Tk()
        self.root.title("Almacén Informático")
        self.root.geometry("1280x820")
        self.root.minsize(1100, 720)
        self.root.configure(bg="#dbe7f3")
        self._icon_image: tk.PhotoImage | None = None
        self._configure_window_icon()

        self.selected_equipment_var = tk.StringVar()
        self.selected_pallet_var = tk.StringVar()
        self.operation_source_pallet_var = tk.StringVar()
        self.operation_equipment_var = tk.StringVar()
        self.withdrawal_who_var = tk.StringVar()
        self.consultation_total_var = tk.StringVar(value="0")
        self.withdrawal_filter_equipment_var = tk.StringVar()
        self.withdrawal_filter_date_var = tk.StringVar()
        self.withdrawal_filter_total_var = tk.StringVar(value="0")

        self._configure_styles()
        self._build_layout()
        self._refresh_all_views()

    def _resource_path(self, relative_path: str) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / relative_path
        return Path(__file__).resolve().parent / relative_path

    def _configure_window_icon(self) -> None:
        png_path = self._resource_path("assets/app_icon.png")
        ico_path = self._resource_path("assets/app_icon.ico")

        if png_path.exists():
            try:
                self._icon_image = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, self._icon_image)
            except tk.TclError:
                self._icon_image = None

        if ico_path.exists():
            try:
                self.root.iconbitmap(default=str(ico_path))
            except tk.TclError:
                pass

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#dbe7f3", foreground="#1e293b")
        style.configure("TNotebook", background="#dbe7f3", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#c8d7e8",
            foreground="#1e293b",
            padding=(12, 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#f8fbff"), ("active", "#d8e5f2")],
            foreground=[("selected", "#0f172a"), ("active", "#0f172a")],
        )
        style.configure("Root.TFrame", background="#dbe7f3")
        style.configure("Panel.TFrame", background="#f8fbff")
        style.configure(
            "PanelTitle.TLabel",
            background="#f8fbff",
            foreground="#0f172a",
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background="#f8fbff",
            foreground="#516275",
            font=("Segoe UI", 10),
        )
        style.configure(
            "SidebarTitle.TLabel",
            background="#eef4fb",
            foreground="#102033",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "SidebarText.TLabel",
            background="#eef4fb",
            foreground="#5b6b7f",
            font=("Segoe UI", 10),
        )
        style.configure(
            "StatValue.TLabel",
            background="#f8fbff",
            foreground="#0f172a",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
            background="#4da3d9",
            foreground="#ffffff",
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#3f95cb"), ("!disabled", "#4da3d9")],
            foreground=[("!disabled", "#ffffff")],
        )
        style.configure(
            "Treeview",
            background="#eef4fb",
            fieldbackground="#eef4fb",
            foreground="#142235",
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#d5e0ec",
            foreground="#102033",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#7fc4eb")],
            foreground=[("selected", "#0f172a")],
        )

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, style="Root.TFrame", padding=10)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        self._build_body(outer)

    def _build_body(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.grid(row=0, column=0, sticky="nsew")

        equipment_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        assign_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        operations_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        consultation_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        withdrawal_logs_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        pallets_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)

        notebook.add(equipment_tab, text="Tipos de equipo")
        notebook.add(assign_tab, text="Asignación a palés")
        notebook.add(operations_tab, text="Operaciones")
        notebook.add(consultation_tab, text="Consulta por palés")
        notebook.add(withdrawal_logs_tab, text="Consulta de retiradas")
        notebook.add(pallets_tab, text="Ubicación de equipos")

        self._build_equipment_tab(equipment_tab)
        self._build_assignments_tab(assign_tab)
        self._build_operations_tab(operations_tab)
        self._build_consultation_tab(consultation_tab)
        self._build_withdrawal_logs_tab(withdrawal_logs_tab)
        self._build_pallets_tab(pallets_tab)

    def _build_equipment_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        form_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        form_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=1, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(form_panel, text="Alta de tipos", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(form_panel, text="Nuevo tipo de equipo", style="PanelTitle.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 16)
        )

        ttk.Label(form_panel, text="Categoría", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.category_entry = ttk.Entry(form_panel, width=30)
        self.category_entry.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Marca", style="Muted.TLabel").grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        self.brand_entry = ttk.Entry(form_panel, width=30)
        self.brand_entry.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Modelo", style="Muted.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.model_entry = ttk.Entry(form_panel, width=30)
        self.model_entry.grid(row=4, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Observaciones", style="Muted.TLabel").grid(
            row=5, column=0, sticky="nw", pady=(0, 4)
        )
        self.notes_text = tk.Text(
            form_panel,
            width=24,
            height=7,
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            borderwidth=1,
            wrap="word",
        )
        self.notes_text.grid(row=5, column=1, sticky="ew", pady=(0, 14))

        button_row = ttk.Frame(form_panel, style="Panel.TFrame")
        button_row.grid(row=6, column=0, columnspan=2, sticky="e")
        ttk.Button(button_row, text="Limpiar", command=self._reset_equipment_form).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            button_row,
            text="Crear tipo de equipo",
            style="Primary.TButton",
            command=self._create_equipment_type,
        ).pack(side="left")
        form_panel.columnconfigure(1, weight=1)

        ttk.Label(list_panel, text="Catálogo", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(list_panel, text="Tipos registrados", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(22, 12)
        )

        columns = ("id", "categoria", "marca", "modelo", "observaciones")
        self.equipment_tree = ttk.Treeview(list_panel, columns=columns, show="headings")
        self.equipment_tree.grid(row=1, column=0, sticky="nsew")

        for column, text, width in [
            ("id", "ID", 100),
            ("categoria", "Categoría", 140),
            ("marca", "Marca", 140),
            ("modelo", "Modelo", 220),
            ("observaciones", "Observaciones", 260),
        ]:
            self.equipment_tree.heading(column, text=text)
            self.equipment_tree.column(column, width=width, anchor="w")

        equipment_scroll = ttk.Scrollbar(
            list_panel, orient="vertical", command=self.equipment_tree.yview
        )
        equipment_scroll.grid(row=1, column=1, sticky="ns")
        equipment_scroll_x = ttk.Scrollbar(
            list_panel, orient="horizontal", command=self.equipment_tree.xview
        )
        equipment_scroll_x.grid(row=2, column=0, sticky="ew")
        self.equipment_tree.configure(yscrollcommand=equipment_scroll.set)
        self.equipment_tree.configure(xscrollcommand=equipment_scroll_x.set)

    def _build_assignments_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        form_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        form_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=1, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(form_panel, text="Asignación", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(form_panel, text="Asignar equipo a palé", style="PanelTitle.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 16)
        )

        ttk.Label(form_panel, text="Equipo", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.equipment_combo = ttk.Combobox(
            form_panel,
            textvariable=self.selected_equipment_var,
            state="readonly",
            width=34,
        )
        self.equipment_combo.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Palé", style="Muted.TLabel").grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        self.assignment_pallet_var = tk.StringVar(value=FIXED_PALLETS[0])
        self.pallet_combo_assign = ttk.Combobox(
            form_panel,
            textvariable=self.assignment_pallet_var,
            values=FIXED_PALLETS,
            state="readonly",
            width=34,
        )
        self.pallet_combo_assign.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Cantidad", style="Muted.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.assignment_quantity = ttk.Spinbox(form_panel, from_=1, to=9999, width=34)
        self.assignment_quantity.set("1")
        self.assignment_quantity.grid(row=4, column=1, sticky="ew", pady=(0, 14))

        ttk.Button(
            form_panel,
            text="Asignar al palé",
            style="Primary.TButton",
            command=self._assign_to_pallet,
        ).grid(row=5, column=0, columnspan=2, sticky="ew")
        form_panel.columnconfigure(1, weight=1)

        ttk.Label(list_panel, text="Movimientos actuales", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(list_panel, text="Asignaciones registradas", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(22, 12)
        )

        columns = ("pale", "id", "categoria", "marca", "modelo", "cantidad")
        self.assignments_tree = ttk.Treeview(list_panel, columns=columns, show="headings")
        self.assignments_tree.grid(row=1, column=0, sticky="nsew")

        for column, text, width in [
            ("pale", "Palé", 120),
            ("id", "ID", 90),
            ("categoria", "Categoría", 130),
            ("marca", "Marca", 130),
            ("modelo", "Modelo", 220),
            ("cantidad", "Cantidad", 90),
        ]:
            self.assignments_tree.heading(column, text=text)
            self.assignments_tree.column(column, width=width, anchor="w")

        assignments_scroll = ttk.Scrollbar(
            list_panel, orient="vertical", command=self.assignments_tree.yview
        )
        assignments_scroll.grid(row=1, column=1, sticky="ns")
        self.assignments_tree.configure(yscrollcommand=assignments_scroll.set)

    def _build_pallets_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=0, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(list_panel, text="Detalle", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(list_panel, text="Ubicación por equipo", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(22, 12)
        )

        columns = (
            "id",
            "categoria",
            "marca",
            "modelo",
            *[f"pale_{pale}" for pale in FIXED_PALLETS],
            "total",
        )
        self.pallet_tree = ttk.Treeview(list_panel, columns=columns, show="headings")
        self.pallet_tree.grid(row=1, column=0, sticky="nsew")

        for column, text, width in [
            ("id", "ID", 100),
            ("categoria", "Categoría", 140),
            ("marca", "Marca", 140),
            ("modelo", "Modelo", 240),
            *[(f"pale_{pale}", f"Palé {pale}", 80) for pale in FIXED_PALLETS],
            ("total", "Total", 90),
        ]:
            self.pallet_tree.heading(column, text=text)
            self.pallet_tree.column(column, width=width, anchor="w")

        pallet_scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.pallet_tree.yview)
        pallet_scroll.grid(row=1, column=1, sticky="ns")
        pallet_scroll_x = ttk.Scrollbar(
            list_panel, orient="horizontal", command=self.pallet_tree.xview
        )
        pallet_scroll_x.grid(row=2, column=0, sticky="ew")
        self.pallet_tree.configure(yscrollcommand=pallet_scroll.set)
        self.pallet_tree.configure(xscrollcommand=pallet_scroll_x.set)

    def _build_operations_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        form_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        form_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=1, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(form_panel, text="Movimientos", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(form_panel, text="Restar o mover stock", style="PanelTitle.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 16)
        )

        ttk.Label(form_panel, text="Palé origen", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.operation_source_pallet_combo = ttk.Combobox(
            form_panel,
            textvariable=self.operation_source_pallet_var,
            state="readonly",
            width=32,
        )
        self.operation_source_pallet_combo.grid(row=2, column=1, sticky="ew", pady=(0, 10))
        self.operation_source_pallet_combo.bind(
            "<<ComboboxSelected>>", self._on_operation_pallet_selected
        )

        ttk.Label(form_panel, text="Equipo", style="Muted.TLabel").grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        self.operation_equipment_combo = ttk.Combobox(
            form_panel,
            textvariable=self.operation_equipment_var,
            state="readonly",
            width=32,
        )
        self.operation_equipment_combo.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Cantidad", style="Muted.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.operation_quantity = ttk.Spinbox(form_panel, from_=1, to=9999, width=32)
        self.operation_quantity.set("1")
        self.operation_quantity.grid(row=4, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Palé destino", style="Muted.TLabel").grid(
            row=5, column=0, sticky="w", pady=(0, 4)
        )
        self.destination_pallet_var = tk.StringVar(value=FIXED_PALLETS[0])
        self.destination_pallet_combo = ttk.Combobox(
            form_panel,
            textvariable=self.destination_pallet_var,
            values=FIXED_PALLETS,
            state="readonly",
            width=32,
        )
        self.destination_pallet_combo.grid(row=5, column=1, sticky="ew", pady=(0, 16))

        ttk.Label(form_panel, text="Quién retira", style="Muted.TLabel").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        self.withdrawal_who_entry = ttk.Entry(
            form_panel,
            textvariable=self.withdrawal_who_var,
            width=32,
        )
        self.withdrawal_who_entry.grid(row=6, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(form_panel, text="Motivo de la retirada", style="Muted.TLabel").grid(
            row=7, column=0, sticky="nw", pady=(0, 4)
        )
        self.withdrawal_reason_text = tk.Text(
            form_panel,
            width=24,
            height=7,
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            borderwidth=1,
            wrap="word",
        )
        self.withdrawal_reason_text.grid(row=7, column=1, sticky="ew", pady=(0, 16))

        ttk.Button(
            form_panel,
            text="Restar del palé",
            command=self._remove_from_pallet,
        ).grid(row=8, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            form_panel,
            text="Mover a otro palé",
            style="Primary.TButton",
            command=self._move_between_pallets,
        ).grid(row=8, column=1, sticky="ew", padx=(6, 0))
        form_panel.columnconfigure(1, weight=1)

        ttk.Label(list_panel, text="Existencias actuales", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(list_panel, text="Stock por palé", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(22, 12)
        )

        columns = ("pale", "id", "categoria", "marca", "modelo", "cantidad")
        self.operations_tree = ttk.Treeview(list_panel, columns=columns, show="headings")
        self.operations_tree.grid(row=1, column=0, sticky="nsew")

        for column, text, width in [
            ("pale", "Palé", 120),
            ("id", "ID", 90),
            ("categoria", "Categoría", 130),
            ("marca", "Marca", 130),
            ("modelo", "Modelo", 220),
            ("cantidad", "Cantidad", 90),
        ]:
            self.operations_tree.heading(column, text=text)
            self.operations_tree.column(column, width=width, anchor="w")

        operations_scroll = ttk.Scrollbar(
            list_panel, orient="vertical", command=self.operations_tree.yview
        )
        operations_scroll.grid(row=1, column=1, sticky="ns")
        self.operations_tree.configure(yscrollcommand=operations_scroll.set)

    def _build_consultation_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=0, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(list_panel, text="Detalle por palés", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        columns = ("pale", "id", "categoria", "marca", "modelo", "cantidad")
        self.consultation_tree = ttk.Treeview(list_panel, columns=columns, show="headings")
        self.consultation_tree.grid(row=1, column=0, sticky="nsew")
        for column, text, width in [
            ("pale", "Palé", 100),
            ("id", "ID", 100),
            ("categoria", "Categoría", 140),
            ("marca", "Marca", 140),
            ("modelo", "Modelo", 220),
            ("cantidad", "Cantidad", 100),
        ]:
            self.consultation_tree.heading(column, text=text)
            self.consultation_tree.column(column, width=width, anchor="w")

        consultation_scroll = ttk.Scrollbar(
            list_panel, orient="vertical", command=self.consultation_tree.yview
        )
        consultation_scroll.grid(row=1, column=1, sticky="ns")
        consultation_scroll_x = ttk.Scrollbar(
            list_panel, orient="horizontal", command=self.consultation_tree.xview
        )
        consultation_scroll_x.grid(row=2, column=0, sticky="ew")
        self.consultation_tree.configure(yscrollcommand=consultation_scroll.set)
        self.consultation_tree.configure(xscrollcommand=consultation_scroll_x.set)
        self.consultation_tree.tag_configure(
            "odd_pallet_group",
            background="#d8e2ee",
            foreground="#102033",
            font=("Segoe UI", 10, "bold"),
        )
        self.consultation_tree.tag_configure(
            "odd_pallet_item",
            background="#ecf2f8",
            foreground="#142235",
        )
        self.consultation_tree.tag_configure(
            "even_pallet_group",
            background="#b7d0e6",
            foreground="#102033",
            font=("Segoe UI", 10, "bold"),
        )
        self.consultation_tree.tag_configure(
            "even_pallet_item",
            background="#dbe9f4",
            foreground="#142235",
        )

    def _build_withdrawal_logs_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        filter_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        filter_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        list_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        list_panel.grid(row=0, column=1, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        ttk.Label(filter_panel, text="Logs", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(filter_panel, text="Consulta de retiradas", style="PanelTitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(6, 16)
        )

        ttk.Label(filter_panel, text="Tipo de equipo", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.withdrawal_filter_equipment_combo = ttk.Combobox(
            filter_panel,
            textvariable=self.withdrawal_filter_equipment_var,
            state="readonly",
            width=34,
        )
        self.withdrawal_filter_equipment_combo.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self.withdrawal_filter_equipment_combo.bind(
            "<<ComboboxSelected>>", self._on_withdrawal_filter_changed
        )

        ttk.Label(
            filter_panel,
            text="Fecha (AAAA-MM-DD)",
            style="Muted.TLabel",
        ).grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.withdrawal_filter_date_entry = ttk.Entry(
            filter_panel,
            textvariable=self.withdrawal_filter_date_var,
            width=34,
        )
        self.withdrawal_filter_date_entry.grid(row=5, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(
            filter_panel,
            text="Aplicar filtros",
            command=self._render_withdrawal_logs_table,
        ).grid(row=6, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(
            filter_panel,
            text="Limpiar filtros",
            command=self._reset_withdrawal_filters,
        ).grid(row=7, column=0, sticky="ew")

        ttk.Label(list_panel, text="Detalle de retiradas", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        columns = (
            "fecha_hora",
            "id",
            "categoria",
            "marca",
            "modelo",
            "pale",
            "cantidad",
            "quien",
            "motivo",
        )
        self.withdrawal_logs_tree = ttk.Treeview(list_panel, columns=columns, show="headings")
        self.withdrawal_logs_tree.grid(row=1, column=0, sticky="nsew")

        for column, text, width in [
            ("fecha_hora", "Fecha y hora", 180),
            ("id", "ID", 90),
            ("categoria", "Categoría", 120),
            ("marca", "Marca", 120),
            ("modelo", "Modelo", 180),
            ("pale", "Palé", 70),
            ("cantidad", "Cantidad", 80),
            ("quien", "Quién retira", 160),
            ("motivo", "Motivo", 280),
        ]:
            self.withdrawal_logs_tree.heading(column, text=text)
            self.withdrawal_logs_tree.column(column, width=width, anchor="w")

        withdrawal_logs_scroll = ttk.Scrollbar(
            list_panel,
            orient="vertical",
            command=self.withdrawal_logs_tree.yview,
        )
        withdrawal_logs_scroll.grid(row=1, column=1, sticky="ns")
        withdrawal_logs_scroll_x = ttk.Scrollbar(
            list_panel,
            orient="horizontal",
            command=self.withdrawal_logs_tree.xview,
        )
        withdrawal_logs_scroll_x.grid(row=2, column=0, sticky="ew")
        self.withdrawal_logs_tree.configure(yscrollcommand=withdrawal_logs_scroll.set)
        self.withdrawal_logs_tree.configure(xscrollcommand=withdrawal_logs_scroll_x.set)

    def _refresh_all_views(self) -> None:
        self._render_equipment_table()
        self._render_assignments_table()
        self._render_operations_table()
        self._refresh_equipment_options()
        self._refresh_withdrawal_filter_options()
        self._refresh_pallet_options()
        self._refresh_operation_options()
        self._render_selected_pallet()
        self._render_consultation_table()
        self._render_withdrawal_logs_table()

    def _render_equipment_table(self) -> None:
        for item_id in self.equipment_tree.get_children():
            self.equipment_tree.delete(item_id)

        for item in self.inventory["equipment_types"]:
            self.equipment_tree.insert(
                "",
                "end",
                values=(
                    item["id"],
                    item["categoria"],
                    item["marca"],
                    item["modelo"],
                    item.get("observaciones", ""),
                ),
            )

    def _render_assignments_table(self) -> None:
        for item_id in self.assignments_tree.get_children():
            self.assignments_tree.delete(item_id)

        for pallet in self.inventory["pallets"]:
            for assigned_item in pallet["items"]:
                equipment = self._find_equipment_by_id(assigned_item["equipment_id"])
                if equipment is None:
                    continue
                self.assignments_tree.insert(
                    "",
                    "end",
                    values=(
                        pallet["pale"],
                        equipment["id"],
                        equipment["categoria"],
                        equipment["marca"],
                        equipment["modelo"],
                        assigned_item["cantidad"],
                    ),
                )

    def _render_selected_pallet(self) -> None:
        for item_id in self.pallet_tree.get_children():
            self.pallet_tree.delete(item_id)

        for equipment in self.inventory["equipment_types"]:
            quantities_by_pallet = {pale: 0 for pale in FIXED_PALLETS}
            total_quantity = 0

            for pallet_name in FIXED_PALLETS:
                pallet_item = self._find_pallet_item(pallet_name, equipment["id"])
                if pallet_item is None:
                    continue

                quantity = int(pallet_item["cantidad"])
                quantities_by_pallet[pallet_name] = quantity
                total_quantity += quantity

            self.pallet_tree.insert(
                "",
                "end",
                values=(
                    equipment["id"],
                    equipment["categoria"],
                    equipment["marca"],
                    equipment["modelo"],
                    *[quantities_by_pallet[pale] for pale in FIXED_PALLETS],
                    total_quantity,
                ),
            )

    def _render_operations_table(self) -> None:
        for item_id in self.operations_tree.get_children():
            self.operations_tree.delete(item_id)

        for pallet in self.inventory["pallets"]:
            for assigned_item in pallet["items"]:
                equipment = self._find_equipment_by_id(assigned_item["equipment_id"])
                if equipment is None:
                    continue
                self.operations_tree.insert(
                    "",
                    "end",
                    values=(
                        pallet["pale"],
                        equipment["id"],
                        equipment["categoria"],
                        equipment["marca"],
                        equipment["modelo"],
                        assigned_item["cantidad"],
                    ),
                )

    def _refresh_equipment_options(self) -> None:
        values = [self._equipment_label(item) for item in self.inventory["equipment_types"]]
        self.equipment_combo["values"] = values
        if values and self.selected_equipment_var.get() not in values:
            self.selected_equipment_var.set(values[0])
        if not values:
            self.selected_equipment_var.set("")

    def _refresh_consultation_options(self) -> None:
        return

    def _refresh_withdrawal_filter_options(self) -> None:
        values = ["Todos"] + [
            self._equipment_label(item) for item in self.inventory["equipment_types"]
        ]
        self.withdrawal_filter_equipment_combo["values"] = values
        if self.withdrawal_filter_equipment_var.get() not in values:
            self.withdrawal_filter_equipment_var.set(values[0] if values else "")

    def _refresh_pallet_options(self) -> None:
        return

    def _refresh_operation_options(self) -> None:
        pallet_names = list(FIXED_PALLETS)
        self.operation_source_pallet_combo["values"] = pallet_names

        if pallet_names and self.operation_source_pallet_var.get() not in pallet_names:
            self.operation_source_pallet_var.set(pallet_names[0])
        if not pallet_names:
            self.operation_source_pallet_var.set("")

        self._refresh_operation_equipment_options()

    def _refresh_operation_equipment_options(self) -> None:
        pallet_name = self.operation_source_pallet_var.get().strip()
        pallet = self._find_pallet(pallet_name)
        values: list[str] = []

        if pallet is not None:
            for assigned_item in pallet["items"]:
                equipment = self._find_equipment_by_id(assigned_item["equipment_id"])
                if equipment is None:
                    continue
                values.append(
                    f'{equipment["id"]} | {equipment["categoria"]} | '
                    f'{equipment["marca"]} | {equipment["modelo"]} | '
                    f'Cantidad: {assigned_item["cantidad"]}'
                )

        self.operation_equipment_combo["values"] = values
        if values and self.operation_equipment_var.get() not in values:
            self.operation_equipment_var.set(values[0])
        if not values:
            self.operation_equipment_var.set("")

    def _equipment_label(self, item: dict[str, str]) -> str:
        return f'{item["id"]} | {item["categoria"]} | {item["marca"]} | {item["modelo"]}'

    def _render_consultation_table(self) -> None:
        for item_id in self.consultation_tree.get_children():
            self.consultation_tree.delete(item_id)

        total_quantity = 0
        pallets_with_stock = 0

        for pallet in self.inventory["pallets"]:
            pallet_rows = []
            pallet_total = 0
            for assigned_item in pallet["items"]:
                equipment = self._find_equipment_by_id(assigned_item["equipment_id"])
                if equipment is None:
                    continue

                quantity = int(assigned_item["cantidad"])
                total_quantity += quantity
                pallet_total += quantity
                pallet_rows.append(
                    (
                        pallet["pale"],
                        equipment["id"],
                        equipment["categoria"],
                        equipment["marca"],
                        equipment["modelo"],
                        quantity,
                    )
                )

            if not pallet_rows:
                continue

            pallets_with_stock += 1
            pallet_number = int(pallet["pale"])
            if pallet_number % 2 == 0:
                group_tag = "even_pallet_group"
                item_tag = "even_pallet_item"
            else:
                group_tag = "odd_pallet_group"
                item_tag = "odd_pallet_item"

            self.consultation_tree.insert(
                "",
                "end",
                values=(
                    f'Palé {pallet["pale"]}',
                    "",
                    "",
                    "",
                    "Subtotal",
                    pallet_total,
                ),
                tags=(group_tag,),
            )
            for row_values in pallet_rows:
                self.consultation_tree.insert("", "end", values=row_values, tags=(item_tag,))

        if pallets_with_stock == 0:
            self.consultation_tree.insert(
                "",
                "end",
                values=("-", "-", "Sin stock", "-", "-", 0),
            )

        self.consultation_total_var.set(str(total_quantity))

    def _render_withdrawal_logs_table(self) -> None:
        for item_id in self.withdrawal_logs_tree.get_children():
            self.withdrawal_logs_tree.delete(item_id)

        selected_equipment = self.withdrawal_filter_equipment_var.get().strip()
        selected_date = self.withdrawal_filter_date_var.get().strip()
        equipment_id = ""
        if selected_equipment and selected_equipment != "Todos":
            equipment_id = selected_equipment.split("|", maxsplit=1)[0].strip()

        matches = []
        for entry in reversed(self.withdrawal_logs.get("withdrawals", [])):
            if equipment_id and entry.get("equipment_id", "") != equipment_id:
                continue
            if selected_date and entry.get("date", "") != selected_date:
                continue
            matches.append(entry)

        for entry in matches:
            self.withdrawal_logs_tree.insert(
                "",
                "end",
                values=(
                    entry.get("timestamp", ""),
                    entry.get("equipment_id", ""),
                    entry.get("categoria", ""),
                    entry.get("marca", ""),
                    entry.get("modelo", ""),
                    entry.get("pale", ""),
                    entry.get("cantidad", 0),
                    entry.get("quien_retira", ""),
                    entry.get("motivo_retirada", ""),
                ),
            )

        self.withdrawal_filter_total_var.set(str(len(matches)))

    def _find_equipment_by_id(self, equipment_id: str) -> dict[str, str] | None:
        for item in self.inventory["equipment_types"]:
            if item["id"] == equipment_id:
                return item
        return None

    def _find_pallet(self, pallet_name: str) -> dict[str, object] | None:
        for pallet in self.inventory["pallets"]:
            if pallet["pale"].lower() == pallet_name.lower():
                return pallet
        return None

    def _find_pallet_item(self, pallet_name: str, equipment_id: str) -> dict[str, object] | None:
        pallet = self._find_pallet(pallet_name)
        if pallet is None:
            return None

        for assigned_item in pallet["items"]:
            if assigned_item["equipment_id"] == equipment_id:
                return assigned_item
        return None

    def _cleanup_empty_pallets(self) -> None:
        cleaned_pallets = []
        for pallet_name in FIXED_PALLETS:
            pallet = self._find_pallet(pallet_name)
            items = []
            if pallet is not None:
                items = [
                    item for item in pallet["items"] if int(item.get("cantidad", 0)) > 0
                ]
            cleaned_pallets.append({"pale": pallet_name, "items": items})
        self.inventory["pallets"] = cleaned_pallets

    def _equipment_type_exists(self, categoria: str, marca: str, modelo: str) -> bool:
        expected = (categoria.strip().lower(), marca.strip().lower(), modelo.strip().lower())
        for item in self.inventory["equipment_types"]:
            current = (
                item["categoria"].strip().lower(),
                item["marca"].strip().lower(),
                item["modelo"].strip().lower(),
            )
            if current == expected:
                return True
        return False

    def _create_equipment_type(self) -> None:
        categoria = self.category_entry.get().strip()
        marca = self.brand_entry.get().strip()
        modelo = self.model_entry.get().strip()
        observaciones = self.notes_text.get("1.0", "end").strip()

        if not categoria or not marca or not modelo:
            messagebox.showwarning(
                "Campos obligatorios",
                "Completa categoría, marca y modelo para crear un tipo de equipo.",
            )
            return

        if self._equipment_type_exists(categoria, marca, modelo):
            messagebox.showwarning(
                "Equipo existente",
                "Ese tipo de equipo ya existe en el catálogo.",
            )
            return

        new_item = {
            "id": next_equipment_id(self.inventory),
            "categoria": categoria,
            "marca": marca,
            "modelo": modelo,
            "observaciones": observaciones,
        }
        self.inventory["equipment_types"].append(new_item)
        self._save_inventory(show_message=False)
        self._refresh_all_views()
        self._reset_equipment_form()
        messagebox.showinfo(
            "Tipo creado",
            f'Se ha creado el equipo {new_item["id"]}: {categoria} {marca} {modelo}.',
        )

    def _reset_equipment_form(self) -> None:
        self.category_entry.delete(0, "end")
        self.brand_entry.delete(0, "end")
        self.model_entry.delete(0, "end")
        self.notes_text.delete("1.0", "end")

    def _assign_to_pallet(self) -> None:
        selected_label = self.selected_equipment_var.get().strip()
        pallet_name = self.assignment_pallet_var.get().strip()

        if not selected_label:
            messagebox.showwarning(
                "Equipo requerido",
                "Selecciona un tipo de equipo antes de asignarlo a un palé.",
            )
            return

        if not pallet_name:
            messagebox.showwarning(
                "Palé requerido",
                "Indica el palé al que quieres asignar el equipo.",
            )
            return

        try:
            quantity = int(self.assignment_quantity.get().strip())
        except ValueError:
            messagebox.showerror("Cantidad inválida", "La cantidad debe ser un número entero.")
            return

        if quantity <= 0:
            messagebox.showwarning(
                "Cantidad inválida",
                "La cantidad debe ser mayor que cero.",
            )
            return

        equipment_id = selected_label.split("|", maxsplit=1)[0].strip()
        pallet = self._find_pallet(pallet_name)
        if pallet is None:
            pallet = {"pale": pallet_name, "items": []}
            self.inventory["pallets"].append(pallet)

        total_quantity = quantity
        for assigned_item in pallet["items"]:
            if assigned_item["equipment_id"] == equipment_id:
                total_quantity = int(assigned_item["cantidad"]) + quantity
                assigned_item["cantidad"] = total_quantity
                break
        else:
            pallet["items"].append({"equipment_id": equipment_id, "cantidad": quantity})

        self._save_inventory(show_message=False)
        self.assignment_quantity.set("1")
        self.selected_pallet_var.set(pallet_name)
        self._refresh_all_views()
        messagebox.showinfo(
            "Asignación guardada",
            f"Se han añadido {quantity} unidades de {equipment_id} al palé {pallet_name}. "
            f"Total en el palé: {total_quantity}.",
        )

    def _parse_operation_selection(self) -> tuple[str, str, int] | None:
        pallet_name = self.operation_source_pallet_var.get().strip()
        selection = self.operation_equipment_var.get().strip()

        if not pallet_name or not selection:
            messagebox.showwarning(
                "Datos incompletos",
                "Selecciona un palé origen y un equipo antes de realizar la operación.",
            )
            return None

        try:
            quantity = int(self.operation_quantity.get().strip())
        except ValueError:
            messagebox.showerror("Cantidad inválida", "La cantidad debe ser un número entero.")
            return None

        if quantity <= 0:
            messagebox.showwarning(
                "Cantidad inválida",
                "La cantidad debe ser mayor que cero.",
            )
            return None

        equipment_id = selection.split("|", maxsplit=1)[0].strip()
        pallet_item = self._find_pallet_item(pallet_name, equipment_id)
        if pallet_item is None:
            messagebox.showwarning(
                "Equipo no encontrado",
                "Ese equipo ya no existe en el palé seleccionado.",
            )
            return None

        available_quantity = int(pallet_item["cantidad"])
        if quantity > available_quantity:
            messagebox.showwarning(
                "Cantidad insuficiente",
                f"No puedes mover o restar {quantity} unidades porque solo hay {available_quantity}.",
            )
            return None

        return pallet_name, equipment_id, quantity

    def _get_withdrawal_details(self) -> tuple[str, str] | None:
        who = self.withdrawal_who_var.get().strip()
        reason = self.withdrawal_reason_text.get("1.0", "end").strip()

        if not who:
            messagebox.showwarning(
                "Dato obligatorio",
                'Indica "Quién retira" para registrar la retirada.',
            )
            return None

        if not reason:
            messagebox.showwarning(
                "Dato obligatorio",
                'Indica el "Motivo de la retirada" para registrar la retirada.',
            )
            return None

        return who, reason

    def _register_withdrawal_log(
        self,
        pallet_name: str,
        equipment_id: str,
        quantity: int,
        who: str,
        reason: str,
    ) -> None:
        equipment = self._find_equipment_by_id(equipment_id)
        timestamp = datetime.now().astimezone()
        entry = {
            "timestamp": timestamp.isoformat(timespec="seconds"),
            "date": timestamp.date().isoformat(),
            "equipment_id": equipment_id,
            "categoria": equipment["categoria"] if equipment else "",
            "marca": equipment["marca"] if equipment else "",
            "modelo": equipment["modelo"] if equipment else "",
            "pale": pallet_name,
            "cantidad": quantity,
            "quien_retira": who,
            "motivo_retirada": reason,
        }
        self.withdrawal_logs["meta"]["last_updated"] = datetime.now(UTC).isoformat()
        self.withdrawal_logs.setdefault("withdrawals", []).append(entry)
        save_withdrawal_logs(self.withdrawal_logs)

    def _reset_withdrawal_form(self) -> None:
        self.withdrawal_who_var.set("")
        self.withdrawal_reason_text.delete("1.0", "end")

    def _reset_withdrawal_filters(self) -> None:
        self.withdrawal_filter_equipment_var.set("Todos")
        self.withdrawal_filter_date_var.set("")
        self._render_withdrawal_logs_table()

    def _remove_from_pallet(self) -> None:
        parsed = self._parse_operation_selection()
        if parsed is None:
            return

        withdrawal_details = self._get_withdrawal_details()
        if withdrawal_details is None:
            return

        pallet_name, equipment_id, quantity = parsed
        who, reason = withdrawal_details
        pallet_item = self._find_pallet_item(pallet_name, equipment_id)
        if pallet_item is None:
            return

        pallet_item["cantidad"] = int(pallet_item["cantidad"]) - quantity
        self._cleanup_empty_pallets()
        self._save_inventory(show_message=False)
        self._register_withdrawal_log(pallet_name, equipment_id, quantity, who, reason)
        self.operation_quantity.set("1")
        self.destination_pallet_var.set(FIXED_PALLETS[0])
        self._reset_withdrawal_form()
        self._refresh_all_views()
        messagebox.showinfo(
            "Stock actualizado",
            f"Se han restado {quantity} unidades de {equipment_id} del palé {pallet_name}.",
        )

    def _move_between_pallets(self) -> None:
        parsed = self._parse_operation_selection()
        if parsed is None:
            return

        source_pallet, equipment_id, quantity = parsed
        destination_pallet = self.destination_pallet_var.get().strip()

        if not destination_pallet:
            messagebox.showwarning(
                "Destino requerido",
                "Indica el palé de destino para mover el stock.",
            )
            return

        if destination_pallet.lower() == source_pallet.lower():
            messagebox.showwarning(
                "Destino invalido",
                "El palé de destino debe ser distinto del palé origen.",
            )
            return

        source_item = self._find_pallet_item(source_pallet, equipment_id)
        if source_item is None:
            return

        source_item["cantidad"] = int(source_item["cantidad"]) - quantity

        destination = self._find_pallet(destination_pallet)
        if destination is None:
            destination = {"pale": destination_pallet, "items": []}
            self.inventory["pallets"].append(destination)

        for assigned_item in destination["items"]:
            if assigned_item["equipment_id"] == equipment_id:
                assigned_item["cantidad"] = int(assigned_item["cantidad"]) + quantity
                break
        else:
            destination["items"].append({"equipment_id": equipment_id, "cantidad": quantity})

        self._cleanup_empty_pallets()
        self._save_inventory(show_message=False)
        self.operation_quantity.set("1")
        self.destination_pallet_var.set(FIXED_PALLETS[0])
        self.selected_pallet_var.set(destination_pallet)
        self._refresh_all_views()
        messagebox.showinfo(
            "Movimiento realizado",
            f"Se han movido {quantity} unidades de {equipment_id} desde {source_pallet} a {destination_pallet}.",
        )

    def _on_operation_pallet_selected(self, _event: object) -> None:
        self._refresh_operation_equipment_options()

    def _on_consultation_equipment_selected(self, _event: object) -> None:
        self._render_consultation_table()

    def _on_withdrawal_filter_changed(self, _event: object) -> None:
        self._render_withdrawal_logs_table()

    def _on_pallet_selected(self, _event: object) -> None:
        self._render_selected_pallet()

    def _save_inventory(self, show_message: bool = True) -> None:
        self.inventory["meta"]["last_updated"] = datetime.now(UTC).isoformat()
        save_inventory(self.inventory)

        if show_message:
            messagebox.showinfo("Guardado", "Inventario guardado correctamente.")

    def run(self) -> None:
        self.root.mainloop()



