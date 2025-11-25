import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from Instruction import Instruction, Op
from TOMASSULLLERoriSimulator import TOMASSULLLERoriSimulator


class TOMASSULLLERoriGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador do Algoritmo de Tomasulo - Versão Melhorada")
        self.root.geometry("1600x950")
        self.root.configure(bg="#f0f0f0")

        self.simulator = None
        self.auto_run_active = False
        self.auto_run_speed = 500  # ms entre ciclos

        # Esquema de cores
        self.colors = {
            'bg_main': '#f0f0f0',
            'bg_panel': '#ffffff',
            'bg_config': '#e8f4f8',
            'btn_primary': '#4CAF50',
            'btn_secondary': '#2196F3',
            'btn_warning': '#FF9800',
            'btn_danger': '#f44336',
            'text_dark': '#212121',
            'text_light': '#757575',

            # Estados das instruções
            'state_waiting': '#FFF9C4',      # Amarelo claro - Esperando
            'state_issue': '#B3E5FC',        # Azul claro - Issue
            'state_exec': '#81D4FA',         # Azul médio - Executando
            'state_write': '#4FC3F7',        # Azul - Write Result
            'state_commit': '#C8E6C9',       # Verde claro - Commit
            'state_squashed': '#FFCDD2',     # Vermelho claro - Descartada
            'state_speculative': '#FFE082',  # Laranja claro - Especulativa

            # Estados das RSs
            'rs_free': '#E8F5E9',            # Verde muito claro - Livre
            'rs_busy': '#FFEBEE',            # Vermelho claro - Ocupada
            'rs_ready': '#FFF3E0',           # Laranja claro - Pronta para executar
            'rs_executing': '#E3F2FD',       # Azul claro - Executando
        }

        self.init_components()
        self.add_listeners()
        self.update_ui(False)

    def init_components(self):
        # Container principal com scrollbar
        main_container = tk.Frame(self.root, bg=self.colors['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Divide em duas colunas principais
        left_column = tk.Frame(main_container, bg=self.colors['bg_main'], width=350)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        left_column.pack_propagate(False)

        right_column = tk.Frame(main_container, bg=self.colors['bg_main'])
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== COLUNA ESQUERDA =====
        self.create_config_panel(left_column)
        self.create_input_panel(left_column)

        # ===== COLUNA DIREITA =====
        self.create_control_panel(right_column)
        self.create_visualization_panels(right_column)

    def create_config_panel(self, parent):
        """Painel de configuração"""
        config_frame = tk.LabelFrame(parent, text="⚙️ Configurações do Simulador",
                                     font=("Arial", 11, "bold"), bg=self.colors['bg_config'],
                                     relief=tk.RIDGE, borderwidth=2)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Unidades Funcionais
        fu_frame = tk.LabelFrame(config_frame, text="Unidades Funcionais",
                                font=("Arial", 9, "bold"), bg=self.colors['bg_config'])
        fu_frame.pack(fill=tk.X, padx=10, pady=5)

        fu_entries = [
            ("ADD/SUB:", "fu_add", "1"),
            ("LOAD/STORE:", "fu_store", "1"),
            ("MUL/DIV:", "fu_mult", "1"),
            ("BRANCH:", "fu_branch", "1")
        ]

        for i, (label, attr, default) in enumerate(fu_entries):
            tk.Label(fu_frame, text=label, bg=self.colors['bg_config'],
                    font=("Arial", 9)).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            entry = tk.Entry(fu_frame, width=8, font=("Arial", 9))
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=2)
            setattr(self, attr, entry)

        # Latências
        lat_frame = tk.LabelFrame(config_frame, text="Latências (Ciclos)",
                                 font=("Arial", 9, "bold"), bg=self.colors['bg_config'])
        lat_frame.pack(fill=tk.X, padx=10, pady=5)

        lat_entries = [
            ("ADD/SUB:", "lat_add", "2"),
            ("LOAD:", "lat_load", "6"),
            ("STORE:", "lat_store", "6"),
            ("MUL:", "lat_mult", "3"),
            ("DIV:", "lat_div", "3"),
            ("BRANCH:", "lat_branch", "4")
        ]

        for i, (label, attr, default) in enumerate(lat_entries):
            tk.Label(lat_frame, text=label, bg=self.colors['bg_config'],
                    font=("Arial", 9)).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            entry = tk.Entry(lat_frame, width=8, font=("Arial", 9))
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=2)
            setattr(self, attr, entry)

        # Botão configurar
        self.setup_simulator_button = tk.Button(
            config_frame, text="🔧 Configurar Simulador",
            bg=self.colors['btn_secondary'], fg="white",
            font=("Arial", 10, "bold"), relief=tk.RAISED, cursor="hand2"
        )
        self.setup_simulator_button.pack(pady=10, padx=10, fill=tk.X)

    def create_input_panel(self, parent):
        """Painel de entrada de código"""
        input_frame = tk.LabelFrame(parent, text="📝 Carregar Instruções",
                                   font=("Arial", 11, "bold"), bg=self.colors['bg_panel'],
                                   relief=tk.RIDGE, borderwidth=2)
        input_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(input_frame, text="Cole as instruções (uma por linha):",
                font=("Arial", 9, "bold"), bg=self.colors['bg_panel']).pack(anchor=tk.W, padx=5, pady=(5, 0))
        tk.Label(input_frame, text="Formato: OP DEST SRC1 SRC2",
                font=("Arial", 8), fg=self.colors['text_light'], bg=self.colors['bg_panel']).pack(anchor=tk.W, padx=5)
        tk.Label(input_frame, text="Exemplo: ADD R1 R2 R3",
                font=("Arial", 8), fg=self.colors['text_light'], bg=self.colors['bg_panel']).pack(anchor=tk.W, padx=5)

        self.paste_text_area = scrolledtext.ScrolledText(
            input_frame, width=35, height=15, font=("Courier New", 9),
            bg="#fafafa", relief=tk.SUNKEN, borderwidth=2
        )
        self.paste_text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Texto de exemplo
        example_text = "# Exemplo de programa:\nADD R1 R2 R3\nMUL R4 R1 R5\nSUB R6 R4 R2\n"
        self.paste_text_area.insert("1.0", example_text)

        # Botões
        btn_frame = tk.Frame(input_frame, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.load_from_paste_button = tk.Button(
            btn_frame, text="▶️ Iniciar Simulação",
            bg=self.colors['btn_primary'], fg="white",
            font=("Arial", 9, "bold"), cursor="hand2"
        )
        self.load_from_paste_button.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        self.clear_paste_button = tk.Button(
            btn_frame, text="🗑️ Limpar",
            bg=self.colors['btn_warning'], fg="white",
            font=("Arial", 9, "bold"), cursor="hand2"
        )
        self.clear_paste_button.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

    def create_control_panel(self, parent):
        """Painel de controle da simulação"""
        control_frame = tk.LabelFrame(parent, text="🎮 Controles da Simulação",
                                     font=("Arial", 12, "bold"), bg=self.colors['bg_panel'],
                                     relief=tk.RIDGE, borderwidth=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Linha 1: Clock e estado
        info_frame = tk.Frame(control_frame, bg=self.colors['bg_panel'])
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        self.clock_label = tk.Label(
            info_frame, text="🕐 Clock: 0",
            font=("Arial", 16, "bold"), fg=self.colors['btn_secondary'],
            bg=self.colors['bg_panel']
        )
        self.clock_label.pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(
            info_frame, text="⏸️ Aguardando configuração",
            font=("Arial", 11), fg=self.colors['text_light'],
            bg=self.colors['bg_panel']
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Linha 2: Botões de controle
        btn_frame = tk.Frame(control_frame, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.step_back_button = tk.Button(
            btn_frame, text="⏮️ Voltar",
            bg=self.colors['btn_secondary'], fg="white",
            font=("Arial", 10, "bold"), cursor="hand2", state=tk.DISABLED
        )
        self.step_back_button.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.next_cycle_button = tk.Button(
            btn_frame, text="⏭️ Próximo Ciclo",
            bg=self.colors['btn_primary'], fg="white",
            font=("Arial", 10, "bold"), cursor="hand2"
        )
        self.next_cycle_button.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.auto_run_button = tk.Button(
            btn_frame, text="⏯️ Auto Executar",
            bg=self.colors['btn_warning'], fg="white",
            font=("Arial", 10, "bold"), cursor="hand2"
        )
        self.auto_run_button.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.run_to_end_button = tk.Button(
            btn_frame, text="⏩ Executar Tudo",
            bg=self.colors['btn_danger'], fg="white",
            font=("Arial", 10, "bold"), cursor="hand2"
        )
        self.run_to_end_button.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        # Speed control para auto-run
        speed_frame = tk.Frame(control_frame, bg=self.colors['bg_panel'])
        speed_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(speed_frame, text="Velocidade Auto-Execução:",
                font=("Arial", 9), bg=self.colors['bg_panel']).pack(side=tk.LEFT, padx=5)

        self.speed_slider = tk.Scale(
            speed_frame, from_=100, to=2000, orient=tk.HORIZONTAL,
            bg=self.colors['bg_panel'], length=200,
            command=self.update_speed
        )
        self.speed_slider.set(500)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        self.speed_label = tk.Label(speed_frame, text="500ms",
                                    font=("Arial", 9), bg=self.colors['bg_panel'])
        self.speed_label.pack(side=tk.LEFT, padx=5)

        # Métricas
        self.metrics_frame = tk.Frame(control_frame, bg="#e3f2fd", relief=tk.SUNKEN, borderwidth=2)
        self.metrics_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.metrics_label = tk.Label(
            self.metrics_frame,
            text="📊 IPC: N/A | Ciclos: 0 | Bolhas: 0 | Especulativas: 0 | Descartadas: 0",
            font=("Arial", 10, "bold"), fg=self.colors['text_dark'],
            bg="#e3f2fd", pady=8
        )
        self.metrics_label.pack()

    def create_visualization_panels(self, parent):
        """Painéis de visualização - TUDO VISÍVEL (sem abas)"""
        # Instruções no topo (40% altura)
        instr_frame = tk.LabelFrame(parent, text="📋 Status das Instruções",
                                   font=("Arial", 12, "bold"), bg=self.colors['bg_panel'])
        instr_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.create_instruction_table(instr_frame)

        # Frame inferior para RSs e Registradores lado a lado
        bottom_frame = tk.Frame(parent, bg=self.colors['bg_main'])
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # RSs à esquerda (50%)
        rs_frame = tk.LabelFrame(bottom_frame, text="🔧 Estações de Reserva",
                                font=("Arial", 12, "bold"), bg=self.colors['bg_panel'])
        rs_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
        self.create_rs_table(rs_frame)

        # Registradores à direita (50%)
        reg_frame = tk.LabelFrame(bottom_frame, text="📝 Register File",
                                 font=("Arial", 12, "bold"), bg=self.colors['bg_panel'])
        reg_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(3, 0))
        self.create_register_table(reg_frame)

        # Legenda compacta no rodapé
        self.create_compact_legend(parent)

    def create_instruction_table(self, parent):
        """Tabela de instruções com cores"""
        # Frame para a tabela
        table_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("ID", "Op", "Dest", "Src1", "Src2", "Issue", "Exec Start",
                  "Exec End", "Write", "Commit", "Estado", "Especulativa")

        self.instruction_status_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )

        # Configurar colunas
        widths = {"ID": 40, "Op": 50, "Dest": 50, "Src1": 50, "Src2": 50,
                 "Issue": 50, "Exec Start": 80, "Exec End": 70, "Write": 50,
                 "Commit": 60, "Estado": 100, "Especulativa": 90}

        for col in columns:
            self.instruction_status_table.heading(col, text=col)
            self.instruction_status_table.column(col, width=widths.get(col, 70), anchor=tk.CENTER)

        # Scrollbars
        vsb = tk.Scrollbar(table_frame, orient=tk.VERTICAL,
                          command=self.instruction_status_table.yview)
        hsb = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL,
                          command=self.instruction_status_table.xview)
        self.instruction_status_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.instruction_status_table.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Configurar tags de cores
        self.instruction_status_table.tag_configure('waiting', background=self.colors['state_waiting'])
        self.instruction_status_table.tag_configure('issue', background=self.colors['state_issue'])
        self.instruction_status_table.tag_configure('exec', background=self.colors['state_exec'])
        self.instruction_status_table.tag_configure('write', background=self.colors['state_write'])
        self.instruction_status_table.tag_configure('commit', background=self.colors['state_commit'])
        self.instruction_status_table.tag_configure('squashed', background=self.colors['state_squashed'])
        self.instruction_status_table.tag_configure('speculative', background=self.colors['state_speculative'])

    def create_rs_table(self, parent):
        """Tabela de Reservation Stations"""
        table_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Nome", "Estado", "Op", "Vj", "Vk", "Qj", "Qk", "Ciclos Restantes")

        self.rs_status_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )

        for col in columns:
            self.rs_status_table.heading(col, text=col)
            self.rs_status_table.column(col, width=100, anchor=tk.CENTER)

        vsb = tk.Scrollbar(table_frame, orient=tk.VERTICAL,
                          command=self.rs_status_table.yview)
        self.rs_status_table.configure(yscrollcommand=vsb.set)

        self.rs_status_table.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Tags de cores
        self.rs_status_table.tag_configure('free', background=self.colors['rs_free'])
        self.rs_status_table.tag_configure('busy', background=self.colors['rs_busy'])
        self.rs_status_table.tag_configure('ready', background=self.colors['rs_ready'])
        self.rs_status_table.tag_configure('executing', background=self.colors['rs_executing'])

    def create_register_table(self, parent):
        """Tabela de Register File"""
        table_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Registrador", "Valor", "Produtor (RAT)", "Status")

        self.register_file_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )

        for col in columns:
            self.register_file_table.heading(col, text=col)
            self.register_file_table.column(col, width=150, anchor=tk.CENTER)

        vsb = tk.Scrollbar(table_frame, orient=tk.VERTICAL,
                          command=self.register_file_table.yview)
        self.register_file_table.configure(yscrollcommand=vsb.set)

        self.register_file_table.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Tags
        self.register_file_table.tag_configure('ready', background='#C8E6C9')
        self.register_file_table.tag_configure('waiting', background='#FFE082')

    def create_compact_legend(self, parent):
        """Legenda compacta no rodapé"""
        legend_frame = tk.Frame(parent, bg='#263238', height=60)
        legend_frame.pack(fill=tk.X, padx=5, pady=5)
        legend_frame.pack_propagate(False)

        tk.Label(legend_frame, text="🎨 CORES:", font=("Arial", 10, "bold"),
                bg='#263238', fg='white').pack(side=tk.LEFT, padx=10)

        legend_items = [
            ("🟨 Aguard", self.colors['state_waiting']),
            ("🟦 Issue", self.colors['state_issue']),
            ("🟦 Exec", self.colors['state_exec']),
            ("🟩 Commit", self.colors['state_commit']),
            ("🟧 Espec", self.colors['state_speculative']),
            ("🟥 Desc", self.colors['state_squashed']),
        ]

        for text, color in legend_items:
            label = tk.Label(legend_frame, text=text, font=("Arial", 9, "bold"),
                           bg=color, fg="black", relief=tk.RAISED, padx=8, pady=3)
            label.pack(side=tk.LEFT, padx=3)

    def create_legend_old(self, parent):
        """Legenda de cores (versão antiga - não usada)"""
        legend_text = tk.Text(parent, font=("Arial", 10), bg=self.colors['bg_panel'],
                             relief=tk.FLAT, wrap=tk.WORD)
        legend_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        legend_content = """
🎨 LEGENDA DE CORES DO SIMULADOR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 INSTRUÇÕES:

🟨 Amarelo Claro - Instrução esperando ser despachada (Issue)
🟦 Azul Claro - Instrução foi despachada (Issue feito)
🟦 Azul Médio - Instrução executando
🟦 Azul Escuro - Write Result completo
🟩 Verde Claro - Commit completo (instrução finalizada)
🟧 Laranja Claro - Instrução especulativa (após branch não resolvido)
🟥 Vermelho Claro - Instrução descartada (squashed)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 ESTAÇÕES DE RESERVA:

🟩 Verde Muito Claro - RS livre (disponível)
🟥 Vermelho Claro - RS ocupada mas esperando operandos
🟧 Laranja Claro - RS pronta para executar (operandos disponíveis)
🟦 Azul Claro - RS executando operação

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 REGISTRADORES:

🟩 Verde Claro - Valor pronto (sem dependências)
🟧 Laranja Claro - Esperando resultado de RS (RAT apontando)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 DICAS:

• Use "Próximo Ciclo" para ver passo a passo
• Use "Auto Executar" para ver em tempo real (ajuste a velocidade)
• Use "Voltar" para revisar ciclos anteriores
• Observe as cores mudando conforme o pipeline avança!
• Instruções especulativas aparecem após branches não resolvidos
• Instruções descartadas (squashed) são em vermelho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        legend_text.insert("1.0", legend_content)
        legend_text.configure(state=tk.DISABLED)

    def add_listeners(self):
        """Adiciona event listeners"""
        self.setup_simulator_button.config(command=self.setup_simulator)
        self.next_cycle_button.config(command=self.next_cycle)
        self.step_back_button.config(command=self.step_back)
        self.run_to_end_button.config(command=self.run_to_end)
        self.auto_run_button.config(command=self.toggle_auto_run)
        self.load_from_paste_button.config(command=self.load_from_paste)
        self.clear_paste_button.config(command=self.clear_paste)

    def update_speed(self, value):
        """Atualiza velocidade da auto-execução"""
        self.auto_run_speed = int(float(value))
        self.speed_label.config(text=f"{self.auto_run_speed}ms")

    def setup_simulator(self):
        """Configura o simulador"""
        try:
            add = int(self.fu_add.get())
            store = int(self.fu_store.get())
            mult = int(self.fu_mult.get())
            branch = int(self.fu_branch.get())

            lat_add = int(self.lat_add.get())
            lat_load = int(self.lat_load.get())
            lat_store = int(self.lat_store.get())
            lat_mult = int(self.lat_mult.get())
            lat_div = int(self.lat_div.get())
            lat_branch = int(self.lat_branch.get())

            self.simulator = TOMASSULLLERoriSimulator(
                add, store, mult, branch,
                lat_add, lat_load, lat_store, lat_mult, lat_div, lat_branch
            )

            messagebox.showinfo("✅ Sucesso",
                              "Simulador configurado! Agora carregue as instruções.")
            self.status_label.config(text="⏸️ Configurado - Carregue instruções")
            self.update_ui(False)
        except ValueError:
            messagebox.showerror("❌ Erro",
                               "Por favor, insira números válidos.")

    def next_cycle(self):
        """Avança um ciclo"""
        if self.simulator is not None:
            self.simulator.next_cycle()
            self.update_tables()
            self.update_metrics()

            if self.simulator.is_simulation_finished():
                self.status_label.config(text="✅ Simulação concluída!")
                messagebox.showinfo("🎉 Fim", "Simulação Concluída!")
                self.update_ui(False)
            else:
                self.status_label.config(text="▶️ Simulando...")

            # Atualiza estado do botão Step Back
            if self.simulator.can_step_back():
                self.step_back_button.config(state=tk.NORMAL)

    def step_back(self):
        """Volta um ciclo"""
        if self.simulator is not None and self.simulator.can_step_back():
            success = self.simulator.restore_previous_state()
            if success:
                self.update_tables()
                self.update_metrics()
                self.status_label.config(text="⏮️ Voltou um ciclo")

                # Atualiza estado do botão
                if not self.simulator.can_step_back():
                    self.step_back_button.config(state=tk.DISABLED)
            else:
                messagebox.showwarning("⚠️ Aviso", "Não é possível voltar mais.")

    def toggle_auto_run(self):
        """Alterna modo de auto-execução"""
        if self.auto_run_active:
            self.auto_run_active = False
            self.auto_run_button.config(text="⏯️ Auto Executar",
                                       bg=self.colors['btn_warning'])
            self.status_label.config(text="⏸️ Auto-execução pausada")
        else:
            self.auto_run_active = True
            self.auto_run_button.config(text="⏸️ Pausar",
                                       bg=self.colors['btn_danger'])
            self.status_label.config(text="▶️ Auto-executando...")
            self.auto_run_cycle()

    def auto_run_cycle(self):
        """Executa ciclos automaticamente"""
        if self.auto_run_active and self.simulator is not None:
            if not self.simulator.is_simulation_finished():
                self.next_cycle()
                self.root.after(self.auto_run_speed, self.auto_run_cycle)
            else:
                self.auto_run_active = False
                self.auto_run_button.config(text="⏯️ Auto Executar",
                                           bg=self.colors['btn_warning'])
                self.status_label.config(text="✅ Auto-execução completa!")

    def run_to_end(self):
        """Executa até o fim imediatamente"""
        if self.simulator is not None:
            self.simulator.run_to_end()
            self.update_tables()
            self.update_metrics()
            self.status_label.config(text="✅ Executado até o fim!")
            messagebox.showinfo("🎉 Fim", "Simulação Concluída!")
            self.update_ui(False)

    def get_instruction_state(self, instr):
        """Determina o estado atual da instrução"""
        if instr.is_squashed():
            return "Descartada", "squashed"
        elif instr.get_commit_cycle() != -1:
            return "Commit ✓", "commit"
        elif instr.get_write_result_cycle() != -1:
            return "Write Result", "write"
        elif instr.get_end_exec_cycle() != -1:
            return "Exec Completo", "write"
        elif instr.get_start_exec_cycle() != -1:
            return "Executando", "exec"
        elif instr.get_issue_cycle() != -1:
            return "Issue ✓", "issue"
        else:
            return "Aguardando", "waiting"

    def is_instruction_speculative(self, instr_id):
        """Verifica se a instrução é especulativa"""
        if self.simulator is None:
            return False

        # Procura por branches não resolvidos antes desta instrução
        for instr in self.simulator.get_all_instructions():
            if instr.get_id() >= instr_id:
                break
            if instr.get_op() in [Op.BEQ, Op.BNE]:
                if instr.get_issue_cycle() != -1 and not instr.is_branch_resolved():
                    return True
        return False

    def update_tables(self):
        """Atualiza todas as tabelas"""
        if self.simulator is None:
            return

        # Atualiza tabela de instruções
        for item in self.instruction_status_table.get_children():
            self.instruction_status_table.delete(item)

        for instr in self.simulator.get_all_instructions():
            state_text, state_tag = self.get_instruction_state(instr)
            is_spec = self.is_instruction_speculative(instr.get_id())

            # Se for especulativa e não descartada, usa tag especulativa
            if is_spec and not instr.is_squashed() and instr.get_commit_cycle() == -1:
                state_tag = "speculative"

            values = (
                instr.get_id(),
                instr.get_op().value,
                instr.get_dest(),
                instr.get_src1(),
                instr.get_src2(),
                instr.get_issue_cycle() if instr.get_issue_cycle() != -1 else "-",
                instr.get_start_exec_cycle() if instr.get_start_exec_cycle() != -1 else "-",
                instr.get_end_exec_cycle() if instr.get_end_exec_cycle() != -1 else "-",
                instr.get_write_result_cycle() if instr.get_write_result_cycle() != -1 else "-",
                instr.get_commit_cycle() if instr.get_commit_cycle() != -1 else "-",
                state_text,
                "SIM ⚠️" if is_spec else "NÃO"
            )
            self.instruction_status_table.insert("", tk.END, values=values, tags=(state_tag,))

        # Atualiza tabela de RSs
        for item in self.rs_status_table.get_children():
            self.rs_status_table.delete(item)

        for rs_array in [self.simulator.get_rs_add(), self.simulator.get_rs_store(),
                         self.simulator.get_rs_mult(), self.simulator.get_rs_branch()]:
            for rs in rs_array:
                if rs.is_busy():
                    instr = rs.get_instruction()
                    ciclos_restantes = instr.get_current_latency() if instr else "-"

                    # Determina estado da RS
                    if rs.is_ready_to_execute() and instr.get_start_exec_cycle() != -1:
                        estado = "Executando ▶️"
                        tag = "executing"
                    elif rs.is_ready_to_execute():
                        estado = "Pronta ✓"
                        tag = "ready"
                    else:
                        estado = "Esperando ⏳"
                        tag = "busy"
                else:
                    estado = "Livre ✓"
                    tag = "free"
                    ciclos_restantes = "-"

                values = (
                    rs.get_name(),
                    estado,
                    rs.get_op().value if rs.get_op() is not None else "-",
                    f"{rs.get_Vj():.2f}" if rs.get_Vj() is not None else "-",
                    f"{rs.get_Vk():.2f}" if rs.get_Vk() is not None else "-",
                    rs.get_Qj() if rs.get_Qj() is not None else "-",
                    rs.get_Qk() if rs.get_Qk() is not None else "-",
                    ciclos_restantes
                )
                self.rs_status_table.insert("", tk.END, values=values, tags=(tag,))

        # Atualiza tabela de registradores
        for item in self.register_file_table.get_children():
            self.register_file_table.delete(item)

        for reg_name, status in self.simulator.get_register_file().get_registers().items():
            producer = status.get_producer_tag()
            if producer is not None:
                status_text = "Esperando ⏳"
                tag = "waiting"
            else:
                status_text = "Pronto ✓"
                tag = "ready"

            value = status.get_value()
            values = (
                reg_name,
                f"{value:.2f}" if value is not None else "0.00",
                producer if producer is not None else "-",
                status_text
            )
            self.register_file_table.insert("", tk.END, values=values, tags=(tag,))

        # Atualiza clock
        self.clock_label.config(text=f"🕐 Clock: {self.simulator.get_current_clock()}")

    def update_metrics(self):
        """Atualiza métricas"""
        if self.simulator is None:
            return

        ipc = self.simulator.calculate_ipc()
        bubble_cycles = self.simulator.get_bubble_cycles()
        total_cycles = self.simulator.get_current_clock()

        # Usa os novos métodos do simulador que não resetam
        speculative = self.simulator.get_current_speculative_count()
        squashed = self.simulator.get_total_squashed()

        self.metrics_label.config(
            text=f"📊 IPC: {ipc:.3f} | Ciclos: {total_cycles} | Bolhas: {bubble_cycles} | "
                 f"Especulativas: {speculative} | Descartadas: {squashed}"
        )

    def parse_instructions_from_text(self, text):
        """Parse instruções do texto"""
        lines = text.strip().split('\n')
        instructions = []

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '#' in line:
                line = line.split('#')[0].strip()

            tokens = line.split()
            if len(tokens) < 4:
                messagebox.showerror("❌ Erro de Parse",
                    f"Linha {line_num + 1}: '{line}'\nFormato inválido. Use: OP DEST SRC1 SRC2")
                return None

            op_str = tokens[0].upper()
            dest = tokens[1].upper()
            src1 = tokens[2].upper()
            src2 = tokens[3].upper()

            try:
                op = Op[op_str]
            except KeyError:
                messagebox.showerror("❌ Erro de Parse",
                    f"Linha {line_num + 1}: Operação '{op_str}' inválida.\n"
                    f"Operações válidas: ADD, SUB, MUL, DIV, LD, ST, BEQ, BNE")
                return None

            # Determina latência
            latency = 0
            if op in [Op.ADD, Op.SUB]:
                latency = int(self.lat_add.get())
            elif op == Op.LD:
                latency = int(self.lat_load.get())
            elif op == Op.ST:
                latency = int(self.lat_store.get())
            elif op == Op.MUL:
                latency = int(self.lat_mult.get())
            elif op == Op.DIV:
                latency = int(self.lat_div.get())
            elif op in [Op.BEQ, Op.BNE]:
                latency = int(self.lat_branch.get())

            instr_id = len(instructions)

            if op in [Op.BEQ, Op.BNE]:
                try:
                    target_id = int(dest)
                    instr = Instruction(instr_id, op, "0", src1, src2, latency)
                    instr.set_branch_target_id(target_id)
                except ValueError:
                    messagebox.showerror("❌ Erro de Parse",
                        f"Linha {line_num + 1}: ID do alvo do branch deve ser um número.")
                    return None
            else:
                instr = Instruction(instr_id, op, dest, src1, src2, latency)

            instructions.append(instr)

        return instructions

    def load_from_paste(self):
        """Carrega instruções da área de texto"""
        if self.simulator is None:
            messagebox.showerror("❌ Erro", "Configure o simulador primeiro!")
            return

        text = self.paste_text_area.get("1.0", tk.END)
        instructions = self.parse_instructions_from_text(text)

        if instructions is None:
            return

        if len(instructions) == 0:
            messagebox.showwarning("⚠️ Aviso", "Nenhuma instrução válida encontrada.")
            return

        self.simulator.set_instructions(instructions)
        self.update_tables()
        self.update_ui(True)
        self.status_label.config(text=f"✅ {len(instructions)} instrução(ões) carregada(s)")

        messagebox.showinfo("✅ Sucesso",
            f"{len(instructions)} instrução(ões) carregada(s)!\nUse os controles para executar.")

    def clear_paste(self):
        """Limpa a área de texto"""
        self.paste_text_area.delete("1.0", tk.END)
        example_text = "# Exemplo:\nADD R1 R2 R3\nMUL R4 R1 R5\nSUB R6 R4 R2\n"
        self.paste_text_area.insert("1.0", example_text)

    def update_ui(self, simulation_ready):
        """Atualiza estado da UI"""
        if simulation_ready:
            self.next_cycle_button.config(state=tk.NORMAL)
            self.run_to_end_button.config(state=tk.NORMAL)
            self.auto_run_button.config(state=tk.NORMAL)
        else:
            self.next_cycle_button.config(state=tk.DISABLED)
            self.run_to_end_button.config(state=tk.DISABLED)
            self.auto_run_button.config(state=tk.DISABLED)
            self.step_back_button.config(state=tk.DISABLED)

        state = tk.NORMAL if not simulation_ready else tk.DISABLED
        self.fu_add.config(state=state)
        self.fu_store.config(state=state)
        self.fu_mult.config(state=state)
        self.fu_branch.config(state=state)
        self.lat_add.config(state=state)
        self.lat_load.config(state=state)
        self.lat_store.config(state=state)
        self.lat_mult.config(state=state)
        self.lat_div.config(state=state)
        self.lat_branch.config(state=state)
        self.setup_simulator_button.config(state=state)
        self.load_from_paste_button.config(state=state)
        self.clear_paste_button.config(state=state)


if __name__ == "__main__":
    root = tk.Tk()
    app = TOMASSULLLERoriGUI(root)
    root.mainloop()
