# 📚 Exemplos de Programas - Simulador de Tomasulo

Este arquivo contém exemplos prontos para copiar e colar no simulador.

**Como usar:**
1. Configure o simulador (clique em "Configurar Simulador")
2. Copie o código do exemplo (sem comentários!)
3. Cole na área "Carregar Instruções"
4. Clique em "Iniciar"
5. Use "Próximo Ciclo" para ver passo a passo

---

## 📋 Índice de Exemplos

1. [Dependências RAW](#1-dependências-raw-read-after-write)
2. [Paralelismo Máximo](#2-paralelismo-máximo)
3. [WAR e WAW Hazards](#3-war-e-waw-hazards)
4. [Operações de Memória](#4-operações-de-memória)
5. [Branch com Especulação](#5-branch-com-especulação)
6. [Produto Escalar (Programa Completo)](#6-produto-escalar-programa-completo)
7. [Saturação de Recursos](#7-saturação-de-recursos)
8. [Latências Diferentes](#8-latências-diferentes)

---

## 1. Dependências RAW (Read After Write)

**O que demonstra:** Cadeia de dependências de dados (RAW hazards)

**Configuração sugerida:** Padrão (ADD/SUB=1, MUL/DIV=1)

**O que observar:**
- MUL espera ADD terminar (Qj aponta para RS_ADD)
- SUB espera MUL terminar (Qj aponta para RS_MULT)
- DIV espera SUB terminar
- Formação de cadeia de dependências sequencial
- IPC baixo (~0.20-0.30) devido às dependências

### Código para copiar:
```assembly
ADD F0 F1 F2
MUL F4 F0 F3
SUB F6 F4 F5
DIV F8 F6 F7
```

---

## 2. Paralelismo Máximo

**O que demonstra:** Instruções 100% independentes executando em paralelo

**Configuração sugerida:** ADD/SUB=3, MUL/DIV=3 (para ver paralelismo real)

**O que observar:**
- Todas as instruções são despachadas rapidamente
- Múltiplas RSs ocupadas simultaneamente
- Sem dependências entre instruções
- IPC melhor que exemplo anterior (~0.30-0.40)
- Poucas ou zero bolhas estruturais

### Código para copiar:
```assembly
ADD F0 F1 F2
MUL F4 F5 F6
SUB F8 F9 F10
ADD F12 F13 F14
MUL F16 F17 F18
SUB F20 F21 F22
```

---

## 3. WAR e WAW Hazards

**O que demonstra:** Hazards falsos resolvidos por renomeação de registradores

**Configuração sugerida:** Padrão

**O que observar:**
- F0 é escrito duas vezes (WAW entre ADD e MUL)
- SUB lê F0 versão 1 (do ADD)
- DIV lê F0 versão 2 (do MUL)
- ROB renomeia automaticamente, sem stalls!
- Na aba "Registradores", Qi aponta para ROB correto

### Código para copiar:
```assembly
ADD F0 F1 F2
SUB F3 F0 F4
MUL F0 F5 F6
DIV F7 F0 F8
```

---

## 4. Operações de Memória

**O que demonstra:** LOAD e STORE com dependências de dados

**Configuração sugerida:** Padrão (LOAD latência=6)

**O que observar:**
- LOADs usam Load Buffers (RS_STORE)
- STORE usa Store Buffer
- ADD espera AMBOS os LOADs terminarem (Qj e Qk apontam para RSs de LOAD)
- STORE espera ADD terminar
- Latência alta de LOAD (6 ciclos padrão) aumenta tempo total
- IPC muito baixo (~0.20) devido a dependências + latência alta

### Código para copiar:
```assembly
LD F0 R1 0
LD F2 R1 4
ADD F4 F0 F2
ST F4 R1 8
```

---

## 5. Branch com Especulação

**O que demonstra:** Execução especulativa após desvio condicional

**Configuração sugerida:** Padrão

**O que observar:**
- BEQ verifica se R1 == R2 e pula para instrução ID 4 se verdadeiro
- Instruções 1-3 (ADD, MUL, SUB) são especulativas
- Na aba "Status das Instruções", veja que podem executar antes do branch resolver
- Se branch for tomado, instruções 1-3 seriam descartadas (squashed)
- Simulador sempre toma branches (simplificação)

### Código para copiar:
```assembly
BEQ 4 R1 R2
ADD F0 F1 F2
MUL F3 F0 F4
SUB F5 F3 F6
DIV F7 F8 F9
```

---

## 6. Produto Escalar (Programa Completo)

**O que demonstra:** Programa realista calculando produto escalar de dois vetores

**Fórmula:** result = A[0]×B[0] + A[1]×B[1] + A[2]×B[2]

**Configuração sugerida:** LOAD/STORE=2, MUL/DIV=2, ADD/SUB=2

**O que observar:**
- 6 LOADs: podem executar em paralelo (2 por vez se tiver 2 Load Buffers)
- 3 MULs: aguardam LOADs, depois executam em paralelo
- 2 ADDs: formam cadeia de dependência (segundo ADD depende do primeiro)
- STORE: aguarda todas as operações terminarem
- Bom mix de paralelismo e dependências
- IPC moderado (~0.35-0.45)

### Código para copiar:
```assembly
LD F0 R1 0
LD F1 R1 4
LD F2 R1 8
LD F3 R2 0
LD F4 R2 4
LD F5 R2 8
MUL F6 F0 F3
MUL F7 F1 F4
MUL F8 F2 F5
ADD F9 F6 F7
ADD F10 F9 F8
ST F10 R3 0
```

---

## 7. Saturação de Recursos

**O que demonstra:** Como falta de RSs causa bolhas estruturais

**Configuração para ver bolhas:** ADD/SUB=1, MUL/DIV=1 (apenas 1 de cada!)

**Configuração sem bolhas:** ADD/SUB=5, MUL/DIV=5

**O que observar:**
- Com 1 RS: apenas 1 ADD pode fazer issue por vez
- 10 ADDs seguidos saturam a única ADD RS
- Instruções ficam esperando = bolhas estruturais (contador de bolhas aumenta)
- Com 5 RSs: sem bolhas! Todas fazem issue rápido
- Compare os dois cenários!

### Código para copiar:
```assembly
ADD F0 R1 R2
ADD F3 R4 R5
ADD F6 R7 R8
ADD F9 R10 R11
ADD F12 R13 R14
ADD F15 R16 R17
ADD F18 R19 R20
ADD F21 R22 R23
ADD F24 R25 R26
ADD F27 R28 R29
```

---

## 8. Latências Diferentes

**O que demonstra:** Como diferentes latências afetam o tempo de execução

**Configuração sugerida:**
- ADD latência=2
- MUL latência=10
- DIV latência=40 (!)

**O que observar:**
- ADDs terminam rápido (2 ciclos)
- MUL demora 10 ciclos executando
- DIV demora 40 ciclos! (muito lenta)
- Na aba "Reservation Stations", veja a coluna "Cycles" diminuindo
- Tempo total dominado pela operação mais lenta (DIV)
- IPC baixo se houver dependências da DIV

### Código para copiar:
```assembly
ADD F0 F1 F2
MUL F3 F4 F5
ADD F6 F7 F8
DIV F9 F10 F11
ADD F12 F13 F14
```

---

## 🎯 Dicas para Demonstrações

### Para mostrar **paralelismo**:
- Use Exemplo 2 ou 6
- Configure múltiplas RSs (3-5 de cada)
- Observe múltiplas RSs ocupadas simultaneamente

### Para mostrar **dependências**:
- Use Exemplo 1 ou 4
- Execute passo a passo com "Próximo Ciclo"
- Observe Qj/Qk apontando para RSs produtoras

### Para mostrar **renomeação de registradores**:
- Use Exemplo 3
- Observe a aba "Registradores" - Qi muda quando há múltiplas escritas em F0
- Compare com a aba "ROB" para ver versões diferentes

### Para mostrar **bolhas estruturais**:
- Use Exemplo 7
- Configure apenas 1 RS de cada tipo
- Observe contador de bolhas aumentando
- Compare com 5 RSs (zero bolhas!)

### Para mostrar **impacto de latências**:
- Use Exemplo 8
- Configure DIV=40, MUL=10
- Veja quanto tempo a DIV domina a execução

---

## 📊 Tabela de Comparação de IPCs Esperados

| Exemplo | IPC Típico | Motivo |
|---------|-----------|--------|
| 1. Dependências RAW | 0.20-0.30 | Cadeia sequencial |
| 2. Paralelismo | 0.35-0.45 | Instruções independentes |
| 3. WAR/WAW | 0.25-0.35 | Algumas dependências |
| 4. Memória | 0.15-0.25 | LOAD latência alta |
| 5. Branch | 0.20-0.30 | Dependências + branch |
| 6. Produto Escalar | 0.35-0.45 | Mix balanceado |
| 7. Saturação (1 RS) | 0.15-0.25 | Muitas bolhas |
| 7. Saturação (5 RS) | 0.40-0.50 | Sem bolhas |
| 8. Latências | 0.10-0.20 | DIV muito lenta |

**Nota:** IPCs são estimativas. Valores reais dependem das configurações de RSs e latências.

---

## 🎓 Para Apresentações

### Ordem sugerida de demonstração:

1. **Exemplo 2** - Mostre que o Tomasulo funciona (paralelismo básico)
2. **Exemplo 1** - Mostre como resolve dependências automaticamente
3. **Exemplo 3** - Mostre renomeação de registradores (WAW/WAR)
4. **Exemplo 7** - Compare 1 RS vs 5 RS (impacto de recursos)
5. **Exemplo 6** - Programa completo realista

### Roteiro de apresentação (5 minutos):

1. **Minuto 1:** Execute Exemplo 2 - "Vejam múltiplas instruções executando em paralelo!"
2. **Minuto 2:** Execute Exemplo 1 passo a passo - "Vejam as dependências sendo resolvidas"
3. **Minuto 3:** Execute Exemplo 3 - "Renomeação automática resolve WAW sem stalls"
4. **Minuto 4:** Execute Exemplo 7 com 1 RS e depois 5 RS - "Mais recursos = menos bolhas"
5. **Minuto 5:** Execute Exemplo 6 - "Programa completo mostrando tudo junto"

---

**Divirta-se explorando o algoritmo de Tomasulo!** 🚀
