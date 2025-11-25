# 🚀 Guia Rápido - Simulador de Tomasulo

## Início Rápido em 3 Passos

### 1️⃣ Execute o Simulador
```bash
python tomasulo_simulator.py
```

### 2️⃣ A interface já vem com um programa exemplo!
Clique em **"Carregar Programa"**

### 3️⃣ Execute passo a passo
Clique em **"Step (1 Ciclo)"** várias vezes e observe:

- **Aba Instruções**: Veja o pipeline de cada instrução
- **Aba Reservation Stations**: Veja as unidades funcionais trabalhando
- **Aba ROB**: Veja o Buffer de Reordenamento em ação
- **Aba Registradores**: Veja a renomeação dinâmica (Qi)
- **Aba Métricas**: Veja o IPC e outras estatísticas

---

## 📊 O Que Observar em Cada Aba

### Instruções
```
Issue → Execute Start → Execute End → Write → Commit
```
- **Issue**: Instrução foi despachada (alocou RS e ROB)
- **Execute**: Está executando na unidade funcional
- **Write**: Resultado foi escrito no ROB (broadcast)
- **Commit**: Atualizou registrador/memória (in-order!)

### Reservation Stations
- **Busy = Sim**: Está ocupada executando
- **Qj/Qk**: Espera resultado de qual ROB?
- **Vj/Vk**: Valores dos operandos
- **Cycles**: Ciclos restantes de execução

### ROB (Reorder Buffer)
- **Verde**: HEAD (próxima a fazer commit)
- **Azul**: TAIL (última despachada)
- **Ready = Sim**: Resultado está pronto
- **Speculative = Sim**: Instrução após desvio

### Registradores
- **Qi = ROB#**: Registrador está esperando resultado do ROB
- **Qi = -**: Valor é válido (não está esperando)

---

## 🎯 Primeiro Experimento

Cole este código simples:

```assembly
ADD F0, F1, F2
MUL F3, F0, F4
```

Clique **"Carregar Programa"** e depois **"Step"** várias vezes:

**Ciclo 1**:
- ADD faz **Issue**
- ADD vai para **Add0** (Reservation Station)
- F1=2.0, F2=3.0 (valores iniciais)
- ROB0 é alocado

**Ciclo 2**:
- MUL faz **Issue**
- MUL vai para **Mul0**
- **Veja Qj = ROB0** (MUL espera ADD!)
- ROB1 é alocado

**Ciclos 3-4**:
- ADD executa (2 ciclos)

**Ciclo 5**:
- ADD faz **Write Result**
- **Broadcast!** Mul0 recebe o valor (Qj vira Vj)
- MUL começa a executar

**Ciclo 6**:
- ADD faz **Commit** (atualiza F0)

**Ciclos 7-16**:
- MUL executa (10 ciclos)

**Ciclo 17**:
- MUL faz **Write Result**

**Ciclo 18**:
- MUL faz **Commit**

---

## 💡 Conceitos Importantes

### 1. Renomeação de Registradores
```assembly
ADD F0, F1, F2    # F0 versão 1
MUL F0, F3, F4    # F0 versão 2
```
- ROB resolve automaticamente!
- Não há WAW hazard 👍

### 2. Paralelismo
```assembly
ADD F0, F1, F2    # Executa em paralelo
MUL F3, F4, F5    # com esta!
```
- Instruções independentes = IPC alto

### 3. Dependências
```assembly
ADD F0, F1, F2
MUL F3, F0, F4    # Espera ADD (veja Qj)
```
- Qj/Qk mostram dependências
- Broadcast resolve quando pronto

### 4. Especulação
```assembly
BEQ R1, R2, 5
ADD F0, F1, F2    # Especulativa!
```
- Executa, mas só faz commit após BEQ resolver

---

## 📈 Entendendo as Métricas

### IPC (Instructions Per Cycle)
- **IPC = 1.0**: Perfeito! 1 instrução por ciclo
- **IPC > 0.5**: Bom paralelismo
- **IPC < 0.3**: Muitos stalls

### Ciclos de Bolha
- **Poucos**: Programa bem paralelizado
- **Muitos**: Muitas dependências ou falta de recursos

### Como Melhorar IPC?
1. Reduza dependências de dados
2. Intercale instruções independentes
3. Use diferentes tipos de instrução (ADD + MUL)

---

## 🎓 Próximos Passos

1. ✅ Teste o programa exemplo incluído
2. 📖 Veja `exemplos_programas.md` para mais exemplos
3. 🧪 Crie seus próprios programas!
4. 📚 Leia o `README.md` completo

---

## ⚡ Atalhos Úteis

- **Carregar Programa**: Processa o código
- **Step**: Avança 1 ciclo (melhor para aprender!)
- **Executar Tudo**: Vai até o fim
- **Reset**: Recomeça

---

## 🤔 Dúvidas Comuns

**P: Por que a instrução não executou ainda?**
R: Verifique Qj e Qk na aba RS - ela está esperando algum resultado?

**P: O que significa ROB cheio?**
R: Há 16 entradas no ROB. Se todas ocupadas, novas instruções esperam.

**P: Por que IPC está baixo?**
R: Pode haver muitas dependências, ou latências longas (DIV = 40 ciclos!).

**P: Como vejo se há paralelismo?**
R: Na aba RS, veja quantas estações estão "Busy" ao mesmo tempo.

---

**Divirta-se explorando o Tomasulo! 🎉**
