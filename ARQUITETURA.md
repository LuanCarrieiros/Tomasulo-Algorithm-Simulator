# 🏗️ Arquitetura do Simulador

Este documento descreve a arquitetura interna do simulador para quem quiser modificar ou estender o código.

## 📁 Estrutura do Código

```
tomasulo_simulator.py (800+ linhas)
├── ENUMS E DATACLASSES
│   ├── InstructionType        # Tipos de instrução (ADD, MUL, etc.)
│   ├── RSType                 # Tipos de RS (Add/Sub, Mul/Div, etc.)
│   ├── Instruction            # Representa uma instrução
│   ├── ReservationStation     # Representa uma RS
│   ├── ROBEntry               # Entrada do ROB
│   └── RegisterFile           # Arquivo de registradores + RAT
│
├── PARSER DE INSTRUÇÕES
│   └── MIPSParser             # Converte texto → Instruction
│
├── SIMULADOR TOMASULO
│   └── TomasulSimulator       # Lógica principal do algoritmo
│       ├── Issue              # Despacho de instruções
│       ├── Execute            # Execução nas RSs
│       ├── Write Result       # Broadcast de resultados
│       └── Commit             # Commit in-order do ROB
│
└── INTERFACE GRÁFICA
    └── TomasulGUI             # Interface Tkinter
        ├── 5 abas de visualização
        └── Controles de execução
```

---

## 🔧 Classes Principais

### 1. `Instruction` (dataclass)

Representa uma instrução MIPS com todos seus metadados:

```python
@dataclass
class Instruction:
    line_num: int           # Número da linha
    original: str           # Texto original
    type: InstructionType   # ADD, MUL, LOAD, etc.
    dest: str               # Registrador destino
    src1: str               # Operando 1
    src2: str               # Operando 2
    immediate: int          # Valor imediato
    offset: int             # Offset para LOAD/STORE

    # Pipeline tracking
    issue_cycle: int
    execute_start_cycle: int
    execute_end_cycle: int
    write_result_cycle: int
    commit_cycle: int

    rob_entry: int          # Entrada do ROB alocada
```

### 2. `ReservationStation` (dataclass)

Representa uma estação de reserva:

```python
@dataclass
class ReservationStation:
    name: str               # "Add0", "Mul1", etc.
    type: RSType            # ADD_SUB, MUL_DIV, LOAD, STORE
    busy: bool              # Está ocupada?

    # Operandos
    vj: float               # Valor do operando J
    vk: float               # Valor do operando K
    qj: str                 # "ROB3" se esperando operando J
    qk: str                 # "ROB5" se esperando operando K

    # Execução
    op: InstructionType     # Operação sendo executada
    cycles_remaining: int   # Ciclos até terminar
    rob_entry: int          # ROB entry associada
    instruction: Instruction
```

**Estados possíveis de Qj/Qk:**
- `None`: Valor está pronto em Vj/Vk
- `"ROB3"`: Esperando resultado do ROB entry 3

### 3. `ROBEntry` (dataclass)

Entrada do Reorder Buffer:

```python
@dataclass
class ROBEntry:
    entry_num: int              # 0-15
    busy: bool                  # Está ocupada?
    instruction_type: InstructionType
    destination: str            # Registrador destino
    value: float                # Resultado calculado
    ready: bool                 # Resultado está pronto?
    speculative: bool           # É especulativa?
    instruction: Instruction
```

### 4. `RegisterFile`

Arquivo de registradores com Register Alias Table (RAT):

```python
class RegisterFile:
    values: Dict[str, float]    # "F0" → 5.0
    qi: Dict[str, int]          # "F0" → 3 (ROB entry)
```

**Qi (Register Alias Table):**
- `None`: Valor em `values` é válido
- `3`: Valor virá do ROB entry 3

---

## 🔄 Fluxo de Execução (Ciclo de Clock)

Cada ciclo executa **3 estágios em ordem reversa**:

```python
def step(self):
    self.cycle += 1

    # 1. Commit (mais velho primeiro)
    self.commit()

    # 2. Write Result / Execute
    self.execute()

    # 3. Issue (despachar nova instrução)
    self.issue_instruction()
```

**Por que ordem reversa?**
- Evita conflitos entre estágios no mesmo ciclo
- Commit libera ROB → Execute pode terminar → Issue pode alocar

---

## 📝 Detalhamento dos Estágios

### 1️⃣ Issue (Despacho)

```python
def issue_instruction(self) -> bool:
    # 1. Pega próxima instrução (PC)
    # 2. Verifica RS livre
    # 3. Verifica ROB livre
    # 4. Aloca RS e ROB
    # 5. Lê operandos ou registra dependências
    # 6. Atualiza RAT (Qi)
    # 7. Avança PC e ROB tail
```

**Leitura de operandos:**
```python
if registers.qi[src1] is not None:
    rs.qj = f"ROB{registers.qi[src1]}"  # Espera ROB
    rs.vj = None
else:
    rs.vj = registers.values[src1]      # Valor está pronto
    rs.qj = None
```

### 2️⃣ Execute

```python
def execute(self):
    for rs in all_reservation_stations:
        # Verifica se operandos estão prontos
        if rs.qj is not None or rs.qk is not None:
            continue  # Espera broadcast

        # Executa
        rs.cycles_remaining -= 1

        if rs.cycles_remaining == 0:
            # Calcula resultado
            result = compute(rs.op, rs.vj, rs.vk)

            # Write Result
            self.write_result(rs, result)
```

### 3️⃣ Write Result (Broadcast)

```python
def write_result(self, rs, result):
    # 1. Escreve no ROB
    rob[rs.rob_entry].value = result
    rob[rs.rob_entry].ready = True

    # 2. Broadcast para todas as RSs
    rob_tag = f"ROB{rs.rob_entry}"
    for other_rs in all_reservation_stations:
        if other_rs.qj == rob_tag:
            other_rs.vj = result
            other_rs.qj = None

        if other_rs.qk == rob_tag:
            other_rs.vk = result
            other_rs.qk = None

    # 3. Libera RS
    rs.busy = False
```

**Common Data Bus (CDB):**
- Simulado pelo broadcast para todas as RSs
- Uma única RS pode fazer broadcast por ciclo (simplificação)

### 4️⃣ Commit

```python
def commit(self):
    rob_entry = rob[rob_head]

    # Só faz commit se estiver pronto
    if not rob_entry.ready:
        return

    # Atualiza registrador
    if rob_entry.destination:
        if registers.qi[dest] == rob_head:
            registers.values[dest] = rob_entry.value
            registers.qi[dest] = None

    # Avança HEAD
    rob_head = (rob_head + 1) % rob_size
```

**Commit in-order:**
- Sempre processa ROB HEAD
- Preserva semântica do programa sequencial
- Permite exceções precisas

---

## 🎯 Especulação de Desvios

```python
# No Issue de BEQ/BNE:
if inst.type in [BEQ, BNE]:
    self.speculating = True
    self.speculation_rob_entry = rob_tail

# Todas instruções após BEQ:
if self.speculating:
    rob_entry.speculative = True

# No Commit do BEQ:
if rob_entry == speculation_rob_entry:
    self.speculating = False
```

**Implementação atual:**
- Predição: always not-taken (continua sequencial)
- Instruções especulativas executam normalmente
- Commit só após resolução do desvio

**Possível extensão:**
- Implementar flush do ROB se desvio for tomado
- Adicionar preditor de desvios (2-bit, gshare, etc.)

---

## 📊 Métricas de Desempenho

```python
def get_metrics(self):
    return {
        "Total de Ciclos": self.cycle,
        "Instruções Completadas": self.instructions_committed,
        "IPC": instructions_committed / cycle,
        "Ciclos de Bolha": self.bubble_cycles,
        "Branch Mispredictions": self.branch_mispredictions,
    }
```

**Ciclos de Bolha:**
- Incrementado quando Issue falha (sem RS/ROB livre)
- Indica stalls estruturais

---

## 🎨 Interface Gráfica (Tkinter)

### Arquitetura da GUI

```python
class TomasulGUI:
    def __init__(self):
        self.simulator = TomasulSimulator()
        self.setup_ui()

    def setup_ui(self):
        # 5 tabs (Notebook)
        # Controles (buttons)
        # Área de código (ScrolledText)

    def update_display(self):
        # Atualiza todas as visualizações
        self.update_instructions_view()
        self.update_rs_view()
        self.update_rob_view()
        self.update_register_view()
        self.update_metrics_view()
```

### Treeview (Tabelas)

Todas as abas usam `ttk.Treeview`:

```python
columns = ('Col1', 'Col2', ...)
tree = ttk.Treeview(frame, columns=columns, show='headings')

for col in columns:
    tree.heading(col, text=col)

tree.insert('', tk.END, values=(val1, val2, ...))
```

---

## 🔨 Como Estender

### 1. Adicionar Nova Instrução

```python
# 1. Adicione ao enum
class InstructionType(Enum):
    ...
    AND = "AND"

# 2. Adicione ao parser
def parse_instruction(line, line_num):
    ...
    elif op == 'AND':
        return Instruction(..., InstructionType.AND, ...)

# 3. Adicione latência
self.latencies[InstructionType.AND] = 1

# 4. Adicione lógica de execução
def execute(self):
    ...
    elif rs.op == InstructionType.AND:
        result = int(rs.vj) & int(rs.vk)
```

### 2. Mudar Número de RSs

```python
def __init__(self):
    self.num_add_rs = 5  # Era 3
    self.num_mul_rs = 4  # Era 2
```

### 3. Mudar Latências

```python
self.latencies = {
    InstructionType.ADD: 1,   # Era 2
    InstructionType.MUL: 5,   # Era 10
    InstructionType.DIV: 20,  # Era 40
}
```

### 4. Implementar Preditor de Desvios

```python
class BranchPredictor:
    def predict(self, pc):
        # Implementar 2-bit saturating counter
        pass

    def update(self, pc, taken):
        pass

# No simulador:
def issue_instruction(self):
    if inst.type == BEQ:
        prediction = self.branch_predictor.predict(self.pc)
        if prediction:
            self.pc = compute_target(inst.offset)
```

### 5. Adicionar Cache

```python
class Cache:
    def __init__(self, size, line_size):
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def read(self, addr):
        if addr in self.cache:
            self.hits += 1
            return self.cache[addr], hit=True
        else:
            self.misses += 1
            return self.memory[addr], hit=False

# Atualizar latência de LOAD dinamicamente
if cache_hit:
    rs.cycles_remaining = 1
else:
    rs.cycles_remaining = 100  # Cache miss!
```

---

## 🐛 Debugging

### Logging

Adicione prints para debug:

```python
def issue_instruction(self):
    print(f"Cycle {self.cycle}: Issuing {inst.original} to {rs.name}")

def commit(self):
    print(f"Cycle {self.cycle}: Committing {rob_entry.instruction.original}")
```

### Breakpoints

Use o debugger do Python:

```python
import pdb

def step(self):
    self.cycle += 1
    if self.cycle == 10:
        pdb.set_trace()  # Para no ciclo 10
```

---

## 📚 Referências da Implementação

### Algoritmo de Tomasulo Original
- Proposto por Robert Tomasulo (IBM, 1967)
- Usado no IBM System/360 Model 91

### Modificações para Fins Didáticos
1. **ROB**: Adicionado (não estava no original)
2. **Especulação**: Simplificada
3. **CDB**: Uma transmissão por ciclo (original tinha múltiplos)
4. **Memória**: Simplificada (sem cache)

### Livro de Referência
- **Computer Architecture: A Quantitative Approach**
  - Hennessy & Patterson
  - Capítulo sobre Dynamic Scheduling

---

## 🎓 Conceitos Avançados Não Implementados

Possíveis extensões para projetos futuros:

1. **Multiple Issue**: Despachar N instruções por ciclo
2. **Multiple CDB**: Vários broadcasts simultâneos
3. **Memory Disambiguation**: Load/Store em qualquer ordem
4. **Register Renaming Table**: Separada do ROB
5. **Exceções**: Tratamento preciso de exceções
6. **Cache Hierarchy**: L1, L2, L3
7. **Pipelining das RSs**: Instruções pipelined
8. **Preditor de Desvio**: Tournament, gshare, TAGE

---

## 📝 Notas de Implementação

### Decisões de Design

1. **ROB circular**: Usa modulo para índices
2. **RS liberada após Write**: Simplifica gerenciamento
3. **Commit in-order**: Mantém semântica correta
4. **Valores iniciais**: Registradores têm valores para facilitar testes

### Simplificações

1. **Sem exceções**: Não trata divisão por zero, overflow, etc.
2. **Memória infinita**: Sem proteção ou limites
3. **Sem cache**: Latência de memória constante
4. **Predição simplificada**: Always not-taken

### Trade-offs

| Realismo | vs | Simplicidade Didática |
|----------|----|-----------------------|
| Cache real | ✗ | Latência fixa ✓ |
| Múltiplos CDB | ✗ | Um broadcast ✓ |
| Exceções | ✗ | Sem tratamento ✓ |

---

**Este simulador prioriza clareza e aprendizado sobre realismo absoluto!** 🎓
