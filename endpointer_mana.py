import pymem
import pymem.process
import time
import os

# Nome do processo do jogo
PROCESS_NAME = "PathOfExile.exe"
# Nome do arquivo contendo os ponteiros
FILE_NAME = "pointers_mana.txt"

def load_pointers():
    pointers = []
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()  # Remove espaços extras e quebras de linha
            if not line or line.startswith("Base Address"):  # Ignora cabeçalho e linhas vazias
                continue

            parts = line.split()
            if len(parts) < 9:  # Garante que há pelo menos 9 colunas na linha
                continue

            try:
                base_address = parts[0].split("+")  # Exemplo: "PathOfExile.exe+038ADEC8"
                module_name = base_address[0].strip('"')  # Remove aspas
                base_offset = int(base_address[1], 16)  # Converte o endereço base para HEX

                offsets = []
                for value in parts[1:8]:  # Pega os offsets (7 valores)
                    if all(c in "0123456789ABCDEFabcdef" for c in value):  # Verifica se é HEX válido
                        offsets.append(int(value, 16))

                if len(offsets) == 7:
                    pointers.append((module_name, base_offset, offsets))

            except Exception as e:
                print(f"Erro ao processar linha {line}: {e}")

    return pointers

def read_memory():
    try:
        pm = pymem.Pymem(PROCESS_NAME)
        pointers = load_pointers()

        base_address = pymem.process.module_from_name(pm.process_handle, PROCESS_NAME).lpBaseOfDll

        while True:
            valid_mana = None  # Variável para verificar se a mana foi encontrada

            for module_name, base_offset, offsets in pointers:
                addr = base_address + base_offset

                # Tentativa de leitura com os offsets
                for offset in offsets:
                    try:
                        addr = pm.read_longlong(addr) + offset
                    except pymem.exception.MemoryReadError:
                        continue  # Se ocorrer erro, tenta o próximo offset

                try:
                    mana_value = pm.read_int(addr)  # Tenta ler o valor da mana
                    if mana_value:  # Se a mana for válida
                        valid_mana = mana_value
                        break  # Sai do loop de offsets se a mana for encontrada

                except pymem.exception.MemoryReadError:
                    continue  # Ignora erro de leitura de memória e tenta o próximo ponteiro

            if valid_mana is not None:  # Se a mana foi encontrada, exibe o valor
                os.system('cls' if os.name == 'nt' else 'clear')  # Limpa a tela
                print(f"Mana: {valid_mana}")
            else:
                print("Erro: Não foi possível encontrar a mana válida.")  # Se não encontrou mana

            time.sleep(0.5)  # Espera 0.5 segundos antes de tentar novamente

    except Exception as e:
        print(f"Erro ao acessar memória: {e}")

# Chamar a função para testar
read_memory()
