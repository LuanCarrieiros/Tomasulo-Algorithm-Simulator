class ReservationStation:
    def __init__(self, name):
        self.name = name
        self.busy = False
        self.free()  # Inicializa em estado livre

    def assign(self, instruction, op, Qj, Vj, Qk, Vk):
        """Atribui uma instrução a esta Reservation Station"""
        self.busy = True
        self.instruction = instruction
        self.op = op
        self.Qj = Qj
        self.Vj = Vj
        self.Qk = Qk
        self.Vk = Vk
        self.result = None  # Limpa o resultado anterior

    def free(self):
        """Libera esta Reservation Station"""
        self.busy = False
        self.instruction = None
        self.op = None
        self.Qj = None
        self.Vj = None
        self.Qk = None
        self.Vk = None
        self.result = None

    def is_ready_to_execute(self):
        """Verifica se a RS está pronta para executar (operandos disponíveis)"""
        # Se Qj e Qk são None, significa que os valores Vj e Vk estão disponíveis.
        return self.Qj is None and self.Qk is None

    # Getters
    def get_name(self):
        return self.name

    def is_busy(self):
        return self.busy

    def get_op(self):
        return self.op

    def get_Qj(self):
        return self.Qj

    def get_Vj(self):
        return self.Vj

    def get_Qk(self):
        return self.Qk

    def get_Vk(self):
        return self.Vk

    def get_result(self):
        return self.result

    def get_instruction(self):
        return self.instruction

    # Setters
    def set_Vj(self, vj):
        """Valor recebido, Qj limpo"""
        self.Vj = vj
        self.Qj = None

    def set_Vk(self, vk):
        """Valor recebido, Qk limpo"""
        self.Vk = vk
        self.Qk = None

    def set_result(self, result):
        self.result = result

    def set_Qj(self, Qj):
        """Usado para redefinir Qj se a instrução produtora é descartada"""
        self.Qj = Qj

    def set_Qk(self, Qk):
        """Usado para redefinir Qk se a instrução produtora é descartada"""
        self.Qk = Qk

    def __str__(self):
        return (f"{self.name}: {'Busy' if self.busy else 'Free'} | "
                f"Op: {self.op.value if self.op else 'N/A'} | "
                f"Qj: {self.Qj if self.Qj else 'N/A'}, "
                f"Vj: {self.Vj if self.Vj is not None else 0.0:.2f} | "
                f"Qk: {self.Qk if self.Qk else 'N/A'}, "
                f"Vk: {self.Vk if self.Vk is not None else 0.0:.2f} | "
                f"Result: {self.result if self.result is not None else 0.0:.2f} | "
                f"Instr ID: {self.instruction.get_id() if self.instruction else 'N/A'}")
