"""
Simulador do Algoritmo de Tomasulo
Desenvolvido para fins didáticos
Suporta: ROB, Especulação de Desvios, Execução Passo a Passo
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict

# ===========================
# ENUMS E DATACLASSES
# ===========================

class InstructionType(Enum):
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    LOAD = "LOAD"
    STORE = "STORE"
    BEQ = "BEQ"
    BNE = "BNE"

class RSType(Enum):
    ADD_SUB = "Add/Sub"
    MUL_DIV = "Mul/Div"
    LOAD = "Load"
    STORE = "Store"

@dataclass
class Instruction:
    """Representa uma instrução MIPS"""
    line_num: int
    original: str
    type: InstructionType
    dest: Optional[str] = None
    src1: Optional[str] = None
    src2: Optional[str] = None
    immediate: Optional[int] = None
    offset: Optional[int] = None

    # Estágios de execução
    issue_cycle: Optional[int] = None
    execute_start_cycle: Optional[int] = None
    execute_end_cycle: Optional[int] = None
    write_result_cycle: Optional[int] = None
    commit_cycle: Optional[int] = None

    # ROB entry
    rob_entry: Optional[int] = None

@dataclass
class ReservationStation:
    """Estação de Reserva"""
    name: str
    type: RSType
    busy: bool = False
    op: Optional[InstructionType] = None
    vj: Optional[float] = None  # Valor do operando J
    vk: Optional[float] = None  # Valor do operando K
    qj: Optional[str] = None    # ROB entry produzindo J
    qk: Optional[str] = None    # ROB entry produzindo K
    dest: Optional[str] = None  # Registrador destino
    address: Optional[int] = None  # Para LOAD/STORE
    rob_entry: Optional[int] = None
    cycles_remaining: int = 0
    instruction: Optional[Instruction] = None

@dataclass
class ROBEntry:
    """Entrada do Reorder Buffer"""
    entry_num: int
    busy: bool = False
    instruction_type: Optional[InstructionType] = None
    destination: Optional[str] = None
    value: Optional[float] = None
    ready: bool = False
    instruction: Optional[Instruction] = None
    speculative: bool = False  # Se é especulativo

class RegisterFile:
    """Arquivo de Registradores com RAT (Register Alias Table)"""
    def __init__(self, num_regs=32):
        self.values = {f"R{i}": 0.0 for i in range(num_regs)}
        self.values.update({f"F{i}": 0.0 for i in range(num_regs)})  # FP registers
        self.qi = {reg: None for reg in self.values.keys()}  # ROB entry produzindo o valor

    def reset(self):
        for reg in self.values:
            self.values[reg] = 0.0
            self.qi[reg] = None

# ===========================
# PARSER DE INSTRUÇÕES MIPS
# ===========================

class MIPSParser:
    """Parser de instruções MIPS simplificadas"""

    @staticmethod
    def parse_instruction(line: str, line_num: int) -> Optional[Instruction]:
        """Parse uma linha de instrução MIPS"""
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        # Remove comentários
        if '#' in line:
            line = line[:line.index('#')].strip()

        parts = re.split(r'[,\s()]+', line)
        parts = [p for p in parts if p]

        if not parts:
            return None

        op = parts[0].upper()

        try:
            # Instruções aritméticas: ADD R1, R2, R3
            if op in ['ADD', 'ADDI', 'SUB', 'SUBI']:
                inst_type = InstructionType.ADD if 'ADD' in op else InstructionType.SUB
                if 'I' in op:  # Imediato
                    return Instruction(line_num, line, inst_type,
                                     dest=parts[1], src1=parts[2], immediate=int(parts[3]))
                else:
                    return Instruction(line_num, line, inst_type,
                                     dest=parts[1], src1=parts[2], src2=parts[3])

            # Multiplicação/Divisão
            elif op in ['MUL', 'DIV']:
                inst_type = InstructionType.MUL if op == 'MUL' else InstructionType.DIV
                return Instruction(line_num, line, inst_type,
                                 dest=parts[1], src1=parts[2], src2=parts[3])

            # LOAD: L.D F1, 0(R2) ou LOAD F1, 0(R2)
            elif op in ['L.D', 'LOAD', 'LW']:
                offset = int(parts[2]) if len(parts) > 3 else 0
                base = parts[3] if len(parts) > 3 else parts[2]
                return Instruction(line_num, line, InstructionType.LOAD,
                                 dest=parts[1], src1=base, offset=offset)

            # STORE: S.D F1, 0(R2) ou STORE F1, 0(R2)
            elif op in ['S.D', 'STORE', 'SW']:
                offset = int(parts[2]) if len(parts) > 3 else 0
                base = parts[3] if len(parts) > 3 else parts[2]
                return Instruction(line_num, line, InstructionType.STORE,
                                 src1=parts[1], src2=base, offset=offset)

            # Desvios: BEQ R1, R2, label
            elif op in ['BEQ', 'BNE']:
                inst_type = InstructionType.BEQ if op == 'BEQ' else InstructionType.BNE
                offset = int(parts[3]) if parts[3].lstrip('-').isdigit() else 0
                return Instruction(line_num, line, inst_type,
                                 src1=parts[1], src2=parts[2], offset=offset)

        except (IndexError, ValueError) as e:
            print(f"Erro ao fazer parse da linha {line_num}: {line} - {e}")
            return None

        return None

# ===========================
# SIMULADOR TOMASULO
# ===========================

class TomasulSimulator:
    """Simulador do Algoritmo de Tomasulo com ROB e Especulação"""

    def __init__(self):
        # Configurações
        self.num_add_rs = 3
        self.num_mul_rs = 2
        self.num_load_buffers = 2
        self.num_store_buffers = 2
        self.rob_size = 16

        # Latências (em ciclos)
        self.latencies = {
            InstructionType.ADD: 2,
            InstructionType.SUB: 2,
            InstructionType.MUL: 10,
            InstructionType.DIV: 40,
            InstructionType.LOAD: 3,
            InstructionType.STORE: 3,
            InstructionType.BEQ: 1,
            InstructionType.BNE: 1,
        }

        self.reset()

    def reset(self):
        """Reseta o simulador"""
        self.cycle = 0
        self.instructions: List[Instruction] = []
        self.pc = 0

        # Reservation Stations
        self.add_rs = [ReservationStation(f"Add{i}", RSType.ADD_SUB)
                       for i in range(self.num_add_rs)]
        self.mul_rs = [ReservationStation(f"Mul{i}", RSType.MUL_DIV)
                       for i in range(self.num_mul_rs)]
        self.load_buffers = [ReservationStation(f"Load{i}", RSType.LOAD)
                            for i in range(self.num_load_buffers)]
        self.store_buffers = [ReservationStation(f"Store{i}", RSType.STORE)
                             for i in range(self.num_store_buffers)]

        # ROB
        self.rob: List[ROBEntry] = [ROBEntry(i) for i in range(self.rob_size)]
        self.rob_head = 0
        self.rob_tail = 0

        # Registradores
        self.registers = RegisterFile()
        # Inicializa alguns registradores com valores de exemplo para facilitar testes
        self.registers.values["F1"] = 2.0
        self.registers.values["F2"] = 3.0
        self.registers.values["F3"] = 4.0
        self.registers.values["F4"] = 5.0
        self.registers.values["F5"] = 6.0
        self.registers.values["F6"] = 7.0
        self.registers.values["F7"] = 8.0
        self.registers.values["F8"] = 9.0
        self.registers.values["R1"] = 100.0  # Base para LOADs
        self.registers.values["R2"] = 200.0  # Base para LOADs

        # Memória (simplificada)
        self.memory = {i: 0.0 for i in range(1000)}
        # Inicializa alguns valores na memória
        for i in range(20):
            self.memory[100 + i*4] = float(i + 1)  # Mem[100-176] = 1,2,3...
            self.memory[200 + i*4] = float((i + 1) * 10)  # Mem[200-276] = 10,20,30...

        # Métricas
        self.total_cycles = 0
        self.instructions_committed = 0
        self.bubble_cycles = 0
        self.branch_mispredictions = 0

        # Especulação
        self.speculating = False
        self.speculation_rob_entry = None

    def load_program(self, program_text: str):
        """Carrega um programa MIPS"""
        self.reset()
        lines = program_text.strip().split('\n')

        for i, line in enumerate(lines):
            inst = MIPSParser.parse_instruction(line, i)
            if inst:
                self.instructions.append(inst)

    def get_rs_for_instruction(self, inst: Instruction) -> Optional[ReservationStation]:
        """Retorna uma RS livre para a instrução"""
        if inst.type in [InstructionType.ADD, InstructionType.SUB]:
            for rs in self.add_rs:
                if not rs.busy:
                    return rs
        elif inst.type in [InstructionType.MUL, InstructionType.DIV]:
            for rs in self.mul_rs:
                if not rs.busy:
                    return rs
        elif inst.type == InstructionType.LOAD:
            for rs in self.load_buffers:
                if not rs.busy:
                    return rs
        elif inst.type == InstructionType.STORE:
            for rs in self.store_buffers:
                if not rs.busy:
                    return rs
        return None

    def get_free_rob_entry(self) -> Optional[ROBEntry]:
        """Retorna uma entrada livre do ROB"""
        if not self.rob[self.rob_tail].busy:
            return self.rob[self.rob_tail]
        return None

    def issue_instruction(self) -> bool:
        """Tenta despachar a próxima instrução (Issue)"""
        if self.pc >= len(self.instructions):
            return False

        inst = self.instructions[self.pc]

        # Verifica se há RS livre
        rs = self.get_rs_for_instruction(inst)
        if not rs:
            return False

        # Verifica se há entrada livre no ROB
        rob_entry = self.get_free_rob_entry()
        if not rob_entry:
            return False

        # Issue da instrução
        inst.issue_cycle = self.cycle
        inst.rob_entry = self.rob_tail

        # Atualiza ROB
        rob_entry.busy = True
        rob_entry.instruction_type = inst.type
        rob_entry.instruction = inst
        rob_entry.ready = False
        rob_entry.speculative = self.speculating

        if inst.type in [InstructionType.ADD, InstructionType.SUB,
                         InstructionType.MUL, InstructionType.DIV]:
            rob_entry.destination = inst.dest
        elif inst.type == InstructionType.LOAD:
            rob_entry.destination = inst.dest

        # Atualiza RS
        rs.busy = True
        rs.op = inst.type
        rs.rob_entry = self.rob_tail
        rs.instruction = inst
        rs.cycles_remaining = self.latencies[inst.type]

        # Lê operandos
        if inst.src1:
            if self.registers.qi[inst.src1] is not None:
                rs.qj = f"ROB{self.registers.qi[inst.src1]}"
                rs.vj = None
            else:
                rs.vj = self.registers.values[inst.src1]
                rs.qj = None

        if inst.src2:
            if self.registers.qi[inst.src2] is not None:
                rs.qk = f"ROB{self.registers.qi[inst.src2]}"
                rs.vk = None
            else:
                rs.vk = self.registers.values[inst.src2]
                rs.qk = None
        elif inst.immediate is not None:
            rs.vk = float(inst.immediate)
            rs.qk = None

        # Para LOAD/STORE
        if inst.type in [InstructionType.LOAD, InstructionType.STORE]:
            if inst.offset is not None:
                rs.address = inst.offset

        # Atualiza RAT (Register Alias Table)
        if inst.dest and inst.type != InstructionType.STORE:
            self.registers.qi[inst.dest] = self.rob_tail

        # Especulação de desvio
        if inst.type in [InstructionType.BEQ, InstructionType.BNE]:
            self.speculating = True
            self.speculation_rob_entry = self.rob_tail

        # Avança ROB tail
        self.rob_tail = (self.rob_tail + 1) % self.rob_size
        self.pc += 1

        return True

    def execute(self):
        """Executa instruções nas RSs"""
        all_rs = self.add_rs + self.mul_rs + self.load_buffers + self.store_buffers

        for rs in all_rs:
            if not rs.busy:
                continue

            # Verifica se operandos estão prontos
            if rs.qj is not None or rs.qk is not None:
                continue

            # Inicia execução
            inst = rs.instruction
            if inst.execute_start_cycle is None:
                inst.execute_start_cycle = self.cycle

            # Decrementa ciclos
            rs.cycles_remaining -= 1

            # Se terminou execução
            if rs.cycles_remaining == 0:
                inst.execute_end_cycle = self.cycle

                # Calcula resultado
                result = 0.0
                if rs.op == InstructionType.ADD:
                    result = rs.vj + rs.vk
                elif rs.op == InstructionType.SUB:
                    result = rs.vj - rs.vk
                elif rs.op == InstructionType.MUL:
                    result = rs.vj * rs.vk
                elif rs.op == InstructionType.DIV:
                    result = rs.vj / rs.vk if rs.vk != 0 else 0
                elif rs.op == InstructionType.LOAD:
                    addr = int(rs.vj) + (rs.address if rs.address else 0)
                    result = self.memory.get(addr, 0.0)
                elif rs.op == InstructionType.STORE:
                    # STORE não produz resultado para registrador
                    addr = int(rs.vk) + (rs.address if rs.address else 0)
                    result = rs.vj  # Valor a ser armazenado

                # Write Result
                self.write_result(rs, result)

    def write_result(self, rs: ReservationStation, result: float):
        """Escreve resultado no ROB e faz broadcast"""
        inst = rs.instruction
        inst.write_result_cycle = self.cycle

        # Atualiza ROB
        rob_entry = self.rob[rs.rob_entry]
        rob_entry.value = result
        rob_entry.ready = True

        # Broadcast para RSs esperando
        all_rs = self.add_rs + self.mul_rs + self.load_buffers + self.store_buffers
        rob_tag = f"ROB{rs.rob_entry}"

        for other_rs in all_rs:
            if other_rs.qj == rob_tag:
                other_rs.vj = result
                other_rs.qj = None
            if other_rs.qk == rob_tag:
                other_rs.vk = result
                other_rs.qk = None

        # Libera RS
        rs.busy = False
        rs.op = None
        rs.vj = None
        rs.vk = None
        rs.qj = None
        rs.qk = None
        rs.rob_entry = None
        rs.instruction = None

    def commit(self):
        """Commit de instruções do ROB"""
        rob_entry = self.rob[self.rob_head]

        if not rob_entry.busy or not rob_entry.ready:
            return

        inst = rob_entry.instruction
        inst.commit_cycle = self.cycle

        # Atualiza registrador ou memória
        if rob_entry.destination:
            # Atualiza apenas se ainda aponta para este ROB
            if self.registers.qi[rob_entry.destination] == self.rob_head:
                self.registers.values[rob_entry.destination] = rob_entry.value
                self.registers.qi[rob_entry.destination] = None

        # STORE
        if rob_entry.instruction_type == InstructionType.STORE:
            # Calcula endereço e escreve na memória
            # (endereço já foi calculado no execute)
            pass

        # Desvio
        if rob_entry.instruction_type in [InstructionType.BEQ, InstructionType.BNE]:
            # Resolve especulação
            if self.speculation_rob_entry == self.rob_head:
                self.speculating = False
                self.speculation_rob_entry = None

        # Libera entrada do ROB
        rob_entry.busy = False
        rob_entry.ready = False
        rob_entry.instruction = None

        # Avança head
        self.rob_head = (self.rob_head + 1) % self.rob_size
        self.instructions_committed += 1

    def step(self):
        """Executa um ciclo de clock"""
        self.cycle += 1

        # 1. Commit (mais velho primeiro)
        self.commit()

        # 2. Write Result / Execute
        self.execute()

        # 3. Issue (despachar nova instrução)
        issued = self.issue_instruction()

        # Detecta ciclos de bolha
        if not issued and self.pc < len(self.instructions):
            self.bubble_cycles += 1

    def run_to_completion(self, max_cycles=10000):
        """Executa até completar todas instruções"""
        safety_counter = 0
        while not self.is_complete() and safety_counter < max_cycles:
            self.step()
            safety_counter += 1

        self.total_cycles = self.cycle

        if safety_counter >= max_cycles:
            print(f"AVISO: Limite de {max_cycles} ciclos atingido. Possível loop infinito.")

    def is_complete(self) -> bool:
        """Verifica se a simulação está completa"""
        # Todas instruções foram despachadas
        all_issued = self.pc >= len(self.instructions)

        # ROB está vazio
        rob_empty = not any(entry.busy for entry in self.rob)

        # Todas RSs estão livres
        all_rs = self.add_rs + self.mul_rs + self.load_buffers + self.store_buffers
        rs_empty = not any(rs.busy for rs in all_rs)

        return all_issued and rob_empty and rs_empty

    def get_ipc(self) -> float:
        """Calcula IPC (Instructions Per Cycle)"""
        if self.cycle == 0:
            return 0.0
        return self.instructions_committed / self.cycle

    def get_metrics(self) -> dict:
        """Retorna métricas de desempenho"""
        return {
            "Total de Ciclos": self.cycle,
            "Instruções Completadas": self.instructions_committed,
            "IPC": round(self.get_ipc(), 3),
            "Ciclos de Bolha": self.bubble_cycles,
            "Branch Mispredictions": self.branch_mispredictions,
        }


# ===========================
# INTERFACE GRÁFICA
# ===========================

class TomasulGUI:
    """Interface Gráfica do Simulador"""

    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Tomasulo - VERSÃO 2: Tela Única")
        self.root.geometry("1920x1080")  # Tela maior para caber tudo
        self.root.state('zoomed')  # Maximizado

        self.simulator = TomasulSimulator()

        self.setup_ui()
        self.load_example_program()

    def setup_ui(self):
        """Configura a interface"""
        # Menu superior
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Exemplo 1", command=self.load_example_program)
        file_menu.add_command(label="Limpar", command=self.clear_program)

        # Frame principal
        main_frame = ttk.Frame(self.root, padding="3")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # ===== ÁREA DE CÓDIGO =====
        code_frame = ttk.LabelFrame(main_frame, text="Programa MIPS", padding="2")
        code_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=2)

        self.code_text = scrolledtext.ScrolledText(code_frame, height=6, width=80)
        self.code_text.pack(fill=tk.BOTH, expand=True)

        # ===== CONTROLES =====
        control_frame = ttk.Frame(main_frame, padding="2")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)

        ttk.Button(control_frame, text="Carregar Programa",
                  command=self.load_program).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset",
                  command=self.reset_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Step (1 Ciclo)",
                  command=self.step_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Executar Tudo",
                  command=self.run_all).pack(side=tk.LEFT, padx=5)

        self.cycle_label = ttk.Label(control_frame, text="Ciclo: 0", font=('Arial', 12, 'bold'))
        self.cycle_label.pack(side=tk.LEFT, padx=20)

        # ===== LAYOUT EM GRID - TUDO VISÍVEL =====
        # Frame de visualizações
        viz_frame = ttk.Frame(main_frame, padding="2")
        viz_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.columnconfigure(1, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)
        viz_frame.rowconfigure(2, weight=1)

        # LINHA 1: Instruções (esquerda) + Métricas (direita)
        self.instructions_frame = ttk.LabelFrame(viz_frame, text="📋 INSTRUÇÕES", padding="2")
        self.instructions_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        self.setup_instructions_view()

        self.metrics_frame = ttk.LabelFrame(viz_frame, text="📊 MÉTRICAS", padding="2")
        self.metrics_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        self.setup_metrics_view()

        # LINHA 2: Reservation Stations (esquerda) + ROB (direita)
        self.rs_frame = ttk.LabelFrame(viz_frame, text="🔧 RESERVATION STATIONS", padding="2")
        self.rs_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        self.setup_rs_view()

        self.rob_frame = ttk.LabelFrame(viz_frame, text="📦 REORDER BUFFER (ROB)", padding="2")
        self.rob_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        self.setup_rob_view()

        # LINHA 3: Registradores (span 2 colunas)
        self.reg_frame = ttk.LabelFrame(viz_frame, text="📝 REGISTRADORES", padding="2")
        self.reg_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        self.setup_register_view()

    def setup_instructions_view(self):
        """Visualização das instruções"""
        columns = ('Linha', 'Instrução', 'Issue', 'Exec Start', 'Exec End', 'Write', 'Commit', 'ROB')
        self.inst_tree = ttk.Treeview(self.instructions_frame, columns=columns, show='headings', height=6)

        for col in columns:
            self.inst_tree.heading(col, text=col)
            self.inst_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.instructions_frame, orient=tk.VERTICAL, command=self.inst_tree.yview)
        self.inst_tree.configure(yscroll=scrollbar.set)

        self.inst_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_rs_view(self):
        """Visualização das Reservation Stations"""
        columns = ('Name', 'Busy', 'Op', 'Vj', 'Vk', 'Qj', 'Qk', 'ROB', 'Cycles')
        self.rs_tree = ttk.Treeview(self.rs_frame, columns=columns, show='headings', height=6)

        for col in columns:
            self.rs_tree.heading(col, text=col)
            self.rs_tree.column(col, width=80)

        scrollbar = ttk.Scrollbar(self.rs_frame, orient=tk.VERTICAL, command=self.rs_tree.yview)
        self.rs_tree.configure(yscroll=scrollbar.set)

        self.rs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_rob_view(self):
        """Visualização do ROB"""
        columns = ('Entry', 'Busy', 'Instruction', 'Destination', 'Value', 'Ready', 'Speculative')
        self.rob_tree = ttk.Treeview(self.rob_frame, columns=columns, show='headings', height=6)

        for col in columns:
            self.rob_tree.heading(col, text=col)
            self.rob_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.rob_frame, orient=tk.VERTICAL, command=self.rob_tree.yview)
        self.rob_tree.configure(yscroll=scrollbar.set)

        self.rob_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_register_view(self):
        """Visualização dos registradores"""
        columns = ('Registrador', 'Valor', 'Qi (ROB)')
        self.reg_tree = ttk.Treeview(self.reg_frame, columns=columns, show='headings', height=4)

        for col in columns:
            self.reg_tree.heading(col, text=col)
            self.reg_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(self.reg_frame, orient=tk.VERTICAL, command=self.reg_tree.yview)
        self.reg_tree.configure(yscroll=scrollbar.set)

        self.reg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_metrics_view(self):
        """Visualização de métricas"""
        self.metrics_text = scrolledtext.ScrolledText(self.metrics_frame, height=6, width=35,
                                                       font=('Courier', 9))
        self.metrics_text.pack(fill=tk.BOTH, expand=True)

    def load_example_program(self):
        """Carrega programa exemplo"""
        example = """# Exemplo: Multiplicação de Matriz
# Inicializa valores nos registradores
ADD R1, R0, R0     # R1 = 0
ADDI R2, R0, 10    # R2 = 10
ADDI R3, R0, 5     # R3 = 5

# Operações aritméticas
MUL F0, F1, F2     # F0 = F1 * F2
ADD F4, F0, F3     # F4 = F0 + F3
SUB F6, F4, F5     # F6 = F4 - F5
DIV F8, F6, F7     # F8 = F6 / F7

# Operações de memória
LOAD F10, 0(R1)    # F10 = Mem[R1]
STORE F10, 4(R1)   # Mem[R1+4] = F10

# Desvio condicional
BEQ R1, R2, 2      # if R1 == R2, pula 2 instruções
ADD F11, F10, F8   # Executado se não pular
MUL F12, F11, F0   # Executado se não pular
"""
        self.code_text.delete('1.0', tk.END)
        self.code_text.insert('1.0', example)

    def clear_program(self):
        """Limpa o programa"""
        self.code_text.delete('1.0', tk.END)
        self.reset_simulation()

    def load_program(self):
        """Carrega o programa no simulador"""
        program = self.code_text.get('1.0', tk.END)
        try:
            self.simulator.load_program(program)
            self.update_display()
            messagebox.showinfo("Sucesso", f"{len(self.simulator.instructions)} instruções carregadas!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar programa:\n{e}")

    def reset_simulation(self):
        """Reseta a simulação"""
        program = self.code_text.get('1.0', tk.END)
        self.simulator.load_program(program)
        self.update_display()

    def step_simulation(self):
        """Executa um passo (ciclo)"""
        if self.simulator.is_complete():
            messagebox.showinfo("Completo", "Simulação já está completa!")
            return

        self.simulator.step()
        self.update_display()

    def run_all(self):
        """Executa até o fim"""
        self.simulator.run_to_completion()
        self.update_display()
        messagebox.showinfo("Completo", "Simulação completa!")

    def update_display(self):
        """Atualiza todas as visualizações"""
        self.cycle_label.config(text=f"Ciclo: {self.simulator.cycle}")
        self.update_instructions_view()
        self.update_rs_view()
        self.update_rob_view()
        self.update_register_view()
        self.update_metrics_view()

    def update_instructions_view(self):
        """Atualiza visualização de instruções"""
        self.inst_tree.delete(*self.inst_tree.get_children())

        for inst in self.simulator.instructions:
            values = (
                inst.line_num,
                inst.original,
                inst.issue_cycle if inst.issue_cycle else '-',
                inst.execute_start_cycle if inst.execute_start_cycle else '-',
                inst.execute_end_cycle if inst.execute_end_cycle else '-',
                inst.write_result_cycle if inst.write_result_cycle else '-',
                inst.commit_cycle if inst.commit_cycle else '-',
                f"ROB{inst.rob_entry}" if inst.rob_entry is not None else '-'
            )
            self.inst_tree.insert('', tk.END, values=values)

    def update_rs_view(self):
        """Atualiza visualização de RSs"""
        self.rs_tree.delete(*self.rs_tree.get_children())

        all_rs = (self.simulator.add_rs + self.simulator.mul_rs +
                 self.simulator.load_buffers + self.simulator.store_buffers)

        for rs in all_rs:
            values = (
                rs.name,
                'Sim' if rs.busy else 'Não',
                rs.op.value if rs.op else '-',
                f"{rs.vj:.1f}" if rs.vj is not None else '-',
                f"{rs.vk:.1f}" if rs.vk is not None else '-',
                rs.qj if rs.qj else '-',
                rs.qk if rs.qk else '-',
                f"ROB{rs.rob_entry}" if rs.rob_entry is not None else '-',
                rs.cycles_remaining if rs.busy else '-'
            )
            self.rs_tree.insert('', tk.END, values=values)

    def update_rob_view(self):
        """Atualiza visualização do ROB"""
        self.rob_tree.delete(*self.rob_tree.get_children())

        for entry in self.simulator.rob:
            inst_str = entry.instruction.original if entry.instruction else '-'
            values = (
                f"ROB{entry.entry_num}",
                'Sim' if entry.busy else 'Não',
                inst_str[:30],  # Trunca se muito longo
                entry.destination if entry.destination else '-',
                f"{entry.value:.2f}" if entry.value is not None else '-',
                'Sim' if entry.ready else 'Não',
                'Sim' if entry.speculative else 'Não'
            )

            item = self.rob_tree.insert('', tk.END, values=values)

            # Destaca head e tail
            if entry.entry_num == self.simulator.rob_head and entry.busy:
                self.rob_tree.item(item, tags=('head',))
            if entry.entry_num == (self.simulator.rob_tail - 1) % self.simulator.rob_size:
                self.rob_tree.item(item, tags=('tail',))

        self.rob_tree.tag_configure('head', background='lightgreen')
        self.rob_tree.tag_configure('tail', background='lightblue')

    def update_register_view(self):
        """Atualiza visualização de registradores"""
        self.reg_tree.delete(*self.reg_tree.get_children())

        # Mostra apenas registradores relevantes
        regs_to_show = [f"R{i}" for i in range(10)] + [f"F{i}" for i in range(13)]

        for reg in regs_to_show:
            if reg in self.simulator.registers.values:
                qi_str = f"ROB{self.simulator.registers.qi[reg]}" if self.simulator.registers.qi[reg] is not None else '-'
                values = (
                    reg,
                    f"{self.simulator.registers.values[reg]:.2f}",
                    qi_str
                )
                self.reg_tree.insert('', tk.END, values=values)

    def update_metrics_view(self):
        """Atualiza visualização de métricas"""
        self.metrics_text.delete('1.0', tk.END)

        metrics = self.simulator.get_metrics()

        output = "=" * 60 + "\n"
        output += "MÉTRICAS DE DESEMPENHO\n"
        output += "=" * 60 + "\n\n"

        for key, value in metrics.items():
            output += f"{key:.<40} {value}\n"

        output += "\n" + "=" * 60 + "\n"
        output += "CONFIGURAÇÃO DO SIMULADOR\n"
        output += "=" * 60 + "\n\n"

        output += f"Reservation Stations Add/Sub:............ {self.simulator.num_add_rs}\n"
        output += f"Reservation Stations Mul/Div:............ {self.simulator.num_mul_rs}\n"
        output += f"Load Buffers:............................ {self.simulator.num_load_buffers}\n"
        output += f"Store Buffers:........................... {self.simulator.num_store_buffers}\n"
        output += f"Tamanho do ROB:.......................... {self.simulator.rob_size}\n\n"

        output += "LATÊNCIAS (ciclos):\n"
        for inst_type, cycles in self.simulator.latencies.items():
            output += f"  {inst_type.value:.<30} {cycles}\n"

        self.metrics_text.insert('1.0', output)


# ===========================
# MAIN
# ===========================

if __name__ == "__main__":
    root = tk.Tk()
    app = TomasulGUI(root)
    root.mainloop()
