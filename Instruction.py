from enum import Enum


class Op(Enum):
    ADD = "ADD"
    SUB = "SUB"
    LD = "LD"
    ST = "ST"
    BEQ = "BEQ"
    BNE = "BNE"
    MUL = "MUL"
    DIV = "DIV"


class Instruction:
    def __init__(self, id, op, dest, src1, src2, latency):
        self.id = id
        self.op = op
        self.dest = dest
        self.src1 = src1
        self.src2 = src2
        self.original_latency = latency
        self.current_latency = latency

        self.issue_cycle = -1
        self.start_exec_cycle = -1
        self.end_exec_cycle = -1
        self.write_result_cycle = -1
        self.commit_cycle = -1

        # Campos para Branches
        self.branch_target_id = -1
        self.branch_taken = False
        self.branch_resolved = False
        self.squashed = False

        # Campos para Especulação
        self.is_speculative = False
        self.speculative_branch_id = -1

    # Getters
    def get_id(self):
        return self.id

    def get_op(self):
        return self.op

    def get_dest(self):
        return self.dest

    def get_src1(self):
        return self.src1

    def get_src2(self):
        return self.src2

    def get_original_latency(self):
        return self.original_latency

    def get_current_latency(self):
        return self.current_latency

    def get_issue_cycle(self):
        return self.issue_cycle

    def get_start_exec_cycle(self):
        return self.start_exec_cycle

    def get_end_exec_cycle(self):
        return self.end_exec_cycle

    def get_write_result_cycle(self):
        return self.write_result_cycle

    def get_commit_cycle(self):
        return self.commit_cycle

    def get_branch_target_id(self):
        return self.branch_target_id

    def is_branch_taken(self):
        return self.branch_taken

    def is_branch_resolved(self):
        return self.branch_resolved

    def is_squashed(self):
        return self.squashed

    def get_speculative_branch_id(self):
        return self.speculative_branch_id

    # Setters
    def set_current_latency(self, current_latency):
        self.current_latency = current_latency

    def set_issue_cycle(self, issue_cycle):
        self.issue_cycle = issue_cycle

    def set_start_exec_cycle(self, start_exec_cycle):
        self.start_exec_cycle = start_exec_cycle

    def set_end_exec_cycle(self, end_exec_cycle):
        self.end_exec_cycle = end_exec_cycle

    def set_write_result_cycle(self, write_result_cycle):
        self.write_result_cycle = write_result_cycle

    def set_commit_cycle(self, commit_cycle):
        self.commit_cycle = commit_cycle

    def set_branch_target_id(self, branch_target_id):
        self.branch_target_id = branch_target_id

    def set_branch_taken(self, branch_taken):
        self.branch_taken = branch_taken

    def set_branch_resolved(self, branch_resolved):
        self.branch_resolved = branch_resolved

    def set_squashed(self, squashed):
        self.squashed = squashed

    def set_speculative(self, branch_id):
        """Marca instrução como especulativa"""
        self.is_speculative = True
        self.speculative_branch_id = branch_id

    def clear_speculative(self):
        """Limpa flag de especulação"""
        self.is_speculative = False
        self.speculative_branch_id = -1

    def __str__(self):
        base_string = (f"Instr {self.id}: {self.op.value} {self.dest}, {self.src1}, {self.src2} | "
                      f"Issue: {self.issue_cycle if self.issue_cycle != -1 else 'N/A'}, "
                      f"Start Exec: {self.start_exec_cycle if self.start_exec_cycle != -1 else 'N/A'}, "
                      f"End Exec: {self.end_exec_cycle if self.end_exec_cycle != -1 else 'N/A'}, "
                      f"Write Result: {self.write_result_cycle if self.write_result_cycle != -1 else 'N/A'}, "
                      f"Commit: {self.commit_cycle if self.commit_cycle != -1 else 'N/A'} | "
                      f"Latency Restante: {self.current_latency}")
        if self.squashed:
            return base_string + " (DESCARTADA)"
        elif self.is_speculative and self.commit_cycle == -1:
            return base_string + f" (ESPECULATIVA - depende do branch ID {self.speculative_branch_id})"
        return base_string
