# 🏗️ Arquitetura do Simulador

Este documento descreve a arquitetura interna do simulador para quem quiser modificar ou estender o código.

## 📁 Estrutura Modular do Código

O projeto foi reorganizado em uma arquitetura modular com separação de responsabilidades:

```
Tomasulo-Algorithm-Simulator/
├── Instruction.py              # Classe de instrução e enum de operações
├── ReservationStation.py       # Classe de estação de reserva
├── RegisterFile.py             # Gerenciamento de registradores e RAT
├── TOMASSULLLERoriSimulator.py # Motor de simulação (lógica do Tomasulo)
└── TOMASSULLLERoriGUI.py       # Interface gráfica (Tkinter)
```

### Fluxo de Dados

```
TOMASSULLLERoriGUI
    ↓ configura
TOMASSULLLERoriSimulator
    ↓ usa
Instruction, ReservationStation, RegisterFile
```

---

## 🔧 Módulos e Classes

### 1. `Instruction.py` - Representação de Instruções

Define o enum de operações e a classe de instrução.

**Enum Op**:
```python
class Op(Enum):
    ADD = "ADD"
    SUB = "SUB"
    LD = "LD"
    ST = "ST"
    BEQ = "BEQ"
    BNE = "BNE"
    MUL = "MUL"
    DIV = "DIV"
```

**Classe Instruction**:
```python
class Instruction:
    id: int                 # ID único da instrução
    op: Op                  # Operação (ADD, MUL, etc.)
    dest: str               # Registrador destino
    src1: str               # Operando fonte 1
    src2: str               # Operando fonte 2
    original_latency: int   # Latência original da operação
    current_latency: int    # Latência restante

    # Pipeline tracking
    issue_cycle: int
    start_exec_cycle: int
    end_exec_cycle: int
    write_result_cycle: int
    commit_cycle: int

    # Campos para branches
    branch_target_id: int
    branch_taken: bool
    branch_resolved: bool
    squashed: bool          # Se foi descartada
```

**Principais métodos**: Getters e setters para todos os campos

### 2. `ReservationStation.py` - Estações de Reserva

Implementa as estações de reserva que armazenam instruções aguardando execução.

**Classe ReservationStation**:
```python
class ReservationStation:
    name: str               # "RS_ADD_1", "RS_MULT_1", etc.
    busy: bool              # Está ocupada?

    # Operandos
    Vj: float               # Valor do operando J
    Vk: float               # Valor do operando K
    Qj: str                 # Tag da RS produzindo operando J
    Qk: str                 # Tag da RS produzindo operando K

    # Execução
    op: Op                  # Operação sendo executada
    instruction: Instruction # Referência para a instrução
    result: float           # Resultado calculado
```

**Principais métodos**:
- `assign(instruction, op, Qj, Vj, Qk, Vk)`: Atribui uma instrução à RS
- `free()`: Libera a RS
- `is_ready_to_execute()`: Verifica se Qj e Qk são None (operandos prontos)
- `set_Vj(vj)` / `set_Vk(vk)`: Atualiza valores e limpa dependências

**Estados possíveis de Qj/Qk:**
- `None`: Valor está pronto em Vj/Vk
- `"RS_ADD_1"`: Esperando resultado da RS_ADD_1

### 3. `RegisterFile.py` - Gerenciamento de Registradores

Implementa o Register File e a Register Alias Table (RAT).

**Classe RegisterStatus**:
```python
class RegisterStatus:
    value: float            # Valor atual do registrador
    producer_tag: str       # Tag da RS que produzirá o próximo valor
```

**Classe RegisterFile**:
```python
class RegisterFile:
    registers: Dict[str, RegisterStatus]  # "R0" → RegisterStatus
```

**Principais métodos**:
- `get_register_status(register_name)`: Retorna status de um registrador
- `update_register_status(register_name, value, producer_tag)`: Atualiza valor e produtor

**Producer Tag (Register Alias Table - RAT)**:
- `None`: Valor em `value` é válido e atualizado
- `"RS_MULT_1"`: Próximo valor virá da RS_MULT_1

---

### 4. `TOMASSULLLERoriSimulator.py` - Motor de Simulação

O coração do simulador, implementa a lógica do algoritmo de Tomasulo.

**Classe TOMASSULLLERoriSimulator**:
```python
class TOMASSULLLERoriSimulator:
    # Configurações
    add_sub_latency, load_latency, store_latency: int
    mult_latency, div_latency, branch_latency: int

    # Estruturas principais
    register_file: RegisterFile
    rs_add: List[ReservationStation]      # RSs para ADD/SUB
    rs_store: List[ReservationStation]    # RSs para LOAD/STORE
    rs_mult: List[ReservationStation]     # RSs para MUL/DIV
    rs_branch: List[ReservationStation]   # RSs para BRANCH

    # Estado da simulação
    all_instructions: List[Instruction]
    current_clock: int
    program_counter: int
    bubble_cycles: int

    # Common Data Bus
    cdb_producer_tag: str
    cdb_value: float
```

**Principais métodos**:
- `set_instructions(instructions)`: Carrega instruções
- `next_cycle()`: Avança um ciclo
- `run_to_end()`: Executa até o fim
- `is_simulation_finished()`: Verifica se todas instruções foram comitadas

### 5. `TOMASSULLLERoriGUI.py` - Interface Gráfica

Interface Tkinter com visualização completa do estado do simulador.

**Principais componentes**:
- Painel de configuração (unidades funcionais e latências)
- Área de entrada de código (copy/paste)
- Tabela de status das instruções
- Tabela de estações de reserva
- Tabela do register file
- Display de métricas (IPC, ciclos, bolhas)

---

## 🔄 Fluxo de Execução (Ciclo de Clock)

Cada ciclo executa **4 estágios sequencialmente**:

```python
def next_cycle(self):
    self.current_clock += 1

    # 1. Commit (mais velho primeiro)
    self.commit_instructions()

    # 2. Write Result (broadcast no CDB)
    self.write_result_to_cdb()

    # 3. Execute (decrementa latências)
    self.execute_instructions()

    # 4. Issue (despachar nova instrução)
    self.issue_from_instruction_queue()
```

**Por que essa ordem?**
- Commit libera RSs → Write Result pode liberar → Execute pode terminar → Issue pode alocar
- Evita conflitos entre estágios no mesmo ciclo
- Simula o comportamento real do hardware

---

## 📝 Detalhamento dos Estágios

### 1️⃣ Issue (Despacho) - `issue_from_instruction_queue()`

**Fluxo**:
```python
# 1. Pega próxima instrução (PC)
instr_to_issue = all_instructions[program_counter]

# 2. Determina tipo de RS necessária
if instr.op in [ADD, SUB]: target_rs_array = rs_add
elif instr.op in [LD, ST]: target_rs_array = rs_store
elif instr.op in [MUL, DIV]: target_rs_array = rs_mult
elif instr.op in [BEQ, BNE]: target_rs_array = rs_branch

# 3. Verifica RS livre
for rs in target_rs_array:
    if not rs.is_busy():
        # 4. Lê operandos ou registra dependências
        src1_status = register_file.get_register_status(src1)
        if src1_status.producer_tag is not None:
            Qj = src1_status.producer_tag  # Espera RS
            Vj = None
        else:
            Vj = src1_status.value          # Valor pronto
            Qj = None

        # 5. Aloca RS
        rs.assign(instr, op, Qj, Vj, Qk, Vk)

        # 6. Atualiza RAT
        register_file.update_register_status(dest, None, rs.name)

        # 7. Avança PC
        program_counter += 1
```

**Se não há RS livre**: Incrementa `bubble_cycles` (stall estrutural)

### 2️⃣ Execute - `execute_instructions()`

**Fluxo**:
```python
def execute_instructions(self):
    all_rs = rs_add + rs_store + rs_mult + rs_branch

    for rs in all_rs:
        if rs.is_busy():
            instr = rs.get_instruction()

            # Se operandos prontos e ainda não começou
            if instr.start_exec_cycle == -1 and rs.is_ready_to_execute():
                instr.set_start_exec_cycle(current_clock)

            # Se já está executando
            elif instr.start_exec_cycle != -1 and instr.end_exec_cycle == -1:
                # Decrementa latência
                instr.set_current_latency(instr.current_latency - 1)

                # Se terminou
                if instr.current_latency == 0:
                    instr.set_end_exec_cycle(current_clock)

                    # Para branches, marca como tomado
                    if rs.op in [BEQ, BNE]:
                        instr.set_branch_taken(True)
                        instr.set_branch_resolved(True)

                    rs.set_result(resultado_calculado)
```

**Observações**:
- Instruções só executam quando Qj == Qk == None
- Cada RS decrementa sua latência independentemente (paralelismo!)
- Branches nesta implementação sempre são tomados

### 3️⃣ Write Result - `write_result_to_cdb()`

**Fluxo**:
```python
def write_result_to_cdb(self):
    # Limpa CDB
    cdb_producer_tag = None
    cdb_value = None

    # Procura primeira RS que terminou execução
    for rs in all_reservation_stations:
        if (rs.is_busy() and
            rs.instruction.end_exec_cycle != -1 and
            rs.instruction.write_result_cycle == -1):

            # Publica no CDB (apenas uma por ciclo)
            cdb_producer_tag = rs.name
            cdb_value = rs.result
            rs.instruction.set_write_result_cycle(current_clock)

            # Broadcast para todas as RSs
            update_reservation_stations_from_cdb(cdb_producer_tag, cdb_value)

            # Atualiza Register File
            update_register_file_from_cdb(cdb_producer_tag, cdb_value, rs.instruction.dest)

            return  # Apenas uma RS escreve por ciclo
```

**Broadcast (Common Data Bus)**:
```python
def update_reservation_stations_from_cdb(producer_tag, value):
    for rs in all_reservation_stations:
        if rs.is_busy():
            # Atualiza Qj/Vj
            if rs.Qj == producer_tag:
                rs.set_Vj(value)  # Limpa Qj automaticamente

            # Atualiza Qk/Vk
            if rs.Qk == producer_tag:
                rs.set_Vk(value)  # Limpa Qk automaticamente
```

**Simplificação**: Apenas uma RS pode escrever no CDB por ciclo (hardware real pode ter múltiplos)

### 4️⃣ Commit - `commit_instructions()`

**Fluxo**:
```python
def commit_instructions(self):
    # Encontra primeira instrução não comitada
    for i, instr in enumerate(all_instructions):
        if not instr.squashed and instr.commit_cycle == -1:
            instr_to_commit = instr
            break

    # Só comita se write_result já ocorreu
    if instr_to_commit.write_result_cycle != -1:
        instr_to_commit.set_commit_cycle(current_clock)

        # Se é branch tomado, faz squashing
        if instr.op in [BEQ, BNE] and instr.branch_taken:
            # Descarta todas instruções entre esta e o alvo
            for future_instr in all_instructions[i+1:]:
                if future_instr.commit_cycle == -1:
                    future_instr.set_squashed(True)
                    free_reservation_station(future_instr)

            # Reposiciona PC para o alvo
            program_counter = instr.branch_target_id

        # Libera RS
        free_reservation_station(instr_to_commit)
```

**Commit in-order:**
- Sempre processa a primeira instrução não comitada (sequencial)
- Preserva semântica do programa original
- Permite tratamento preciso de exceções (se implementado)

---

## 🎯 Especulação de Desvios

**Implementação atual**:
```python
# No Execute de BEQ/BNE:
if rs.op in [Op.BEQ, Op.BNE] and not instr.is_branch_resolved():
    instr.set_branch_taken(True)        # Sempre toma o branch
    instr.set_branch_resolved(True)
    res = 1.0  # Simboliza branch tomado

# No Commit do BEQ/BNE:
if instr.op in [Op.BEQ, Op.BNE] and instr.is_branch_taken():
    # Squashing: descarta instruções especulativas
    for i in range(instr_index + 1, len(all_instructions)):
        future_instr = all_instructions[i]
        if future_instr.commit_cycle == -1 and not future_instr.is_squashed():
            future_instr.set_squashed(True)
            free_reservation_station(future_instr)

    # Reposiciona PC
    program_counter = instr.branch_target_id
```

**Comportamento**:
- Branches **sempre são tomados** nesta implementação (simplificação)
- Instruções após o branch executam especulativamente
- No commit do branch, instruções entre ele e o alvo são descartadas (squashed)
- PC é reposicionado para a instrução alvo

**Possível extensão**:
- Adicionar preditor de desvios (2-bit saturating counter, gshare, etc.)
- Implementar flush mais eficiente das RSs
- Suportar predição "not-taken" também

---

## 📊 Métricas de Desempenho

```python
def calculate_ipc(self):
    committed_count = 0
    for instr in all_instructions:
        if instr.commit_cycle != -1 and not instr.is_squashed():
            committed_count += 1
    if current_clock == 0:
        return 0.0
    return committed_count / current_clock
```

**Métricas coletadas**:
- **IPC (Instructions Per Cycle)**: Instruções comitadas / ciclos totais
- **Total de Ciclos**: Contador de clock (`current_clock`)
- **Ciclos de Bolha**: Incrementado quando Issue falha (stall estrutural)

**Ciclos de Bolha ocorrem quando**:
- Não há RS livre do tipo necessário (stall estrutural)
- Instrução não pode executar por falta de operandos (stall de dados)

---

## 🎨 Interface Gráfica (Tkinter)

### Arquitetura da GUI

```python
class TOMASSULLLERoriGUI:
    def __init__(self, root):
        self.simulator = None  # Criado após configuração
        self.init_components()
        self.add_listeners()

    def init_components(self):
        # Painel esquerdo: Configuração
        #   - Inputs para quantidade de unidades funcionais
        #   - Inputs para latências
        #   - Botão "Configurar Simulador"
        #   - Área de texto para carregar instruções (copy/paste)

        # Painel direito: Visualizações
        #   - Display de clock
        #   - Botões "Próximo Ciclo" e "Executar Tudo"
        #   - Tabela de status das instruções (Treeview)
        #   - Tabela de estações de reserva (Treeview)
        #   - Tabela de register file (Treeview)
        #   - Display de métricas

    def update_tables(self):
        # Chamado após cada ciclo
        self.update_instruction_table()
        self.update_rs_table()
        self.update_register_table()
        self.update_metrics()
```

### Parser de Instruções na GUI

```python
def parse_instructions_from_text(self, text):
    # Parse linha por linha
    # Formato: OP DEST SRC1 SRC2
    # Exemplo: ADD R1 R2 R3
    # Cria objetos Instruction com latências apropriadas
    # Retorna lista de instruções
```

### Treeview (Tabelas)

Todas as tabelas usam `ttk.Treeview`:

```python
columns = ("ID", "Op", "Dest", "Src1", "Src2", ...)
tree = ttk.Treeview(frame, columns=columns, show='headings')

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=70, anchor=tk.CENTER)

# Inserção de dados
tree.insert('', tk.END, values=(val1, val2, val3, ...))
```

---

## 🔨 Como Estender o Simulador

### 1. Adicionar Nova Instrução

**Passo 1**: Adicione ao enum em `Instruction.py`:
```python
class Op(Enum):
    # ... operações existentes
    AND = "AND"  # Nova operação
```

**Passo 2**: Modifique o parser na GUI (`TOMASSULLLERoriGUI.py:329`):
```python
try:
    op = Op[op_str]  # Já funciona se você adicionou ao enum
except KeyError:
    messagebox.showerror("Erro", f"Operação '{op_str}' inválida")
```

**Passo 3**: Adicione mapeamento de RS no simulador (`TOMASSULLLERoriSimulator.py:104`):
```python
if instr_to_issue.get_op() in [Op.ADD, Op.SUB, Op.AND]:  # Adicione AND aqui
    target_rs_array = self.rs_add
```

**Passo 4**: Adicione latência padrão na GUI (`TOMASSULLLERoriGUI.py:339`):
```python
if op in [Op.ADD, Op.SUB, Op.AND]:
    latency = int(self.lat_add.get())
```

### 2. Mudar Número de RSs

Modifique os valores padrão na GUI (`TOMASSULLLERoriGUI.py:36-53`) ou use a interface:

```python
self.fu_add.insert(0, "3")    # Era 1, agora 3 RSs para ADD/SUB
self.fu_mult.insert(0, "2")   # Era 1, agora 2 RSs para MUL/DIV
```

### 3. Mudar Latências Padrão

Modifique os valores na GUI (`TOMASSULLLERoriGUI.py:61-87`):

```python
self.lat_add.insert(0, "1")      # ADD/SUB: 1 ciclo (era 2)
self.lat_mult.insert(0, "5")     # MUL: 5 ciclos (era 3)
self.lat_div.insert(0, "20")     # DIV: 20 ciclos (era 3)
```

### 4. Implementar Preditor de Desvios

**Criar nova classe** (`BranchPredictor.py`):
```python
class BranchPredictor:
    def __init__(self):
        self.predictor = {}  # PC → contador de 2 bits

    def predict(self, pc):
        # 00, 01 → not taken
        # 10, 11 → taken
        counter = self.predictor.get(pc, 1)  # Default: weakly not-taken
        return counter >= 2

    def update(self, pc, taken):
        counter = self.predictor.get(pc, 1)
        if taken:
            counter = min(3, counter + 1)
        else:
            counter = max(0, counter - 1)
        self.predictor[pc] = counter
```

**Integrar no simulador** (`TOMASSULLLERoriSimulator.py:188`):
```python
# No execute, ao invés de sempre tomar:
if rs.op in [Op.BEQ, Op.BNE] and not instr.is_branch_resolved():
    prediction = self.branch_predictor.predict(instr.get_id())
    instr.set_branch_taken(prediction)  # Usa predição
    instr.set_branch_resolved(True)

# No commit, atualiza o preditor:
if instr.op in [Op.BEQ, Op.BNE]:
    actual_taken = self.evaluate_branch(instr)
    self.branch_predictor.update(instr.get_id(), actual_taken)
```

### 5. Adicionar Hierarquia de Cache

**Criar nova classe** (`Cache.py`):
```python
class Cache:
    def __init__(self, size, block_size, hit_latency, miss_penalty):
        self.size = size
        self.block_size = block_size
        self.hit_latency = hit_latency
        self.miss_penalty = miss_penalty
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def access(self, addr):
        block_addr = addr // self.block_size
        if block_addr in self.cache:
            self.hits += 1
            return self.hit_latency
        else:
            self.misses += 1
            self.cache[block_addr] = True  # Simplificado
            return self.miss_penalty
```

**Integrar no simulador**: Modificar latências de LOAD dinamicamente baseado em cache hit/miss

### 6. Adicionar Múltiplos CDBs

Atualmente apenas uma RS escreve por ciclo. Para permitir múltiplos:

**Modificar** `write_result_to_cdb()` em `TOMASSULLLERoriSimulator.py:196`:
```python
def write_result_to_cdb(self):
    max_writes_per_cycle = 2  # Permite 2 escritas simultâneas

    writes_done = 0
    for rs in all_reservation_stations:
        if writes_done >= max_writes_per_cycle:
            break

        if (rs.is_busy() and
            rs.instruction.end_exec_cycle != -1 and
            rs.instruction.write_result_cycle == -1):

            # Publica no CDB
            self.cdb_producer_tag = rs.name
            self.cdb_value = rs.result
            rs.instruction.set_write_result_cycle(current_clock)

            update_reservation_stations_from_cdb(...)
            update_register_file_from_cdb(...)

            writes_done += 1
```

---

## 🐛 Debugging e Testes

### Logging

Adicione prints para debug em `TOMASSULLLERoriSimulator.py`:

```python
def issue_from_instruction_queue(self):
    print(f"Ciclo {self.current_clock}: Issue - Instrução {instr.get_id()} "
          f"({instr.get_op().value}) para {rs.get_name()}")

def commit_instructions(self):
    print(f"Ciclo {self.current_clock}: Commit - Instrução {instr.get_id()} "
          f"({instr.get_op().value})")

def write_result_to_cdb(self):
    print(f"Ciclo {self.current_clock}: Write Result - {rs.get_name()} "
          f"publica {rs.get_result()} no CDB")
```

### Testes Unitários

Crie arquivo `test_simulator.py`:

```python
import unittest
from Instruction import Instruction, Op
from TOMASSULLLERoriSimulator import TOMASSULLLERoriSimulator

class TestTomasulo(unittest.TestCase):
    def test_issue_simple_add(self):
        sim = TOMASSULLLERoriSimulator(1, 1, 1, 1, 2, 6, 6, 3, 3, 4)
        instr = Instruction(0, Op.ADD, "R1", "R2", "R3", 2)
        sim.set_instructions([instr])

        sim.next_cycle()  # Issue
        self.assertEqual(instr.get_issue_cycle(), 1)

    def test_dependency_detection(self):
        sim = TOMASSULLLERoriSimulator(2, 1, 1, 1, 2, 6, 6, 3, 3, 4)
        instr1 = Instruction(0, Op.ADD, "R1", "R2", "R3", 2)
        instr2 = Instruction(1, Op.MUL, "R4", "R1", "R5", 3)
        sim.set_instructions([instr1, instr2])

        sim.next_cycle()  # Issue ADD
        sim.next_cycle()  # Issue MUL (depende de ADD)

        # Verifica dependência
        rs_mult = sim.get_rs_mult()[0]
        self.assertIsNotNone(rs_mult.get_Qj())  # Deve esperar R1

if __name__ == '__main__':
    unittest.main()
```

### Debugging com IDE

Use breakpoints no Visual Studio Code ou PyCharm:

1. Coloque breakpoint em `TOMASSULLLERoriSimulator.py:70` (no `next_cycle()`)
2. Execute em modo debug
3. Inspecione variáveis: `rs_add`, `register_file`, `current_clock`

---

## 📚 Referências e Conceitos

### Algoritmo de Tomasulo Original
- **Proposto por**: Robert Tomasulo (IBM, 1967)
- **Usado em**: IBM System/360 Model 91
- **Inovação**: Renomeação dinâmica de registradores sem ROB

### Modificações desta Implementação
1. **Sem ROB explícito**: Tags são nomes das RSs, não entradas de ROB
2. **Especulação simplificada**: Branches sempre tomados
3. **CDB**: Uma transmissão por ciclo (hardware real pode ter múltiplos)
4. **Memória**: Simplificada, sem hierarquia de cache
5. **Arquitetura modular**: Separada em múltiplos arquivos Python

### Livros de Referência
- **Computer Architecture: A Quantitative Approach**
  - Hennessy & Patterson (6ª edição)
  - Capítulo 3: Instruction-Level Parallelism
  - Seção 3.4: Dynamic Scheduling (Tomasulo)

- **Computer Organization and Design**
  - Patterson & Hennessy (5ª edição)
  - Capítulo 4: The Processor

---

## 🎓 Conceitos Avançados Não Implementados

Possíveis extensões para projetos futuros:

1. **Reorder Buffer (ROB) explícito**: Separar renomeação de commit
2. **Multiple Issue**: Despachar 2+ instruções por ciclo (superescalar)
3. **Multiple CDB**: Vários broadcasts simultâneos
4. **Memory Disambiguation**: Load/Store fora de ordem com análise de endereços
5. **Exceções precisas**: Tratamento de divisão por zero, overflow, page faults
6. **Cache Hierarchy**: L1, L2, L3 com diferentes latências
7. **Preditor de Desvio**: 2-bit saturating, gshare, tournament, TAGE
8. **Speculative Execution**: Melhor gerenciamento de instruções especulativas
9. **Register Renaming físico**: Physical Register File separado
10. **Superscalar widening**: Pipeline mais largo com múltiplos issue/commit

---

## 📝 Notas de Implementação

### Decisões de Design

1. **Arquitetura modular**: Facilita manutenção e extensão
2. **Tags usam nomes de RS**: Simplifica rastreamento de dependências
3. **Commit in-order**: Preserva semântica sequencial do programa
4. **Valores iniciais R0-R10**: Facilita testes sem inicialização manual
5. **GUI configurável**: Permite experimentar diferentes configurações

### Simplificações

1. **Sem ROB explícito**: RSs servem como buffer temporário
2. **Sem exceções**: Não trata erros de execução
3. **Memória infinita**: Sem limites ou proteção de memória
4. **Sem cache**: Latência de LOAD/STORE é constante
5. **Predição always-taken**: Simplifica lógica de branches
6. **CDB único**: Apenas uma RS escreve por ciclo

### Trade-offs

| Característica | Realismo | Simplicidade Didática |
|----------------|----------|-----------------------|
| Cache real     | ✗        | Latência fixa ✓       |
| Múltiplos CDB  | ✗        | Um broadcast ✓        |
| ROB explícito  | ✗        | RSs como buffer ✓     |
| Exceções       | ✗        | Sem tratamento ✓      |
| Predição complexa | ✗     | Always-taken ✓        |

---

## 👥 Contribuidores

- Arthur Clemente Machado
- Arthur Gonçalves de Moraes
- Bernardo Ferreira Temponi
- Diego Moreira Rocha
- Luan Barbosa Rosa Carrieiros

---

**Este simulador prioriza clareza e aprendizado sobre realismo absoluto!** 🎓
**Para dúvidas ou sugestões, consulte o README.md ou abra uma issue no repositório.**
