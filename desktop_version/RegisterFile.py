class RegisterStatus:
    def __init__(self, value, producer_tag):
        self.value = value
        self.producer_tag = producer_tag  # Nome da RS que está produzindo o valor para este registrador

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def get_producer_tag(self):
        return self.producer_tag

    def set_producer_tag(self, producer_tag):
        self.producer_tag = producer_tag


class RegisterFile:
    def __init__(self):
        self.registers = {}
        # Inicializa 32 registradores (R0-R31) - Padrão MIPS
        # R0 é sempre zero (convenção MIPS), mas por simplicidade permitimos escrita aqui
        for i in range(32):
            self.registers[f"R{i}"] = RegisterStatus(0.0, None)  # Valor 0.0, sem produtor

    def get_register_status(self, register_name):
        return self.registers.get(register_name)

    def update_register_status(self, register_name, value, producer_tag):
        if register_name not in self.registers:
            # Adiciona se não existe (útil se você usar outros registradores)
            self.registers[register_name] = RegisterStatus(value, producer_tag)
        else:
            status = self.registers[register_name]
            status.set_value(value)
            status.set_producer_tag(producer_tag)

    def get_registers(self):
        """Getter para a GUI acessar os dados do Register File"""
        return self.registers.copy()  # Retorna uma cópia
