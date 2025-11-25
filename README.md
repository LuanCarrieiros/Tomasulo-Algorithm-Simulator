# Simulador do Algoritmo de Tomasulo - Web Interface

Simulador didático web do **Algoritmo de Tomasulo** com suporte a:
- ✅ Estações de Reserva (Reservation Stations)
- ✅ Execução fora de ordem (Out-of-Order Execution)
- ✅ Especulação de desvios condicionais
- ✅ Interface web moderna e responsiva
- ✅ Visualização em tempo real do pipeline
- ✅ Execução passo a passo e automática
- ✅ Métricas dinâmicas de desempenho (IPC, ciclos, bolhas, etc.)

## 👥 Equipe de Desenvolvimento

- Arthur Clemente Machado
- Arthur Gonçalves de Moraes
- Bernardo Ferreira Temponi
- Diego Moreira Rocha
- Luan Barbosa Rosa Carrieiros

## 📋 Requisitos

- Python 3.10 ou superior
- Django 5.2.6
- Navegador web moderno (Chrome, Firefox, Edge, Safari)

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar o Servidor

```bash
python manage.py runserver
```

### 3. Acessar a Interface

Abra seu navegador e acesse:
```
http://127.0.0.1:8000/
```

## 📖 Como Usar

### 1. Configurar o Simulador

Na coluna esquerda, configure:

#### **Unidades Funcionais**
Quantidade de cada tipo de estação de reserva:
- **ADD/SUB**: Unidades para adição e subtração (padrão: 3)
- **MULT/DIV**: Unidades para multiplicação e divisão (padrão: 2)
- **STORE**: Buffers para operações de memória (padrão: 2)
- **BRANCH**: Unidades para desvios condicionais (padrão: 1)

#### **Latências (em ciclos)**
Número de ciclos para cada tipo de operação:
- **ADD/SUB**: Latência de adição/subtração (padrão: 2 ciclos)
- **MUL**: Latência de multiplicação (padrão: 10 ciclos)
- **DIV**: Latência de divisão (padrão: 40 ciclos)
- **LOAD**: Latência de leitura de memória (padrão: 2 ciclos)
- **STORE**: Latência de escrita em memória (padrão: 2 ciclos)
- **BRANCH**: Latência de desvio (padrão: 1 ciclo)

### 2. Escrever o Programa

- Digite ou cole suas instruções na área de texto **📝 Programa**
- Formato: `OP DEST SRC1 SRC2`
- Exemplo: `ADD R1 R2 R3`
- Linhas começando com `#` são comentários e serão ignoradas
- Use o dropdown **"Exemplos..."** para carregar programas predefinidos

### 3. Executar Simulação

Clique em **▶ Iniciar** para rodar a simulação. A interface processará todas as instruções e preparará a visualização ciclo a ciclo.

### 4. Navegar pelos Ciclos

Após a simulação, use os controles disponíveis:

- **⏮ Anterior**: Volta um ciclo
- **Próximo ⏭**: Avança um ciclo
- **⏯ Auto Executar**: Executa automaticamente com velocidade ajustável
- **⏸ Pausar**: Pausa a execução automática
- **⏩ Executar Tudo**: Pula para o último ciclo
- **Slider de ciclos**: Navegue diretamente para qualquer ciclo
- **Controle de velocidade**: Ajuste a velocidade da auto-execução (100ms - 2000ms)

### 5. Visualizações Disponíveis

#### 🎮 Métricas em Tempo Real
Valores que **mudam dinamicamente** conforme você navega pelos ciclos:
- **IPC**: Instructions Per Cycle no ciclo atual
- **Ciclo Atual**: Número do ciclo sendo visualizado
- **Bolhas**: Ciclos desperdiçados acumulados até o momento
- **Especulativas**: Número de instruções especulativas no ciclo atual
- **Descartadas**: Total de instruções descartadas até o momento

#### 📋 Status das Instruções
Tabela mostrando o pipeline completo de cada instrução:
- **ID**: Identificador da instrução
- **OP**: Operação (ADD, SUB, MUL, DIV, LD, ST, BEQ, BNE)
- **Dest, Src1, Src2**: Operandos
- **Issue**: Ciclo de despacho
- **Exec Start**: Início da execução
- **Exec End**: Fim da execução
- **Write**: Escrita do resultado no CDB
- **Commit**: Commit final (in-order)
- **Estado**: Status visual com cores:
  - 🟦 **Aguardando**: Ainda não foi despachada
  - 🟨 **Issued**: Despachada, aguardando operandos
  - 🟦 **Executando**: Em execução
  - 🟩 **Write**: Resultado escrito no CDB
  - 🟩 **Committed**: Comitada com sucesso
  - 🟧 **ESPECULATIVA**: Executando especulativamente
  - 🟥 **DESCARTADA**: Descartada por branch misprediction

#### 🔧 Estações de Reserva
Visualiza o estado de todas as Reservation Stations:
- **Nome**: Identificação da estação (ADD_0, MULT_1, etc.)
- **Op**: Operação sendo executada
- **Vj, Vk**: Valores dos operandos
- **Qj, Qk**: Tags das estações produzindo operandos (dependências)
- **Cores**: 🟥 Ocupada | 🟩 Livre

#### 📝 Register File
Mostra o estado dos registradores em tempo real:
- **Reg**: Nome do registrador (R0-R10)
- **Valor**: Valor atual calculado
- **Produtor**: Tag da RS que produzirá o próximo valor (Register Alias Table)

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

### Valores Imediatos
Você pode usar valores numéricos diretamente:
```assembly
ADD R2 R0 20      # R2 = R0 + 20 = 0 + 20 = 20
MUL R3 R2 5       # R3 = R2 * 5 = 20 * 5 = 100
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
**Nota**: Para branches, o primeiro operando é o ID da instrução alvo (baseado em zero)

### Comentários
```assembly
# Isto é um comentário
ADD R1 R2 R3  # Comentário inline também funciona
```

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
- Diferentes tipos: ADD/SUB, MULT/DIV, STORE, BRANCH

### Register Alias Table (RAT)
- Mapeia cada registrador para a RS que produzirá seu próximo valor
- Elimina dependências falsas (WAR e WAW)
- Permite renomeação de registradores

### Especulação de Desvios
- Branches sempre são tomados nesta implementação
- Instruções após branches não resolvidos podem executar especulativamente
- Squashing (descarte) de instruções quando branch é resolvido incorretamente
- Permite explorar paralelismo de instruções mesmo com branches

## 📚 Experimentos Sugeridos

### 1. Analise Dependências
```assembly
ADD R1 R2 R3
MUL R4 R1 R5   # Depende de R1 (Qj aponta para RS_ADD)
SUB R6 R4 R2   # Depende de R4 (Qj aponta para RS_MULT)
```
Use navegação passo a passo para ver como as instruções esperam (Qj/Qk) até os valores ficarem prontos.

### 2. Observe Paralelismo
```assembly
ADD R1 R2 R3
MUL R4 R5 R6   # Independente! Executa em paralelo com ADD
```
Veja que ambas executam simultaneamente nas suas respectivas RSs.

### 3. Teste Hazards WAW
```assembly
ADD R1 R2 R3
SUB R1 R4 R5   # WAW hazard em R1 - resolvido pela RAT!
MUL R6 R1 R7   # Pega o valor correto (de SUB, não ADD)
```
A RAT garante que R6 receberá o valor da SUB.

### 4. Especulação de Desvio
```assembly
BEQ 5 R1 R2      # ID 0: Se R1 == R2, pula para instrução 5
ADD R3 R4 R5     # ID 1: Executa especulativamente
MUL R6 R3 R7     # ID 2: Também especulativa
SUB R8 R9 R10    # ID 3
DIV R1 R2 R3     # ID 4
ADD R7 R8 R9     # ID 5: Alvo do branch
```
Observe como as instruções 1-4 podem ser descartadas se o branch for tomado.

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

## 📁 Estrutura do Projeto

```
Tomasulo-Algorithm-Simulator/
├── 🌐 WEB VERSION (Django)
│   ├── manage.py                    # Django management script
│   ├── requirements.txt             # Dependências Python
│   ├── db.sqlite3                   # Banco de dados SQLite
│   ├── README.md                    # Este arquivo
│   │
│   ├── tomasulo_web/                # Configurações Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── simulator/                   # App Django
│   │   ├── views.py                 # Endpoints da API
│   │   ├── urls.py
│   │   ├── models.py
│   │   └── templates/
│   │       └── simulator/
│   │           └── index.html       # Interface web
│   │
│   ├── static/                      # Arquivos estáticos
│   │
│   └── 🔧 CORE (Motor do Simulador)
│       ├── Instruction.py           # Classe Instruction e enum Op
│       ├── ReservationStation.py    # Classe ReservationStation
│       ├── RegisterFile.py          # Classes RegisterStatus e RegisterFile
│       └── TOMASSULLLERoriSimulator.py  # Lógica principal do simulador
│
└── 🖥️ desktop_version/              # Versão desktop antiga (Tkinter)
    ├── TOMASSULLLERoriGUI.py
    ├── README_DESKTOP.md
    ├── ARQUITETURA.md
    ├── GUIA_RAPIDO.md
    └── exemplos_programas.md
```

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.14**: Linguagem principal
- **Django 5.2.6**: Framework web
- **Django REST Framework 3.15.2**: API REST
- **Django CORS Headers 4.3.1**: Suporte a CORS

### Frontend
- **HTML5**: Estrutura
- **Tailwind CSS 3.x**: Estilização responsiva
- **Alpine.js 3.x**: Reatividade e interatividade
- **JavaScript ES6+**: Lógica da interface

### Servidor
- **WhiteNoise 6.6.0**: Servir arquivos estáticos
- **SQLite 3**: Banco de dados (sessões)

## 🐛 Limitações e Simplificações

- **Predição de desvio**: Sempre assume que branches são tomados (simplificação didática)
- **Memória**: Simplificada, sem hierarquia de cache
- **CDB**: Apenas uma RS pode escrever por ciclo (CDB real pode ter múltiplos barramentos)
- **Exceções**: Não há tratamento de exceções (divisão por zero, overflow, etc.)

## 📝 Licença

Este projeto é de código aberto para fins educacionais.

## 👨‍💻 Desenvolvimento

Desenvolvido para a matéria de **Arquitetura de Computadores III**.

**Paradigma**: Orientado a objetos com arquitetura MVC (Django)

---

## 🔗 Links Úteis

- **Versão Desktop**: Veja a pasta `desktop_version/` para a versão original com interface Tkinter
- **Documentação Detalhada**: Consulte `desktop_version/ARQUITETURA.md` para detalhes internos da implementação
- **Guia Rápido**: `desktop_version/GUIA_RAPIDO.md`
- **Exemplos de Programas**: `desktop_version/exemplos_programas.md`

---

**🎓 Projeto acadêmico - 2025**
