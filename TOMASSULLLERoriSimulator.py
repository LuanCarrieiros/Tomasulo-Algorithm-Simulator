from Instruction import Instruction, Op
from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
import copy


class TOMASSULLLERoriSimulator:
    def __init__(self, add_fu_count, store_fu_count, mult_fu_count, branch_fu_count,
                 add_sub_latency, load_latency, store_latency, mult_latency, div_latency, branch_latency):
        self.add_sub_latency = add_sub_latency
        self.load_latency = load_latency
        self.store_latency = store_latency
        self.mult_latency = mult_latency
        self.div_latency = div_latency
        self.branch_latency = branch_latency

        self.register_file = RegisterFile()

        self.rs_add = [ReservationStation(f"RS_ADD_{i + 1}") for i in range(add_fu_count)]
        self.rs_store = [ReservationStation(f"RS_STORE_{i + 1}") for i in range(store_fu_count)]
        self.rs_mult = [ReservationStation(f"RS_MULT_{i + 1}") for i in range(mult_fu_count)]
        self.rs_branch = [ReservationStation(f"RS_BRANCH_{i + 1}") for i in range(branch_fu_count)]

        self.all_instructions = []
        self.cdb_producer_tag = None
        self.cdb_value = None

        self.bubble_cycles = 0
        self.current_clock = 0
        self.program_counter = 0  # Índice da próxima instrução a ser emitida

        # Contadores permanentes de métricas (nunca resetam durante a simulação)
        self.total_squashed_count = 0
        self.max_speculative_count = 0

        # Histórico de estados para Step Back
        self.state_history = []

        self.reset_simulation_state()  # Garante um estado limpo

    def set_instructions(self, instructions):
        """Método para a GUI carregar as instruções"""
        self.all_instructions = instructions
        self.reset_simulation_state()  # Reseta o estado quando novas instruções são carregadas

    def reset_simulation_state(self):
        self.current_clock = 0
        self.bubble_cycles = 0
        self.program_counter = 0
        self.cdb_producer_tag = None
        self.cdb_value = None
        self.state_history = []  # Limpa o histórico
        self.total_squashed_count = 0  # Reseta contador de descartadas
        self.max_speculative_count = 0  # Reseta contador de especulativas

        # Limpa todas as RSs
        for rs in self.rs_add:
            rs.free()
        for rs in self.rs_store:
            rs.free()
        for rs in self.rs_mult:
            rs.free()
        for rs in self.rs_branch:
            rs.free()

        # Reseta o Register File
        self.register_file = RegisterFile()

        # Reseta o estado das instruções
        for instr in self.all_instructions:
            instr.set_issue_cycle(-1)
            instr.set_start_exec_cycle(-1)
            instr.set_end_exec_cycle(-1)
            instr.set_write_result_cycle(-1)
            instr.set_commit_cycle(-1)
            instr.set_current_latency(instr.get_original_latency())
            instr.set_branch_taken(False)
            instr.set_branch_resolved(False)
            instr.set_squashed(False)
            instr.clear_speculative()  # Limpa flag de especulação

    def save_state(self):
        """Salva o estado atual para permitir Step Back"""
        state = {
            'current_clock': self.current_clock,
            'bubble_cycles': self.bubble_cycles,
            'program_counter': self.program_counter,
            'cdb_producer_tag': self.cdb_producer_tag,
            'cdb_value': self.cdb_value,
            'instructions': copy.deepcopy(self.all_instructions),
            'rs_add': copy.deepcopy(self.rs_add),
            'rs_store': copy.deepcopy(self.rs_store),
            'rs_mult': copy.deepcopy(self.rs_mult),
            'rs_branch': copy.deepcopy(self.rs_branch),
            'register_file': copy.deepcopy(self.register_file)
        }
        self.state_history.append(state)

    def restore_previous_state(self):
        """Restaura o estado anterior (Step Back)"""
        if len(self.state_history) == 0:
            return False  # Não há histórico

        state = self.state_history.pop()
        self.current_clock = state['current_clock']
        self.bubble_cycles = state['bubble_cycles']
        self.program_counter = state['program_counter']
        self.cdb_producer_tag = state['cdb_producer_tag']
        self.cdb_value = state['cdb_value']
        self.all_instructions = state['instructions']
        self.rs_add = state['rs_add']
        self.rs_store = state['rs_store']
        self.rs_mult = state['rs_mult']
        self.rs_branch = state['rs_branch']
        self.register_file = state['register_file']
        return True

    def can_step_back(self):
        """Verifica se é possível voltar um ciclo"""
        return len(self.state_history) > 0

    def next_cycle(self):
        """Método para avançar um ciclo"""
        if self.is_simulation_finished():
            return
        # Salva o estado antes de avançar (para permitir Step Back)
        self.save_state()
        self.current_clock += 1
        # As fases na ordem correta
        self.commit_instructions()
        self.write_result_to_cdb()
        self.execute_instructions()
        self.issue_from_instruction_queue()

    def run_to_end(self):
        """Método para executar até o fim"""
        while not self.is_simulation_finished():
            self.next_cycle()

    def is_simulation_finished(self):
        """Verifica se a simulação terminou"""
        if not self.all_instructions:
            return True  # Se não há instruções, a simulação está "pronta"
        for instr in self.all_instructions:
            if not instr.is_squashed() and instr.get_commit_cycle() == -1:
                return False  # Ainda há instruções não comitadas e não descartadas
        return True  # Todas as instruções foram comitadas ou descartadas

    def issue_from_instruction_queue(self):
        if self.program_counter < len(self.all_instructions):
            instr_to_issue = self.all_instructions[self.program_counter]

            if instr_to_issue.is_squashed() or instr_to_issue.get_issue_cycle() != -1:
                self.program_counter += 1  # Já squashed ou emitida, avança
                return

            target_rs_array = None
            if instr_to_issue.get_op() in [Op.ADD, Op.SUB]:
                target_rs_array = self.rs_add
            elif instr_to_issue.get_op() in [Op.LD, Op.ST]:
                target_rs_array = self.rs_store
            elif instr_to_issue.get_op() in [Op.MUL, Op.DIV]:
                target_rs_array = self.rs_mult
            elif instr_to_issue.get_op() in [Op.BEQ, Op.BNE]:
                target_rs_array = self.rs_branch

            if target_rs_array is not None:
                issued = False
                for rs in target_rs_array:
                    if not rs.is_busy():
                        Qj = None
                        Vj = None
                        Qk = None
                        Vk = None

                        # Resolve src1
                        if instr_to_issue.get_src1() != "0":
                            src1_status = self.register_file.get_register_status(instr_to_issue.get_src1())
                            if src1_status is not None:
                                if src1_status.get_producer_tag() is not None:
                                    Qj = src1_status.get_producer_tag()
                                else:
                                    Vj = src1_status.get_value()
                            else:
                                try:
                                    Vj = float(instr_to_issue.get_src1())
                                except ValueError:
                                    Vj = 0.0
                        else:
                            Vj = 0.0

                        # Resolve src2
                        if instr_to_issue.get_src2() != "0":
                            src2_status = self.register_file.get_register_status(instr_to_issue.get_src2())
                            if src2_status is not None:
                                if src2_status.get_producer_tag() is not None:
                                    Qk = src2_status.get_producer_tag()
                                else:
                                    Vk = src2_status.get_value()
                            else:
                                try:
                                    Vk = float(instr_to_issue.get_src2())
                                except ValueError:
                                    Vk = 0.0
                        else:
                            Vk = 0.0

                        rs.assign(instr_to_issue, instr_to_issue.get_op(), Qj, Vj, Qk, Vk)
                        instr_to_issue.set_issue_cycle(self.current_clock)

                        # BUG FIX #3: Marcar instruções como especulativas
                        # Verifica se existe branch não-comitado antes desta instrução
                        for i in range(self.program_counter - 1, -1, -1):
                            prev_instr = self.all_instructions[i]
                            if (prev_instr.get_op() in [Op.BEQ, Op.BNE] and
                                prev_instr.get_commit_cycle() == -1):
                                instr_to_issue.set_speculative(prev_instr.get_id())
                                break

                        # Atualizar o Register File (RAT) para o registrador de destino
                        if instr_to_issue.get_dest() is not None and instr_to_issue.get_dest() != "0":
                            self.register_file.update_register_status(instr_to_issue.get_dest(), None, rs.get_name())
                        issued = True
                        break

                if issued:
                    self.program_counter += 1
                else:
                    self.bubble_cycles += 1

    def execute_instructions(self):
        # Cria lista com todas as RSs
        all_rs = self.rs_add + self.rs_store + self.rs_mult + self.rs_branch

        for rs in all_rs:
            if rs.is_busy():
                instr = rs.get_instruction()
                if instr.is_squashed():
                    continue

                if instr.get_start_exec_cycle() == -1 and rs.is_ready_to_execute():
                    instr.set_start_exec_cycle(self.current_clock)
                elif instr.get_start_exec_cycle() != -1 and instr.get_end_exec_cycle() == -1:
                    if instr.get_current_latency() > 0:
                        instr.set_current_latency(instr.get_current_latency() - 1)
                        if instr.get_current_latency() == 0:
                            instr.set_end_exec_cycle(self.current_clock)
                            res = 0.0  # Placeholder para o resultado

                            # Lógica para branches - SEMPRE TOMA O SALTO nesta simulação
                            if (rs.get_op() in [Op.BEQ, Op.BNE]) and not instr.is_branch_resolved():
                                instr.set_branch_taken(True)
                                instr.set_branch_resolved(True)
                                res = 1.0  # Simboliza branch tomado
                            rs.set_result(res)
                # Removido: contagem de bolhas por data hazard (comportamento normal do Tomasulo)

    def write_result_to_cdb(self):
        self.cdb_producer_tag = None  # Limpa o CDB no início da fase
        self.cdb_value = None

        all_rs = self.rs_add + self.rs_store + self.rs_mult + self.rs_branch

        # Prioridade de escrita no CDB: aqui, a primeira RS que terminou escreve.
        for rs in all_rs:
            if (rs.is_busy() and rs.get_instruction().get_end_exec_cycle() != -1 and
                rs.get_instruction().get_write_result_cycle() == -1):
                if rs.get_instruction().is_squashed():
                    self.free_reservation_station(rs.get_instruction(), self.rs_add)
                    self.free_reservation_station(rs.get_instruction(), self.rs_store)
                    self.free_reservation_station(rs.get_instruction(), self.rs_mult)
                    self.free_reservation_station(rs.get_instruction(), self.rs_branch)
                    continue

                self.cdb_producer_tag = rs.get_name()
                self.cdb_value = rs.get_result()
                rs.get_instruction().set_write_result_cycle(self.current_clock)

                # Disparar atualizações para outras RSs e Register File
                self.update_reservation_stations_from_cdb(self.cdb_producer_tag, self.cdb_value)
                self.update_register_file_from_cdb(self.cdb_producer_tag, self.cdb_value,
                                                   rs.get_instruction().get_dest())

                # Uma RS por ciclo publica no CDB para simplificação
                return

    def update_reservation_stations_from_cdb(self, producer_tag, value):
        all_rs = self.rs_add + self.rs_store + self.rs_mult + self.rs_branch

        for rs in all_rs:
            if rs.is_busy():
                if rs.get_Qj() is not None and rs.get_Qj() == producer_tag:
                    rs.set_Vj(value)
                if rs.get_Qk() is not None and rs.get_Qk() == producer_tag:
                    rs.set_Vk(value)

    def update_register_file_from_cdb(self, producer_tag, value, dest_register):
        if dest_register is not None and dest_register != "0":
            status = self.register_file.get_register_status(dest_register)
            if (status is not None and status.get_producer_tag() is not None and
                status.get_producer_tag() == producer_tag):
                self.register_file.update_register_status(dest_register, value, None)

    def commit_instructions(self):
        instr_index_to_commit = -1
        for i in range(len(self.all_instructions)):
            if (not self.all_instructions[i].is_squashed() and
                self.all_instructions[i].get_commit_cycle() == -1):
                instr_index_to_commit = i
                break

        if instr_index_to_commit != -1:
            instr_to_commit = self.all_instructions[instr_index_to_commit]

            if instr_to_commit.get_write_result_cycle() != -1:
                instr_to_commit.set_commit_cycle(self.current_clock)

                # Lógica de SQUASHING para BRANCHES
                if (instr_to_commit.get_op() in [Op.BEQ, Op.BNE] and
                    instr_to_commit.is_branch_taken()):
                    target_instruction_index = -1
                    for i in range(len(self.all_instructions)):
                        if self.all_instructions[i].get_id() == instr_to_commit.get_branch_target_id():
                            target_instruction_index = i
                            break

                    if target_instruction_index != -1:
                        # BUG FIX: Descartar apenas instruções ENTRE branch e destino
                        # ANTES: descartava todas após o branch
                        # DEPOIS: descarta só as especulativas (entre branch+1 e destino-1)
                        for i in range(instr_index_to_commit + 1, target_instruction_index):
                            future_instr = self.all_instructions[i]
                            if future_instr.get_commit_cycle() == -1 and not future_instr.is_squashed():
                                future_instr.set_squashed(True)
                                self.total_squashed_count += 1  # Incrementa contador permanente
                                self.free_reservation_station(future_instr, self.rs_add)
                                self.free_reservation_station(future_instr, self.rs_store)
                                self.free_reservation_station(future_instr, self.rs_mult)
                                self.free_reservation_station(future_instr, self.rs_branch)
                        # Salta PC para o destino do branch
                        self.program_counter = target_instruction_index

                    # Limpa flag especulativa de todas instruções que dependiam deste branch
                    for instr in self.all_instructions:
                        if instr.get_speculative_branch_id() == instr_to_commit.get_id():
                            instr.clear_speculative()

                # Libera a RS da instrução comitada
                self.free_reservation_station(instr_to_commit, self.rs_add)
                self.free_reservation_station(instr_to_commit, self.rs_store)
                self.free_reservation_station(instr_to_commit, self.rs_mult)
                self.free_reservation_station(instr_to_commit, self.rs_branch)

                # Para instruções STORE, o valor é efetivamente "escrito" na memória no commit
                if instr_to_commit.get_op() == Op.ST:
                    store_rs = self.find_reservation_station(instr_to_commit, self.rs_store)
                    if store_rs is not None:
                        # Poderia simular a escrita em uma memória aqui
                        pass

    def free_reservation_station(self, committed_instruction, rs_array):
        for rs in rs_array:
            if rs.is_busy() and rs.get_instruction() == committed_instruction:
                rs.free()
                return

    def find_reservation_station(self, instruction, rs_array):
        for rs in rs_array:
            if rs.is_busy() and rs.get_instruction() == instruction:
                return rs
        return None

    # Getters para a GUI
    def get_current_clock(self):
        return self.current_clock

    def get_bubble_cycles(self):
        return self.bubble_cycles

    def get_all_instructions(self):
        return self.all_instructions.copy()

    def get_rs_add(self):
        return self.rs_add

    def get_rs_store(self):
        return self.rs_store

    def get_rs_mult(self):
        return self.rs_mult

    def get_rs_branch(self):
        return self.rs_branch

    def get_register_file(self):
        return self.register_file

    def get_total_squashed(self):
        """Retorna total de instruções descartadas (nunca reseta)"""
        return self.total_squashed_count

    def get_current_speculative_count(self):
        """Retorna número ATUAL de instruções especulativas (não comitadas e não descartadas)"""
        count = 0
        for instr in self.all_instructions:
            if (instr.is_speculative and
                not instr.is_squashed() and
                instr.get_commit_cycle() == -1):
                count += 1
        # Atualiza o máximo se necessário
        if count > self.max_speculative_count:
            self.max_speculative_count = count
        return count

    def calculate_ipc(self):
        committed_count = 0
        for instr in self.all_instructions:
            if instr.get_commit_cycle() != -1 and not instr.is_squashed():
                committed_count += 1
        if self.current_clock == 0:
            return 0.0
        return committed_count / self.current_clock
