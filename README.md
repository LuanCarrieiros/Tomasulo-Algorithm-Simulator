# Simulador do Algoritmo de Tomasulo

Simulador didático do **Algoritmo de Tomasulo** com suporte a:
- ✅ Estações de Reserva (Reservation Stations)
- ✅ Execução fora de ordem (Out-of-Order Execution)
- ✅ Especulação de desvios condicionais
- ✅ Execução passo a passo
- ✅ Interface gráfica intuitiva
- ✅ Métricas de desempenho (IPC, ciclos, bolhas, etc.)

## 👥 Equipe de Desenvolvimento

- Arthur Clemente Machado
- Arthur Gonçalves de Moraes
- Bernardo Ferreira Temponi
- Diego Moreira Rocha
- Luan Barbosa Rosa Carrieiros

## 📋 Requisitos

- Python 3.7 ou superior
- Tkinter (geralmente já vem com Python)

## 🚀 Como Executar

```bash
python TOMASSULLLERoriGUI.py
```

## 📖 Como Usar

### 1. Configurar Simulador
Na janela principal, configure:
- **Unidades Funcionais**: Quantidade de cada tipo de estação de reserva
  - ADD/SUB: Unidades para adição e subtração
  - LOAD/STORE: Buffers para operações de memória
  - MUL/DIV: Unidades para multiplicação e divisão
  - BRANCH: Unidades para desvios condicionais

- **Latências**: Número de ciclos para cada tipo de operação
  - ADD/SUB: Latência de adição/subtração (padrão: 2 ciclos)
  - LOAD: Latência de leitura de memória (padrão: 6 ciclos)
  - STORE: Latência de escrita em memória (padrão: 6 ciclos)
  - MUL: Latência de multiplicação (padrão: 3 ciclos)
  - DIV: Latência de divisão (padrão: 3 ciclos)
  - BRANCH: Latência de desvio (padrão: 4 ciclos)

- Clique em **"Configurar Simulador"** após definir os parâmetros

### 2. Carregar Instruções
- Cole ou digite suas instruções na área de texto
- Formato: `OP DEST SRC1 SRC2`
- Exemplo: `ADD R1 R2 R3`
- Linhas começando com `#` são comentários e serão ignoradas
- Clique em **"Carregar do Texto"** para processar as instruções

### 3. Executar Simulação

Dois modos de execução:

- **Próximo Ciclo**: Executa um ciclo de clock por vez (ideal para aprendizado)
- **Executar Tudo**: Executa até o final automaticamente

### 4. Visualizações Disponíveis

#### 📊 Status das Instruções
Mostra o pipeline de cada instrução com os ciclos de:
- **Issue**: Quando foi despachada
- **Exec Start**: Início da execução
- **Exec End**: Fim da execução
- **Write Result**: Escrita do resultado no CDB
- **Commit**: Commit final (in-order)
- **Squashed**: Indica se a instrução foi descartada (por branch misprediction)

#### 🔧 Estações de Reserva
Visualiza o estado de todas as Reservation Stations:
- Nome da estação (RS_ADD_1, RS_MULT_1, etc.)
- Busy: Se está ocupada
- Op: Operação sendo executada
- Vj, Vk: Valores dos operandos
- Qj, Qk: Tags das estações produzindo operandos (dependências)

#### 📝 Register File
Mostra o estado dos registradores:
- **R0-R10**: Registradores disponíveis
- **Valor**: Valor atual do registrador
- **Produtor**: Tag da RS que produzirá o próximo valor (Register Alias Table)

#### 📈 Métricas
Apresenta estatísticas de desempenho em tempo real:
- **IPC**: Instructions Per Cycle (quanto maior, melhor!)
- **Ciclos Gastos**: Total de ciclos executados
- **Ciclos Bolha**: Ciclos desperdiçados por stalls estruturais

## 💡 Instruções Suportadas

### Formato Geral
```
OP DEST SRC1 SRC2
```

### Aritméticas
```assembly
ADD R1 R2 R3      # R1 = R2 + R3
SUB R1 R2 R3      # R1 = R2 - R3
MUL R4 R1 R5      # R4 = R1 * R5
DIV R6 R4 R2      # R6 = R4 / R2
```

### Memória
```assembly
LD R1 R2 0        # R1 = Mem[R2 + 0]
ST R3 R4 8        # Mem[R4 + 8] = R3
```

### Desvios Condicionais
```assembly
BEQ TARGET_ID R1 R2    # Se R1 == R2, pula para instrução TARGET_ID
BNE TARGET_ID R1 R2    # Se R1 != R2, pula para instrução TARGET_ID
```
**Nota**: Para branches, DEST é substituído pelo ID da instrução alvo (baseado em zero)

### Comentários
```assembly
# Isto é um comentário
ADD R1 R2 R3  # Comentário inline também funciona
```

## ⚙️ Configurações do Simulador

### Unidades Funcionais (Configurável via GUI)
- **ADD/SUB**: Reservation Stations para adição e subtração (padrão: 1)
- **LOAD/STORE**: Buffers para operações de memória (padrão: 1)
- **MUL/DIV**: Reservation Stations para multiplicação e divisão (padrão: 1)
- **BRANCH**: Unidades para desvios condicionais (padrão: 1)

### Latências (em ciclos, configurável via GUI)
- **ADD/SUB**: 2 ciclos
- **LOAD**: 6 ciclos
- **STORE**: 6 ciclos
- **MUL**: 3 ciclos
- **DIV**: 3 ciclos
- **BRANCH**: 4 ciclos

*Você pode modificar essas configurações diretamente na interface gráfica antes de configurar o simulador*

## 🎓 Conceitos Implementados

### Algoritmo de Tomasulo
- **Renomeação dinâmica de registradores** via Register Alias Table (RAT)
- **Execução fora de ordem** (Out-of-Order Execution)
- **Eliminação de hazards WAR e WAW** através de tags de Reservation Stations
- **Broadcast de resultados** via Common Data Bus (CDB)
- **Commit in-order** para preservar a semântica sequencial do programa

### Estações de Reserva (Reservation Stations)
- Armazenam instruções aguardando operandos
- Mantêm valores (Vj, Vk) ou tags de dependências (Qj, Qk)
- Executam operações assim que os operandos estão disponíveis
- Diferentes tipos: ADD/SUB, LOAD/STORE, MUL/DIV, BRANCH

### Register Alias Table (RAT)
- Mapeia cada registrador para a RS que produzirá seu próximo valor
- Elimina dependências falsas (WAR e WAW)
- Permite renomeação de registradores

### Especulação de Desvios
- Branches sempre são tomados nesta implementação
- Instruções após branches não resolvidos podem executar especulativamente
- Squashing (descarte) de instruções quando branch é resolvido
- Permite explorar paralelismo de instruções mesmo com branches

## 📚 Para Estudantes

### Experimentos Sugeridos

1. **Analise dependências**:
   ```assembly
   ADD R1 R2 R3
   MUL R4 R1 R5   # Depende de R1 (Qj aponta para RS_ADD)
   SUB R6 R4 R2   # Depende de R4 (Qj aponta para RS_MULT)
   ```
   Use **Próximo Ciclo** para ver como as instruções esperam (Qj/Qk) até os valores ficarem prontos

2. **Observe paralelismo**:
   ```assembly
   ADD R1 R2 R3
   MUL R4 R5 R6   # Independente! Executa em paralelo com ADD
   ```
   Veja que ambas executam simultaneamente nas suas respectivas RSs

3. **Teste hazards WAW**:
   ```assembly
   ADD R1 R2 R3
   SUB R1 R4 R5   # WAW hazard em R1 - resolvido pela RAT!
   MUL R6 R1 R7   # Pega o valor correto (de SUB, não ADD)
   ```
   A RAT garante que R6 receberá o valor da SUB

4. **Especulação de desvio**:
   ```assembly
   BEQ 5 R1 R2      # ID 0: Se R1 == R2, pula para instrução 5
   ADD R3 R4 R5     # ID 1: Executa especulativamente
   MUL R6 R3 R7     # ID 2: Também especulativa
   SUB R8 R9 R10    # ID 3
   DIV R1 R2 R3     # ID 4
   ADD R7 R8 R9     # ID 5: Alvo do branch
   ```
   Observe como as instruções 1-4 podem ser descartadas se o branch for tomado

## 🔍 Detalhes de Implementação

### Estágios do Pipeline

Cada ciclo executa os seguintes estágios em ordem:

1. **Commit**
   - Processa a primeira instrução não comitada (in-order)
   - Atualiza Register File com o resultado
   - Libera Reservation Station
   - Resolve branches e faz squashing se necessário

2. **Write Result**
   - Escreve resultado da RS que terminou no CDB
   - Faz broadcast para todas as RSs esperando (atualiza Vj/Vk)
   - Atualiza Register File se for o produtor atual
   - Uma única RS escreve por ciclo (simplificação)

3. **Execute**
   - Para cada RS ocupada:
     - Se operandos prontos (Qj == Qk == None), executa
     - Decrementa latência até chegar a zero
     - Marca ciclo de fim de execução

4. **Issue (Despacho)**
   - Pega próxima instrução do Program Counter
   - Verifica se há RS livre do tipo apropriado
   - Aloca RS e atribui instrução
   - Lê operandos ou registra dependências (Qj, Qk)
   - Atualiza Register Alias Table (produtor do registrador destino)
   - Incrementa PC

### Estrutura de Arquivos

```
Tomasulo-Algorithm-Simulator/
├── Instruction.py              # Classe Instruction e enum Op
├── ReservationStation.py       # Classe ReservationStation
├── RegisterFile.py             # Classes RegisterStatus e RegisterFile
├── TOMASSULLLERoriSimulator.py # Lógica principal do simulador
├── TOMASSULLLERoriGUI.py       # Interface gráfica (Tkinter)
├── README.md                   # Este arquivo
├── ARQUITETURA.md              # Documentação detalhada da arquitetura
└── exemplos_programas.md       # Exemplos de programas
```

### Estruturas de Dados Principais

**Instruction** (`Instruction.py:15-128`):
```python
- id: ID da instrução (baseado em zero)
- op: Operação (ADD, SUB, MUL, DIV, LD, ST, BEQ, BNE)
- dest, src1, src2: Registradores operandos
- issue_cycle, start_exec_cycle, end_exec_cycle: Tracking do pipeline
- write_result_cycle, commit_cycle: Mais tracking
- squashed: Se foi descartada por misprediction
- branch_target_id, branch_taken: Para branches
```

**ReservationStation** (`ReservationStation.py:1-93`):
```python
- name: Nome da estação (ex: "RS_ADD_1")
- busy: Está ocupada?
- op: Operação sendo executada
- Vj, Vk: Valores dos operandos
- Qj, Qk: Tags das RSs produzindo operandos (dependências)
- instruction: Referência para a instrução
- result: Resultado calculado
```

**RegisterFile** (`RegisterFile.py:19-42`):
```python
- registers: Dicionário de RegisterStatus
  - value: Valor atual do registrador
  - producer_tag: Nome da RS que produzirá o próximo valor (RAT)
```

## 🐛 Limitações e Simplificações

- **Predição de desvio**: Sempre assume que branches são tomados (simplificação)
- **Memória**: Simplificada, sem hierarquia de cache
- **CDB**: Apenas uma RS pode escrever por ciclo (CDB real pode ter múltiplos barramentos)
- **Exceções**: Não há tratamento de exceções (divisão por zero, overflow, etc.)
- **Instruções imediatas**: Valores imediatos devem ser passados como registradores

## 📁 Estrutura do Projeto

O projeto segue uma arquitetura modular orientada a objetos:

- **Instruction.py**: Define a classe de instruções e o enum de operações
- **ReservationStation.py**: Implementa as estações de reserva
- **RegisterFile.py**: Gerencia registradores e Register Alias Table
- **TOMASSULLLERoriSimulator.py**: Motor de simulação do algoritmo de Tomasulo
- **TOMASSULLLERoriGUI.py**: Interface gráfica usando Tkinter

Para mais detalhes sobre a arquitetura interna, consulte `ARQUITETURA.md`.

## 📝 Licença

Este projeto é de código aberto para fins educacionais.

## 👨‍💻 Desenvolvimento

Desenvolvido para o curso de Arquitetura de Computadores.

**Tecnologias**:
- Python 3
- Tkinter para GUI
- Paradigma orientado a objetos

---

**Divirta-se aprendendo sobre arquiteturas superescalares!** 🚀
