# Simulador do Algoritmo de Tomasulo

Simulador didático do **Algoritmo de Tomasulo** com suporte a:
- ✅ Buffer de Reordenamento (ROB - Reorder Buffer)
- ✅ Especulação de desvios condicionais
- ✅ Execução passo a passo
- ✅ Interface gráfica intuitiva
- ✅ Métricas de desempenho (IPC, ciclos, bolhas, etc.)

## 📋 Requisitos

- Python 3.7 ou superior
- Tkinter (geralmente já vem com Python)

## 🚀 Como Executar

```bash
python tomasulo_simulator.py
```

## 📖 Como Usar

### 1. Carregar Programa
- O simulador já vem com um programa exemplo carregado
- Você pode editar diretamente na área "Programa MIPS"
- Clique em **"Carregar Programa"** para processar as instruções

### 2. Executar Simulação

Três modos de execução:

- **Step (1 Ciclo)**: Executa um ciclo de clock por vez (ideal para aprendizado)
- **Executar Tudo**: Executa até o final automaticamente
- **Reset**: Reinicia a simulação mantendo o código

### 3. Visualizações Disponíveis

#### 📊 Aba "Instruções"
Mostra o pipeline de cada instrução com os ciclos de:
- **Issue**: Quando foi despachada
- **Exec Start**: Início da execução
- **Exec End**: Fim da execução
- **Write**: Escrita do resultado
- **Commit**: Commit final
- **ROB**: Entrada do ROB alocada

#### 🔧 Aba "Reservation Stations"
Visualiza o estado de todas as Reservation Stations:
- Add/Sub Stations (3 unidades)
- Mul/Div Stations (2 unidades)
- Load Buffers (2 unidades)
- Store Buffers (2 unidades)

Mostra:
- Se está ocupada
- Operação sendo executada
- Valores dos operandos (Vj, Vk)
- Dependências (Qj, Qk apontam para ROB)
- Ciclos restantes

#### 📦 Aba "Reorder Buffer (ROB)"
Visualiza as 16 entradas do ROB:
- Cor **verde**: HEAD (próxima a fazer commit)
- Cor **azul**: TAIL (última alocada)
- Mostra se a instrução está pronta (Ready)
- Indica se é especulativa (após desvio)

#### 📝 Aba "Registradores"
Mostra o estado dos registradores:
- **R0-R9**: Registradores inteiros
- **F0-F12**: Registradores de ponto flutuante
- **Qi**: Indica qual entrada do ROB vai produzir o valor (Register Alias Table)

#### 📈 Aba "Métricas"
Apresenta estatísticas de desempenho:
- **Total de Ciclos**: Ciclos gastos na execução
- **Instruções Completadas**: Quantidade de commits
- **IPC**: Instructions Per Cycle (quanto maior, melhor!)
- **Ciclos de Bolha**: Ciclos desperdiçados por stalls
- **Branch Mispredictions**: Erros de predição de desvio

## 💡 Instruções MIPS Suportadas

### Aritméticas
```assembly
ADD  R1, R2, R3      # R1 = R2 + R3
ADDI R1, R2, 10      # R1 = R2 + 10 (imediato)
SUB  R1, R2, R3      # R1 = R2 - R3
SUBI R1, R2, 5       # R1 = R2 - 5
MUL  F0, F1, F2      # F0 = F1 * F2
DIV  F0, F1, F2      # F0 = F1 / F2
```

### Memória
```assembly
LOAD  F1, 0(R2)      # F1 = Mem[R2 + 0]
L.D   F1, 4(R2)      # Mesmo que LOAD
STORE F1, 0(R2)      # Mem[R2 + 0] = F1
S.D   F1, 8(R2)      # Mesmo que STORE
```

### Desvios Condicionais
```assembly
BEQ R1, R2, 4        # Se R1 == R2, pula 4 instruções
BNE R1, R2, 2        # Se R1 != R2, pula 2 instruções
```

### Comentários
```assembly
# Isto é um comentário
ADD R1, R2, R3  # Comentário inline
```

## ⚙️ Configurações do Simulador

### Unidades Funcionais
- **3** Reservation Stations Add/Sub
- **2** Reservation Stations Mul/Div
- **2** Load Buffers
- **2** Store Buffers
- **16** Entradas no ROB

### Latências (em ciclos)
- **ADD/SUB**: 2 ciclos
- **MUL**: 10 ciclos
- **DIV**: 40 ciclos
- **LOAD**: 3 ciclos
- **STORE**: 3 ciclos
- **BEQ/BNE**: 1 ciclo

*Você pode modificar essas configurações editando o código em `tomasulo_simulator.py`*

## 🎓 Conceitos Implementados

### Algoritmo de Tomasulo
- **Renomeação dinâmica de registradores** via ROB
- **Execução fora de ordem** (Out-of-Order Execution)
- **Eliminação de hazards WAR e WAW**
- **Broadcast de resultados** via Common Data Bus

### Reorder Buffer (ROB)
- **Commit in-order** preservando semântica do programa
- **Suporte a exceções precisas**
- **Especulação segura**

### Especulação de Desvios
- Instruções após desvios são marcadas como especulativas
- Commit só ocorre após resolução do desvio
- Permite explorar paralelismo mesmo com branches

## 📚 Para Estudantes

### Experimentos Sugeridos

1. **Analise dependências**:
   ```assembly
   ADD F0, F1, F2
   MUL F4, F0, F3   # Depende de F0
   SUB F6, F4, F5   # Depende de F4
   ```
   Use **Step** para ver como as instruções esperam (Qj/Qk)

2. **Observe paralelismo**:
   ```assembly
   ADD F0, F1, F2
   MUL F4, F5, F6   # Independente! Executa em paralelo
   ```
   Veja que ambas executam simultaneamente

3. **Teste hazards**:
   ```assembly
   ADD F0, F1, F2
   SUB F0, F3, F4   # WAW hazard - resolvido pelo ROB!
   MUL F5, F0, F6   # Pega o valor correto
   ```

4. **Especulação de desvio**:
   ```assembly
   BEQ R1, R2, 3
   ADD F0, F1, F2   # Especulativa
   MUL F3, F0, F4   # Especulativa
   ```

## 🔍 Detalhes de Implementação

### Estágios do Pipeline

1. **Issue (Despacho)**
   - Aloca Reservation Station
   - Aloca entrada do ROB
   - Lê operandos ou registra dependências (Qj, Qk)
   - Atualiza Register Alias Table (Qi)

2. **Execute**
   - Aguarda operandos (Qj == Qk == None)
   - Executa operação
   - Decrementa contador de ciclos

3. **Write Result**
   - Escreve resultado no ROB
   - Faz broadcast para RSs esperando
   - Libera RS

4. **Commit**
   - Processa entradas do ROB em ordem (HEAD)
   - Atualiza registrador/memória
   - Resolve especulação
   - Avança HEAD

### Estruturas de Dados

```python
# Reservation Station
- name: Nome da estação
- busy: Está ocupada?
- op: Operação
- vj, vk: Valores dos operandos
- qj, qk: ROB entries produzindo operandos
- rob_entry: Entrada do ROB associada
- cycles_remaining: Ciclos até terminar

# ROB Entry
- entry_num: Número da entrada (0-15)
- busy: Está ocupada?
- instruction_type: Tipo da instrução
- destination: Registrador destino
- value: Resultado calculado
- ready: Resultado está pronto?
- speculative: É especulativa?

# Register Alias Table (RAT)
- values[reg]: Valor atual do registrador
- qi[reg]: ROB entry que vai produzir próximo valor
```

## 🐛 Limitações Conhecidas

- Predição de desvio é sempre "not taken" (executa sequencialmente)
- Memória é simplificada (não há cache)
- Não implementa exceções
- Não há suporte para instruções de ponto flutuante complexas

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
