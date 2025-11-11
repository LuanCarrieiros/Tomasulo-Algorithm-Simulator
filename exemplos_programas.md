# Exemplos de Programas para o Simulador de Tomasulo

## Exemplo 1: Dependências RAW (Read After Write)

```assembly
# Demonstra dependências de dados
ADD F0, F1, F2    # F0 = F1 + F2
MUL F4, F0, F3    # Depende de F0 (RAW hazard)
SUB F6, F4, F5    # Depende de F4 (RAW hazard)
DIV F8, F6, F7    # Depende de F6 (RAW hazard)
```

**O que observar:**
- MUL espera ADD completar (veja Qj apontando para ROB0)
- SUB espera MUL completar
- Formação de uma cadeia de dependências

---

## Exemplo 2: Paralelismo de Instruções

```assembly
# Instruções independentes executam em paralelo
ADD F0, F1, F2    # Independente
MUL F4, F5, F6    # Independente - executa em paralelo!
SUB F8, F9, F10   # Independente - executa em paralelo!
ADD F12, F13, F14 # Independente - executa em paralelo!
```

**O que observar:**
- Todas as instruções são despachadas rapidamente
- Múltiplas RSs ocupadas simultaneamente
- IPC próximo de 1.0 (bom paralelismo)
- Poucas bolhas

---

## Exemplo 3: WAR e WAW Hazards (Resolvidos pelo ROB!)

```assembly
# Hazards falsos resolvidos por renomeação
ADD F0, F1, F2    # F0 (versão 1)
SUB F3, F0, F4    # Lê F0 (versão 1)
MUL F0, F5, F6    # F0 (versão 2) - WAW com instrução 1
DIV F7, F0, F8    # Lê F0 (versão 2) - WAR com instrução 2
```

**O que observar:**
- Não há stalls por WAR ou WAW
- ROB renomeia F0 automaticamente
- SUB pega F0 de ROB0, DIV pega F0 de ROB2
- Qi dos registradores aponta para ROB correto

---

## Exemplo 4: Operações de Memória

```assembly
# LOAD e STORE
LOAD F0, 0(R1)     # F0 = Mem[R1 + 0]
LOAD F2, 4(R1)     # F2 = Mem[R1 + 4]
ADD F4, F0, F2     # Depende dos LOADs
STORE F4, 8(R1)    # Mem[R1 + 8] = F4
```

**O que observar:**
- LOADs usam Load Buffers
- STORE usa Store Buffer
- ADD espera LOADs completarem (Qj e Qk)

---

## Exemplo 5: Desvios Condicionais (Especulação)

```assembly
# Especulação de desvios
BEQ R1, R2, 3      # Se R1 == R2, pula 3 instruções
ADD F0, F1, F2     # Instrução especulativa
MUL F3, F0, F4     # Instrução especulativa
SUB F5, F3, F6     # Instrução especulativa
DIV F7, F8, F9     # Instrução após o desvio
```

**O que observar:**
- Na aba ROB, veja a coluna "Speculative" = Sim
- Instruções especulativas são executadas, mas só fazem commit após BEQ resolver
- Se desvio for tomado, instruções especulativas seriam descartadas

---

## Exemplo 6: Saturação de Recursos

```assembly
# Satura as Reservation Stations
ADD F0, F1, F2
ADD F3, F4, F5
ADD F6, F7, F8
ADD F9, F10, F11   # Tem que esperar! Só há 3 Add RS
MUL F12, F13, F14
MUL F15, F16, F17
MUL F18, F19, F20  # Tem que esperar! Só há 2 Mul RS
```

**O que observar:**
- 4ª instrução ADD não consegue issue (sem RS livre)
- Ciclos de bolha aumentam
- IPC diminui devido à contenção de recursos

---

## Exemplo 7: Loop com Desvio

```assembly
# Simula um pequeno loop
ADDI R1, R0, 0     # R1 = 0 (contador)
ADDI R2, R0, 5     # R2 = 5 (limite)
ADD F0, F1, F2     # Corpo do loop
ADDI R1, R1, 1     # R1++
BEQ R1, R2, -2     # Se R1 == R2, encerra (else volta 2 instruções)
```

**O que observar:**
- Desvio condicional ao final
- Especulação após BEQ

---

## Exemplo 8: Instruções com Imediato

```assembly
# Uso de valores imediatos
ADDI R1, R0, 100   # R1 = 0 + 100
SUBI R2, R1, 50    # R2 = R1 - 50
ADDI F0, F1, 10    # F0 = F1 + 10
```

**O que observar:**
- Vk recebe o valor imediato diretamente
- Qk fica como '-' (não há dependência)

---

## Exemplo 9: Latências Diferentes

```assembly
# Demonstra diferentes latências
ADD F0, F1, F2     # 2 ciclos
MUL F3, F4, F5     # 10 ciclos (mais lenta)
ADD F6, F7, F8     # 2 ciclos
DIV F9, F10, F11   # 40 ciclos (muito lenta!)
ADD F12, F13, F14  # 2 ciclos
```

**O que observar:**
- ADDs completam rápido
- MUL demora 10 ciclos
- DIV demora 40 ciclos
- Veja "Cycles" na aba RS diminuindo

---

## Exemplo 10: Programa Completo - Produto Escalar

```assembly
# Calcula produto escalar: result = (A[0]*B[0]) + (A[1]*B[1]) + (A[2]*B[2])

# Carrega elementos do vetor A
LOAD F0, 0(R1)     # F0 = A[0]
LOAD F1, 4(R1)     # F1 = A[1]
LOAD F2, 8(R1)     # F2 = A[2]

# Carrega elementos do vetor B
LOAD F3, 0(R2)     # F3 = B[0]
LOAD F4, 4(R2)     # F4 = B[1]
LOAD F5, 8(R2)     # F5 = B[2]

# Multiplica elementos correspondentes
MUL F6, F0, F3     # F6 = A[0] * B[0]
MUL F7, F1, F4     # F7 = A[1] * B[1]
MUL F8, F2, F5     # F8 = A[2] * B[2]

# Soma os produtos
ADD F9, F6, F7     # F9 = F6 + F7
ADD F10, F9, F8    # F10 = F9 + F8 (resultado final)

# Armazena resultado
STORE F10, 0(R3)   # Mem[R3] = resultado
```

**O que observar:**
- 6 LOADs podem executar em paralelo (2 por vez)
- 3 MULs podem executar em paralelo (2 por vez)
- ADDs formam cadeia de dependência
- Observe o alto IPC devido ao paralelismo

---

## Exemplo 11: Teste de ROB Cheio

```assembly
# Muitas instruções longas para encher o ROB
MUL F0, F1, F2
MUL F3, F4, F5
MUL F6, F7, F8
MUL F9, F10, F11
MUL F12, F13, F14
DIV F15, F16, F17
DIV F18, F19, F20
DIV F21, F22, F23
DIV F24, F25, F26
DIV F27, F28, F29
ADD F30, F31, F0
ADD F1, F2, F3
ADD F4, F5, F6
ADD F7, F8, F9
ADD F10, F11, F12
ADD F13, F14, F15
```

**O que observar:**
- ROB (16 entradas) pode encher
- Issue pode parar por falta de ROB
- Ciclos de bolha aumentam
- Commits liberam espaço no ROB

---

## Como Usar estes Exemplos

1. Copie o código do exemplo
2. Cole na área "Programa MIPS" do simulador
3. Clique em "Carregar Programa"
4. Use "Step (1 Ciclo)" para ver passo a passo
5. Ou use "Executar Tudo" para ver o resultado final

## Sugestões de Análise

Para cada exemplo, observe:

### Na aba "Instruções":
- Quando cada instrução foi despachada (Issue)
- Quando começou/terminou execução
- Quando fez Write Result e Commit

### Na aba "Reservation Stations":
- Quantas RSs estão ocupadas simultaneamente
- Dependências (Qj, Qk apontam para ROB)
- Ciclos restantes de cada operação

### Na aba "ROB":
- HEAD (próxima a fazer commit)
- TAIL (última despachada)
- Quais estão prontas (Ready = Sim)
- Quais são especulativas

### Na aba "Registradores":
- Qi mostra renomeação (aponta para ROB)
- Valores só atualizam após commit

### Na aba "Métricas":
- **IPC alto** = bom paralelismo
- **Muitas bolhas** = muitos stalls (ruim)
- Compare diferentes programas!

---

**Experimente modificar os exemplos e criar seus próprios programas!** 🎓
