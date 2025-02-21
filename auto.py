import tkinter as tk
from tkinter import ttk
import psutil
import os
from PIL import ImageGrab
import pytesseract
import threading
import time
from pynput import mouse
from tkinter import messagebox
import keyboard

# Função para verificar se o jogo está aberto
def is_game_running(process_name="PathOfExile.exe"):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
            return True
    return False

# Função para salvar as configurações no arquivo settings.txt
def save_settings(mp_key, mana_location, mp_state, slider_value, delay_value):
    with open("settings.txt", "w") as file:
        file.write(f"MP Key: {mp_key}\n")
        file.write(f"Mana Location: {mana_location}\n")
        file.write(f"MP State: {mp_state}\n")
        file.write(f"Slider Value: {slider_value}\n")
        file.write(f"Delay Value: {int(delay_value)}\n")  # Converte para inteiro antes de salvar

#------------------------ Start --------------------------------------#
# Função para carregar as configurações do arquivo
def load_settings():
    try:
        with open("settings.txt", "r") as file:
            settings = file.readlines()

            mp_key = settings[0].split(":")[1].strip() if len(settings) > 0 else ""
            mana_location = settings[1].split(":")[1].strip() if len(settings) > 1 else ""

            if mana_location:
                try:
                    mana_location = tuple(map(int, mana_location.strip("()").split(", ")))
                except ValueError:
                    print(f"Erro ao converter a localização de Mana: {mana_location}")
                    mana_location = None

            mp_state = settings[2].split(":")[1].strip().lower() == "true" if len(settings) > 2 else False
            slider_value = int(float(settings[3].split(":")[1].strip())) if len(settings) > 3 else 0
            delay_value = int(float(settings[4].split(":")[1].strip())) if len(settings) > 4 else 1  # Definindo um valor padrão de 1 para o delay

            return mp_key, mana_location, mp_state, slider_value, delay_value

    except FileNotFoundError:
        print("Arquivo settings.txt não encontrado.")
        return "", None, False, 0, 1  # Usando o valor padrão de 1 para delay se o arquivo não for encontrado

    except ValueError as e:
        print(f"Erro ao carregar as configurações: {e}")
        return "", None, False, 0, 1  # Usando o valor padrão de 1 para delay em caso de erro

#------------------------ End --------------------------------------#

#Função que determina os segundo para usar pote de MP.
ultima_vez_pressionado = 0  # Inicialmente, nenhum pote foi usado ainda
primeira_vez = True  # Variável para identificar a primeira ativação

def usar_pote_mana(mana_atual, mana_total):
    global ultima_vez_pressionado, primeira_vez
    delay = delay_var.get()  # Obtém o valor do delay em segundos

    # Se for a primeira vez, usa o pote imediatamente
    if primeira_vez:
        print(f"Mana baixa ({mana_atual}/{mana_total}), pressionando tecla {mp_key}")
        keyboard.press_and_release(mp_key)  # Pressiona a tecla do pote
        ultima_vez_pressionado = time.time()  # Atualiza o tempo do último uso
        primeira_vez = False  # Define que a primeira vez já ocorreu
        return  # Sai da função sem aplicar delay

    # Para as próximas ativações, respeita o delay configurado
    tempo_decorrido = time.time() - ultima_vez_pressionado
    if tempo_decorrido >= delay:
        # Se o tempo de delay já passou, usa o pote instantaneamente
        print(f"Mana baixa ({mana_atual}/{mana_total}), pressionando tecla {mp_key}")
        keyboard.press_and_release(mp_key)
        ultima_vez_pressionado = time.time()  # Atualiza o tempo do último uso
    else:
        # Caso contrário, informa quanto tempo falta até o próximo uso
        remaining_time = delay - tempo_decorrido
        print(f"Tempo restante até o próximo uso: {remaining_time:.1f} segundos.")

#----------------------------------------------------------------------------#

# Função para iniciar o processo de "Start"
def on_start_click():
    if not mana_location:
        preview_label.config(text="Erro: Nenhuma área de Mana configurada.", foreground="red")
        return

    start_button.config(state="disabled")
    stop_button.config(state="normal")
    print("Iniciando o programa...")

    # Salva as configurações ao pressionar Start
    save_settings(mp_key_entry.get(), str(mana_location), mp_var.get(), slider_var.get(), int(delay_var.get()))

    running_flag.set()
    threading.Thread(target=update_mana_in_real_time, daemon=True).start()

# Função para parar o processo de "Stop"
def on_stop_click():
    running_flag.clear()
    start_button.config(state="normal")
    stop_button.config(state="disabled")
    print("Parando o programa...")

# Função para controlar a habilitação do botão "Select MP Area"
def toggle_select_mp_area():
    if mp_var.get():
        select_area_button.config(state="disabled")
        slider.config(state="disabled")
    else:
        select_area_button.config(state="normal")
        slider.config(state="normal")

# Função para iniciar o processo de seleção de área
def select_area():
    def on_click(x, y, button, pressed):
        global monitor_center
        if pressed:  # Clique inicial para selecionar o ponto
            monitor_center = (x, y)
            print(f"Centro selecionado: {x}, {y}")
            listener.stop()

    # Informar o usuário para clicar no centro da área desejada
    root.withdraw()
    messagebox.showinfo("Instrução", "Clique no centro da área que deseja capturar.")
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    root.deiconify()

    # Se o centro foi selecionado, captura a área correspondente
    if monitor_center:
        capture_area()

# Função para capturar a área com base no centro selecionado
def capture_area():
    global monitor_center, mana_location
    if not monitor_center:
        print("Nenhuma área selecionada!")
        return

    x_center, y_center = monitor_center
    rect_width = 200  # Largura da área a capturar
    rect_height = 70  # Altura da área a capturar

    # Definir as coordenadas da área com base no centro selecionado
    x1 = x_center - rect_width // 2
    y1 = y_center - rect_height // 2
    x2 = x_center + rect_width // 2
    y2 = y_center + rect_height // 2

    mana_location = (x1, y1, x2, y2)
    save_settings(mp_key_entry.get(), str(mana_location), mp_var.get(), slider_var.get(), delay_var.get())
    print(f"Área selecionada: {mana_location}")
    preview_label.config(text="Área de Mana Selecionada!", foreground="green")

    # Exibir a mana capturada
    mana_text = extract_text_from_screen()
    preview_label.config(text=mana_text, foreground="green" if "Mana" in mana_text else "red")

# Configurações do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Variáveis globais
monitor_center = None
mana_location = None
running_flag = threading.Event()

# Criando a janela principal
root = tk.Tk()
root.title("PoE Auto Master")
root.geometry("500x600")
root.resizable(False, False)

# Adicionando rótulo para exibir o status do jogo
game_status_label = ttk.Label(root, text="Status: Checking...", foreground="blue", font=("Arial", 10))
game_status_label.pack(pady=5)

# Função para atualizar a mensagem de status
def update_game_status():
    if is_game_running():
        game_status_label.config(text="Status: The Game Is OPEN", foreground="green")
    else:
        game_status_label.config(text="Status: The Game Is CLOSED", foreground="red")

auto_loot_frame = ttk.LabelFrame(root, text="Configuration", padding=10)
auto_loot_frame.pack(padx=10, pady=10, fill="both", expand=True)

settings_frame = ttk.LabelFrame(auto_loot_frame, text="Auto-Sustaining", padding=10)
settings_frame.pack(padx=2, pady=2, anchor="n")

mp_label = ttk.Label(settings_frame, text="MP", font=("Arial", 10, "bold"), foreground="blue")
mp_label.grid(row=0, column=0, sticky="w", pady=10)

mp_var = tk.BooleanVar(value=False)
disable_checkbox = ttk.Checkbutton(settings_frame, text="Disable", variable=mp_var, command=toggle_select_mp_area)
disable_checkbox.grid(row=0, column=1, padx=5)

slider_var = tk.IntVar(value=0)
slider = ttk.Scale(settings_frame, from_=0, to=100, orient="horizontal", variable=slider_var, command=lambda val: slider_value_label.config(text=f"{int(float(val))}%"))
slider.grid(row=0, column=2, padx=10)
slider_value_label = ttk.Label(settings_frame, text="0%", font=("Arial", 10))
slider_value_label.grid(row=0, column=3, padx=5)

mp_key_label = ttk.Label(settings_frame, text="Key MP:", font=("Arial", 10))
mp_key_label.grid(row=1, column=0, sticky="w", pady=10)

mp_key_entry = ttk.Entry(settings_frame, width=10)
mp_key_entry.grid(row=1, column=1, padx=5)

select_area_button = ttk.Button(settings_frame, text="Select MP Area", command=select_area)
select_area_button.grid(row=1, column=2, padx=10)

# --- ADICIONANDO SLIDER PARA ATRASO ENTRE USOS DE POTE (EM SEGUNDOS) ---
# Criando variável para armazenar o atraso (em segundos)
delay_var = tk.DoubleVar(value=1.0)  # Valor padrão 1 segundo

# Adicionando o slider de delay acima da seleção da área de MP
delay_label = ttk.Label(settings_frame, text="Delay (seg):", font=("Arial", 10))
delay_label.grid(row=2, column=0, sticky="w", pady=5)

delay_slider = ttk.Scale(settings_frame, from_=0.1, to=5.0, orient="horizontal", variable=delay_var)
delay_slider.grid(row=2, column=1, padx=5)

delay_value_label = ttk.Label(settings_frame, text="1.0s", font=("Arial", 10))
delay_value_label.grid(row=2, column=2, padx=5)

# Atualizar rótulo conforme o usuário ajusta o slider
def update_delay_label(value):
    delay_value_label.config(text=f"{float(value):.1f}s")

delay_slider.config(command=update_delay_label)
# --------------------------------------------------------------

# Ajustando o preview_label para ficar abaixo do slider de atraso
preview_label = ttk.Label(settings_frame, text="No Captures Taken.", foreground="red", wraplength=300)
preview_label.grid(row=3, column=0, columnspan=4, pady=5)

mp_key, mana_location, mp_state, slider_value, delay_value = load_settings()
print(f"Configuração carregada: Mana Location = {mana_location}")
delay_var.set(delay_value)  # Define o valor carregado no controle deslizante
mp_key_entry.insert(0, mp_key)
mp_var.set(mp_state)
slider_var.set(slider_value)
slider_value_label.config(text=f"{slider_value}%")
toggle_select_mp_area()

if mana_location:  # Verifique se a localização da mana foi carregada
    mana_text = extract_text_from_screen()  # Captura a mana com a localização salva
    preview_label.config(text=mana_text, foreground="green" if "Mana" in mana_text else "red")
else:
    preview_label.config(text="Erro: Nenhuma área de Mana configurada.", foreground="red")

start_button = ttk.Button(root, text="Start", command=on_start_click)
start_button.pack(pady=10)

stop_button = ttk.Button(root, text="Stop", state="disabled", command=on_stop_click)
stop_button.pack(pady=10)

update_game_status()
root.mainloop()
