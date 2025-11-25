from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos do simulador
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TOMASSULLLERoriSimulator import TOMASSULLLERoriSimulator
from Instruction import Instruction, Op


def index(request):
    """Página principal do simulador"""
    return render(request, 'simulator/index.html')


@csrf_exempt
def simulate(request):
    """API endpoint para executar a simulação"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            program_text = data.get('program', '')
            config = data.get('config', {})

            # Parse instruções
            instructions = parse_instructions(program_text)

            if not instructions:
                return JsonResponse({'error': 'Nenhuma instrução válida encontrada'}, status=400)

            # Configurar simulador
            num_rs_add = config.get('rs_add', 3)
            num_rs_mult = config.get('rs_mult', 2)
            num_rs_store = config.get('rs_store', 2)
            num_rs_branch = config.get('rs_branch', 1)

            latency_add = config.get('latency_add', 2)
            latency_mul = config.get('latency_mul', 10)
            latency_div = config.get('latency_div', 40)
            latency_load = config.get('latency_load', 2)
            latency_store = config.get('latency_store', 2)
            latency_branch = config.get('latency_branch', 1)

            # Criar simulador
            simulator = TOMASSULLLERoriSimulator(
                num_rs_add, num_rs_mult, num_rs_store, num_rs_branch,
                latency_add, latency_mul, latency_div, latency_load, latency_store, latency_branch
            )

            simulator.set_instructions(instructions)

            # Executar simulação ciclo a ciclo
            cycles_data = []
            max_cycles = 1000  # Limite de segurança

            # Captura estado inicial (ciclo 0)
            initial_state = capture_cycle_state(simulator)
            cycles_data.append(initial_state)

            while not simulator.is_simulation_finished() and simulator.get_current_clock() < max_cycles:
                simulator.next_cycle()
                cycle_state = capture_cycle_state(simulator)
                cycles_data.append(cycle_state)

            # Métricas finais
            total_instructions = len(instructions)
            committed = sum(1 for i in instructions if i.get_commit_cycle() != -1 and not i.is_squashed())

            metrics = {
                'ipc': simulator.calculate_ipc(),
                'total_cycles': simulator.get_current_clock(),
                'bubble_cycles': simulator.get_bubble_cycles(),
                'total_squashed': simulator.get_total_squashed(),
                'committed_instructions': committed,
                'total_instructions': total_instructions,
                'max_speculative': simulator.max_speculative_count,
                'efficiency': (committed / total_instructions * 100) if total_instructions > 0 else 0
            }

            return JsonResponse({
                'success': True,
                'cycles': cycles_data,
                'metrics': metrics
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


def parse_instructions(text):
    """Parse instruções do texto"""
    lines = text.strip().split('\n')
    instructions = []
    instr_id = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if '#' in line:
            line = line.split('#')[0].strip()

        parts = line.split()
        if len(parts) < 2:
            continue

        op_str = parts[0].upper()

        try:
            if op_str in ['BEQ', 'BNE']:
                # Formato: BEQ target src1 src2
                if len(parts) >= 4:
                    target_id = int(parts[1])
                    src1 = parts[2]
                    src2 = parts[3]
                    op = Op.BEQ if op_str == 'BEQ' else Op.BNE
                    instr = Instruction(instr_id, op, None, src1, src2, 1)
                    instr.set_branch_target_id(target_id)
                    instructions.append(instr)
                    instr_id += 1
            else:
                # Formato: OP dest src1 src2
                if len(parts) >= 4:
                    dest = parts[1]
                    src1 = parts[2]
                    src2 = parts[3]
                    op = Op[op_str]

                    # Define latência padrão
                    latency_map = {
                        'ADD': 2, 'SUB': 2, 'MUL': 10,
                        'DIV': 40, 'LD': 2, 'ST': 2
                    }
                    latency = latency_map.get(op_str, 2)

                    instr = Instruction(instr_id, op, dest, src1, src2, latency)
                    instructions.append(instr)
                    instr_id += 1
        except (KeyError, ValueError, IndexError):
            continue

    return instructions


def capture_cycle_state(simulator):
    """Captura o estado de um ciclo"""
    instructions_state = []

    for instr in simulator.get_all_instructions():
        state = 'waiting'
        if instr.is_squashed():
            state = 'squashed'
        elif instr.get_commit_cycle() != -1:
            state = 'committed'
        elif instr.get_write_result_cycle() != -1:
            state = 'write'
        elif instr.get_start_exec_cycle() != -1:
            state = 'executing'
        elif instr.get_issue_cycle() != -1:
            state = 'issued'

        instructions_state.append({
            'id': instr.get_id(),
            'op': instr.get_op().value,
            'dest': instr.get_dest(),
            'src1': instr.get_src1(),
            'src2': instr.get_src2(),
            'state': state,
            'issue': instr.get_issue_cycle(),
            'exec_start': instr.get_start_exec_cycle(),
            'exec_end': instr.get_end_exec_cycle(),
            'write': instr.get_write_result_cycle(),
            'commit': instr.get_commit_cycle(),
            'is_speculative': instr.is_speculative,
            'is_squashed': instr.is_squashed(),
            'speculative_branch_id': instr.get_speculative_branch_id()
        })

    # Captura estado das RSs (métodos com letras maiúsculas)
    rs_state = {
        'add': [{'busy': rs.is_busy(),
                 'op': rs.get_op().value if rs.is_busy() and rs.get_op() else None,
                 'vj': rs.get_Vj() if rs.get_Vj() is not None else 0.0,
                 'vk': rs.get_Vk() if rs.get_Vk() is not None else 0.0,
                 'qj': rs.get_Qj(),
                 'qk': rs.get_Qk(),
                 'cycles': rs.get_instruction().get_current_latency() if rs.is_busy() and rs.get_instruction() else None}
                for rs in simulator.get_rs_add()],
        'mult': [{'busy': rs.is_busy(),
                  'op': rs.get_op().value if rs.is_busy() and rs.get_op() else None,
                  'vj': rs.get_Vj() if rs.get_Vj() is not None else 0.0,
                  'vk': rs.get_Vk() if rs.get_Vk() is not None else 0.0,
                  'qj': rs.get_Qj(),
                  'qk': rs.get_Qk(),
                  'cycles': rs.get_instruction().get_current_latency() if rs.is_busy() and rs.get_instruction() else None}
                 for rs in simulator.get_rs_mult()],
        'store': [{'busy': rs.is_busy(),
                   'op': rs.get_op().value if rs.is_busy() and rs.get_op() else None,
                   'vj': rs.get_Vj() if rs.get_Vj() is not None else 0.0,
                   'vk': rs.get_Vk() if rs.get_Vk() is not None else 0.0,
                   'qj': rs.get_Qj(),
                   'qk': rs.get_Qk(),
                   'cycles': rs.get_instruction().get_current_latency() if rs.is_busy() and rs.get_instruction() else None}
                  for rs in simulator.get_rs_store()],
        'branch': [{'busy': rs.is_busy(),
                    'op': rs.get_op().value if rs.is_busy() and rs.get_op() else None,
                    'vj': rs.get_Vj() if rs.get_Vj() is not None else 0.0,
                    'vk': rs.get_Vk() if rs.get_Vk() is not None else 0.0,
                    'qj': rs.get_Qj(),
                    'qk': rs.get_Qk(),
                    'cycles': rs.get_instruction().get_current_latency() if rs.is_busy() and rs.get_instruction() else None}
                   for rs in simulator.get_rs_branch()]
    }

    # Captura estado do Register File
    register_file_state = []
    reg_file = simulator.get_register_file()
    registers = reg_file.get_registers()

    # Ordena registradores: em uso primeiro, depois ordem numérica (R0, R1, R2... R10, R11...)
    def sort_registers(reg_name):
        # Extrai o número do registrador (ex: "R10" -> 10)
        num = int(reg_name[1:]) if reg_name[1:].isdigit() else 0
        # Registradores com produtor (em uso) vêm primeiro (False < True)
        in_use = registers[reg_name].get_producer_tag() is None
        return (in_use, num)

    for reg_name in sorted(registers.keys(), key=sort_registers):
        status = registers[reg_name]
        register_file_state.append({
            'name': reg_name,
            'value': status.get_value(),
            'producer': status.get_producer_tag()
        })

    # Calcula métricas dinâmicas para este ciclo
    current_clock = simulator.get_current_clock()
    committed_count = sum(1 for i in simulator.get_all_instructions()
                         if i.get_commit_cycle() != -1 and i.get_commit_cycle() <= current_clock and not i.is_squashed())
    ipc_current = committed_count / current_clock if current_clock > 0 else 0.0

    # Conta instruções descartadas até este ciclo
    squashed_until_now = sum(1 for i in simulator.get_all_instructions() if i.is_squashed())

    return {
        'clock': simulator.get_current_clock(),
        'instructions': instructions_state,
        'reservation_stations': rs_state,
        'register_file': register_file_state,
        'speculative_count': simulator.get_current_speculative_count(),
        'squashed_count': squashed_until_now,
        'ipc': ipc_current,
        'committed_count': committed_count,
        'bubble_cycles': simulator.get_bubble_cycles()
    }
