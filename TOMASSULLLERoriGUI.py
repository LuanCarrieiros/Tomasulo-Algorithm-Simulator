import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from Instruction import Instruction, Op
from TOMASSULLLERoriSimulator import TOMASSULLLERoriSimulator


class TOMASSULLLERoriGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador do Algoritmo de Tomasulo")
        self.root.geometry("1400x900")

        self.simulator = None

        self.init_components()
        self.add_listeners()
        self.update_ui(False)

    def init_components(self):
        # Main frame dividido em left e right
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Painel Esquerdo ---
        left_panel = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # Título do painel esquerdo
        tk.Label(left_panel, text="Configurações e Entrada", font=("Arial", 12, "bold")).pack(pady=5)

        # Input para quantidade de Unidades Funcionais
        fu_frame = tk.LabelFrame(left_panel, text="Unidades Funcionais (Qtd)", padx=10, pady=10)
        fu_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(fu_frame, text="ADD/SUB:").grid(row=0, column=0, sticky=tk.W)
        self.fu_add = tk.Entry(fu_frame, width=10)
        self.fu_add.insert(0, "1")
        self.fu_add.grid(row=0, column=1)

        tk.Label(fu_frame, text="LOAD/STORE:").grid(row=1, column=0, sticky=tk.W)
        self.fu_store = tk.Entry(fu_frame, width=10)
        self.fu_store.insert(0, "1")
        self.fu_store.grid(row=1, column=1)

        tk.Label(fu_frame, text="MUL/DIV:").grid(row=2, column=0, sticky=tk.W)
        self.fu_mult = tk.Entry(fu_frame, width=10)
        self.fu_mult.insert(0, "1")
        self.fu_mult.grid(row=2, column=1)

        tk.Label(fu_frame, text="BRANCH:").grid(row=3, column=0, sticky=tk.W)
        self.fu_branch = tk.Entry(fu_frame, width=10)
        self.fu_branch.insert(0, "1")
        self.fu_branch.grid(row=3, column=1)

        # Input para Latências
        lat_frame = tk.LabelFrame(left_panel, text="Latências (Ciclos)", padx=10, pady=10)
        lat_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(lat_frame, text="ADD/SUB:").grid(row=0, column=0, sticky=tk.W)
        self.lat_add = tk.Entry(lat_frame, width=10)
        self.lat_add.insert(0, "2")
        self.lat_add.grid(row=0, column=1)

        tk.Label(lat_frame, text="LOAD:").grid(row=1, column=0, sticky=tk.W)
        self.lat_load = tk.Entry(lat_frame, width=10)
        self.lat_load.insert(0, "6")
        self.lat_load.grid(row=1, column=1)

        tk.Label(lat_frame, text="STORE:").grid(row=2, column=0, sticky=tk.W)
        self.lat_store = tk.Entry(lat_frame, width=10)
        self.lat_store.insert(0, "6")
        self.lat_store.grid(row=2, column=1)

        tk.Label(lat_frame, text="MUL:").grid(row=3, column=0, sticky=tk.W)
        self.lat_mult = tk.Entry(lat_frame, width=10)
        self.lat_mult.insert(0, "3")
        self.lat_mult.grid(row=3, column=1)

        tk.Label(lat_frame, text="DIV:").grid(row=4, column=0, sticky=tk.W)
        self.lat_div = tk.Entry(lat_frame, width=10)
        self.lat_div.insert(0, "3")
        self.lat_div.grid(row=4, column=1)

        tk.Label(lat_frame, text="BRANCH:").grid(row=5, column=0, sticky=tk.W)
        self.lat_branch = tk.Entry(lat_frame, width=10)
        self.lat_branch.insert(0, "4")
        self.lat_branch.grid(row=5, column=1)

        self.setup_simulator_button = tk.Button(left_panel, text="Configurar Simulador",
                                                bg="lightblue", font=("Arial", 10, "bold"))
        self.setup_simulator_button.pack(pady=5)

        # --- Área de Copy/Paste ---
        paste_frame = tk.LabelFrame(left_panel, text="Carregar Instruções", padx=5, pady=5)
        paste_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(paste_frame, text="Cole as instruções (uma por linha):", font=("Arial", 9)).pack(anchor=tk.W)
        tk.Label(paste_frame, text="Formato: OP DEST SRC1 SRC2", font=("Arial", 8), fg="gray").pack(anchor=tk.W)
        tk.Label(paste_frame, text="Exemplo: ADD R1 R2 R3", font=("Arial", 8), fg="gray").pack(anchor=tk.W)

        self.paste_text_area = scrolledtext.ScrolledText(paste_frame, width=25, height=10, font=("Courier", 9))
        self.paste_text_area.pack(fill=tk.BOTH, expand=True, pady=5)

        # Texto de exemplo inicial
        example_text = "# Exemplo:\n# ADD R1 R2 R3\n# MUL R4 R1 R5\n# SUB R6 R4 R2\n"
        self.paste_text_area.insert("1.0", example_text)

        paste_buttons_frame = tk.Frame(paste_frame)
        paste_buttons_frame.pack(fill=tk.X, pady=5)

        self.load_from_paste_button = tk.Button(paste_buttons_frame, text="Iniciar",
                                                bg="lightgreen", font=("Arial", 9, "bold"))
        self.load_from_paste_button.pack(side=tk.LEFT, padx=2)

        self.clear_paste_button = tk.Button(paste_buttons_frame, text="Limpar",
                                           bg="lightyellow", font=("Arial", 9))
        self.clear_paste_button.pack(side=tk.LEFT, padx=2)

        # --- Painel Direito ---
        right_panel = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controles do Clock
        clock_control_panel = tk.Frame(right_panel)
        clock_control_panel.pack(fill=tk.X, padx=5, pady=5)

        self.clock_label = tk.Label(clock_control_panel, text="Clock: 0", font=("Arial", 14, "bold"))
        self.clock_label.pack(side=tk.LEFT, padx=10)

        self.next_cycle_button = tk.Button(clock_control_panel, text="Próximo Ciclo",
                                          bg="lightgreen", font=("Arial", 10, "bold"))
        self.next_cycle_button.pack(side=tk.LEFT, padx=5)

        self.run_to_end_button = tk.Button(clock_control_panel, text="Executar Tudo",
                                          bg="orange", font=("Arial", 10, "bold"))
        self.run_to_end_button.pack(side=tk.LEFT, padx=5)

        # Tabela de Status das Instruções
        instr_status_frame = tk.LabelFrame(right_panel, text="Status das Instruções", padx=5, pady=5)
        instr_status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("ID", "Op", "Dest", "Src1", "Src2", "Issue", "Exec Start", "Exec End", "Write Result", "Commit", "Squashed")
        self.instruction_status_table = ttk.Treeview(instr_status_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.instruction_status_table.heading(col, text=col)
            self.instruction_status_table.column(col, width=70, anchor=tk.CENTER)

        instr_scrollbar = tk.Scrollbar(instr_status_frame, orient=tk.VERTICAL, command=self.instruction_status_table.yview)
        self.instruction_status_table.configure(yscrollcommand=instr_scrollbar.set)
        self.instruction_status_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        instr_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tabela de Estações de Reserva
        rs_status_frame = tk.LabelFrame(right_panel, text="Estações de Reserva", padx=5, pady=5)
        rs_status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        rs_columns = ("Nome", "Busy", "Op", "Vj", "Vk", "Qj", "Qk")
        self.rs_status_table = ttk.Treeview(rs_status_frame, columns=rs_columns, show="headings", height=4)
        for col in rs_columns:
            self.rs_status_table.heading(col, text=col)
            self.rs_status_table.column(col, width=90, anchor=tk.CENTER)

        rs_scrollbar = tk.Scrollbar(rs_status_frame, orient=tk.VERTICAL, command=self.rs_status_table.yview)
        self.rs_status_table.configure(yscrollcommand=rs_scrollbar.set)
        self.rs_status_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tabela de Register File
        reg_file_frame = tk.LabelFrame(right_panel, text="Register File", padx=5, pady=5)
        reg_file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        reg_columns = ("Registrador", "Valor", "Produtor")
        self.register_file_table = ttk.Treeview(reg_file_frame, columns=reg_columns, show="headings", height=4)
        for col in reg_columns:
            self.register_file_table.heading(col, text=col)
            self.register_file_table.column(col, width=120, anchor=tk.CENTER)

        reg_scrollbar = tk.Scrollbar(reg_file_frame, orient=tk.VERTICAL, command=self.register_file_table.yview)
        self.register_file_table.configure(yscrollcommand=reg_scrollbar.set)
        self.register_file_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Métricas
        self.metrics_label = tk.Label(right_panel, text="Métricas: IPC: N/A | Ciclos Gastos: 0 | Ciclos Bolha: 0",
                                     font=("Arial", 12, "bold"))
        self.metrics_label.pack(pady=5)

    def add_listeners(self):
        self.setup_simulator_button.config(command=self.setup_simulator)
        self.next_cycle_button.config(command=self.next_cycle)
        self.run_to_end_button.config(command=self.run_to_end)
        self.load_from_paste_button.config(command=self.load_from_paste)
        self.clear_paste_button.config(command=self.clear_paste)

    def setup_simulator(self):
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

            self.simulator = TOMASSULLLERoriSimulator(add, store, mult, branch,
                                                     lat_add, lat_load, lat_store, lat_mult, lat_div, lat_branch)
            messagebox.showinfo("Sucesso", "Simulador configurado com sucesso! Agora defina as instruções.")
            self.update_ui(False)
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Por favor, insira números válidos para quantidades e latências.")

    def next_cycle(self):
        if self.simulator is not None:
            self.simulator.next_cycle()
            self.update_tables()
            self.update_metrics()
            if self.simulator.is_simulation_finished():
                messagebox.showinfo("Fim", "Simulação Concluída!")
                self.update_ui(False)

    def run_to_end(self):
        if self.simulator is not None:
            self.simulator.run_to_end()
            self.update_tables()
            self.update_metrics()
            messagebox.showinfo("Fim", "Simulação Concluída!")
            self.update_ui(False)

    def update_tables(self):
        # Atualiza a tabela de Status das Instruções
        for item in self.instruction_status_table.get_children():
            self.instruction_status_table.delete(item)

        for instr in self.simulator.get_all_instructions():
            values = (
                instr.get_id(),
                instr.get_op().value,
                instr.get_dest(),
                instr.get_src1(),
                instr.get_src2(),
                instr.get_issue_cycle() if instr.get_issue_cycle() != -1 else "N/A",
                instr.get_start_exec_cycle() if instr.get_start_exec_cycle() != -1 else "N/A",
                instr.get_end_exec_cycle() if instr.get_end_exec_cycle() != -1 else "N/A",
                instr.get_write_result_cycle() if instr.get_write_result_cycle() != -1 else "N/A",
                instr.get_commit_cycle() if instr.get_commit_cycle() != -1 else "N/A",
                "SIM" if instr.is_squashed() else "NÃO"
            )
            self.instruction_status_table.insert("", tk.END, values=values)

        # Atualiza a tabela de Estações de Reserva
        for item in self.rs_status_table.get_children():
            self.rs_status_table.delete(item)

        self.add_rs_to_table(self.simulator.get_rs_add())
        self.add_rs_to_table(self.simulator.get_rs_store())
        self.add_rs_to_table(self.simulator.get_rs_mult())
        self.add_rs_to_table(self.simulator.get_rs_branch())

        # Atualiza a tabela de Register File
        for item in self.register_file_table.get_children():
            self.register_file_table.delete(item)

        for reg_name, status in self.simulator.get_register_file().get_registers().items():
            producer_info = status.get_producer_tag() if status.get_producer_tag() is not None else "N/A"
            values = (reg_name, status.get_value(), producer_info)
            self.register_file_table.insert("", tk.END, values=values)

        # Atualiza o clock
        self.clock_label.config(text=f"Clock: {self.simulator.get_current_clock()}")

    def add_rs_to_table(self, rs_array):
        for rs in rs_array:
            values = (
                rs.get_name(),
                "SIM" if rs.is_busy() else "NÃO",
                rs.get_op().value if rs.get_op() is not None else "N/A",
                f"{rs.get_Vj():.2f}" if rs.get_Vj() is not None else "N/A",
                f"{rs.get_Vk():.2f}" if rs.get_Vk() is not None else "N/A",
                rs.get_Qj() if rs.get_Qj() is not None else "N/A",
                rs.get_Qk() if rs.get_Qk() is not None else "N/A"
            )
            self.rs_status_table.insert("", tk.END, values=values)

    def update_metrics(self):
        ipc = self.simulator.calculate_ipc()
        bubble_cycles = self.simulator.get_bubble_cycles()
        total_cycles = self.simulator.get_current_clock()
        self.metrics_label.config(text=f"Métricas: IPC: {ipc:.2f} | Ciclos Gastos: {total_cycles} | Ciclos Bolha: {bubble_cycles}")

    def parse_instructions_from_text(self, text):
        """
        Parse instruções do texto colado.
        Formato esperado: OP DEST SRC1 SRC2
        Exemplo: ADD R1 R2 R3
        Linhas começando com # são ignoradas (comentários)
        """
        lines = text.strip().split('\n')
        instructions = []

        for line_num, line in enumerate(lines):
            line = line.strip()

            # Ignora linhas vazias e comentários
            if not line or line.startswith('#'):
                continue

            # Remove comentários inline
            if '#' in line:
                line = line.split('#')[0].strip()

            # Divide a linha em tokens
            tokens = line.split()

            if len(tokens) < 4:
                messagebox.showerror("Erro de Parse",
                    f"Linha {line_num + 1}: '{line}'\nFormato inválido. Use: OP DEST SRC1 SRC2")
                return None

            op_str = tokens[0].upper()
            dest = tokens[1].upper()
            src1 = tokens[2].upper()
            src2 = tokens[3].upper()

            # Valida a operação
            try:
                op = Op[op_str]
            except KeyError:
                messagebox.showerror("Erro de Parse",
                    f"Linha {line_num + 1}: Operação '{op_str}' inválida.\n"
                    f"Operações válidas: ADD, SUB, MUL, DIV, LD, ST, BEQ, BNE")
                return None

            # Determina latência baseada na operação
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

            # Cria a instrução
            instr_id = len(instructions)

            if op in [Op.BEQ, Op.BNE]:
                # Para branches, dest é o TARGET_ID
                try:
                    target_id = int(dest)
                    instr = Instruction(instr_id, op, "0", src1, src2, latency)
                    instr.set_branch_target_id(target_id)
                except ValueError:
                    messagebox.showerror("Erro de Parse",
                        f"Linha {line_num + 1}: ID do alvo do branch deve ser um número inteiro.")
                    return None
            else:
                instr = Instruction(instr_id, op, dest, src1, src2, latency)

            instructions.append(instr)

        return instructions

    def load_from_paste(self):
        """Carrega instruções da área de texto"""
        if self.simulator is None:
            messagebox.showerror("Erro", "Por favor, configure o simulador primeiro.")
            return

        text = self.paste_text_area.get("1.0", tk.END)
        instructions = self.parse_instructions_from_text(text)

        if instructions is None:
            return  # Erro no parse

        if len(instructions) == 0:
            messagebox.showwarning("Aviso", "Nenhuma instrução válida encontrada no texto.")
            return

        # Carrega as instruções no simulador
        self.simulator.set_instructions(instructions)
        self.update_tables()
        self.update_ui(True)

        messagebox.showinfo("Sucesso",
            f"{len(instructions)} instrução(ões) carregada(s) com sucesso!")

    def clear_paste(self):
        """Limpa a área de texto"""
        self.paste_text_area.delete("1.0", tk.END)
        example_text = "# Exemplo:\n# ADD R1 R2 R3\n# MUL R4 R1 R5\n# SUB R6 R4 R2\n"
        self.paste_text_area.insert("1.0", example_text)

    def update_ui(self, simulation_ready):
        state = tk.NORMAL if not simulation_ready else tk.DISABLED

        self.next_cycle_button.config(state=tk.NORMAL if simulation_ready else tk.DISABLED)
        self.run_to_end_button.config(state=tk.NORMAL if simulation_ready else tk.DISABLED)

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
