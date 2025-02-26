import tkinter as tk
from tkinter import ttk
import random
import pynetlogo
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ambiente import EnvironmentModel

matplotlib.use('TkAgg')

#formula
#prob = alfa1*(t-t0) + alfa2*(h-h0) + alfa3*(d-d0) + alfa4*(v - cos(teta) + 1) +  alfa5*(precipitaçao) + alfa6*(humidade) + tipoarvores

class SimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulação de Fogo - Interface Desktop")

        # 1) Conexão com NetLogo
        self.netlogo = pynetlogo.NetLogoLink(
            gui=False,
            netlogo_home=r"C:\Program Files\NetLogo 6.4.0"
        )
        self.netlogo.load_model(r"C:\Users\david\Desktop\Bolsa_Investigacao\projeto\simulacao_fogo.nlogo")
        self.model = EnvironmentModel(5, 10, 10, netlogo=self.netlogo)
        self.netlogo.command("setup")

        # Dados para gráfico
        self.burned_area_evol = []
        self.forested_area_evol = []
        self.timesteps = []

        # Layout da interface
        controls_frame = ttk.Frame(self)
        controls_frame.pack(padx=10, pady=10, fill=tk.X)

        self.iter_label = ttk.Label(controls_frame, text="Iterações:")
        self.iter_label.pack(side=tk.LEFT, padx=5)

        self.iter_scale = ttk.Scale(
            controls_frame,
            from_=10, to=500,
            orient="horizontal",
            length=200
        )
        self.iter_scale.set(200)
        self.iter_scale.pack(side=tk.LEFT, padx=5)

        # Botão "Iniciar Simulação"
        self.run_button = ttk.Button(
            controls_frame,
            text="Iniciar Simulação",
            command=self.run_simulation
        )
        self.run_button.pack(side=tk.LEFT, padx=5)

        # Botão "Apagar Fogo"
        self.stop_fire_button = ttk.Button(
            controls_frame,
            text="Apagar Fogo",
            command=self.stop_fire
        )
        self.stop_fire_button.pack(side=tk.LEFT, padx=5)

        # Label p/ mostrar se há incêndio e temperatura
        self.fire_status_var = tk.StringVar(value="Incêndio: Inativo (Temp: -- °C)")
        self.fire_status_label = ttk.Label(controls_frame, textvariable=self.fire_status_var)
        self.fire_status_label.pack(side=tk.LEFT, padx=10)

        # Caixa de texto para logs
        self.log_text = tk.Text(self, height=10, width=60)
        self.log_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Gráfico
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.ax.set_xlabel("Iterações")
        self.ax.set_ylabel("Quantidade")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.add_log("Interface pronta. Ajuste as iterações e clique em 'Iniciar Simulação'.")

        # Para sabermos se o fires_detected mudou de um passo para outro
        self.last_detected_count = 0

    def add_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def run_simulation(self):
        self.log_text.delete("1.0", tk.END)
        self.burned_area_evol.clear()
        self.forested_area_evol.clear()
        self.timesteps.clear()

        self.netlogo.command("setup")
        self.model.fires_created = 0
        self.model.fires_detected = 0
        self.model.detect_countdown = 0
        self.last_detected_count = 0  # zera ao iniciar

        iterations = int(self.iter_scale.get())

        self.add_log("Preparando simulação...")
        self.add_log(f"Executando {iterations} iterações.\n")

        for i in range(iterations):
            # Podemos gerar fogo aleatoriamente, mas sem logar
            if random.random() < 0.1:  # 10% de chance, por exemplo
                self.model.start_fire()

            # Step do modelo
            self.model.step()

            # Verifica se pelo menos 2 sensores (ar, animais, temperatura) foram ativados
            if self.model.check_fire_sensors():
                # Log de alerta
                self.add_log("[ALERTA] 🚨 Múltiplos sensores ativados! POSSÍVEL INCÊNDIO DETECTADO!")
                self.fire_status_var.set(
                    f"🔥 ALERTA DE INCÊNDIO! (Temp: {self.model.temperature:.1f} °C)"
                )
            else:
                # Caso contrário, mostra se ainda há fogo ou não
                if self.model.is_fire_active():
                    self.fire_status_var.set(
                        f"Incêndio: ATIVO (Temp: {self.model.temperature:.1f} °C)"
                    )
                else:
                    self.fire_status_var.set(
                        f"Incêndio: Inativo (Temp: {self.model.temperature:.1f} °C)"
                    )

            # Se fires_detected aumentou neste tick => houve detecção (contagem de incêndios)
            if self.model.fires_detected > self.last_detected_count:
                self.last_detected_count = self.model.fires_detected
                current_temp = self.model.temperature
                self.add_log(f"[TICK {i}] Incêndio DETECTADO! Temperatura = {current_temp:.1f} °C (contador=10 ticks)")

            # Coleta dados do NetLogo
            burned_trees = self.netlogo.report("burned-trees")
            forested_trees = self.netlogo.report("count patches with [pcolor = green]")

            self.burned_area_evol.append(burned_trees)
            self.forested_area_evol.append(forested_trees)
            self.timesteps.append(i)

            self.add_log(f"Iteração {i} | Queimadas: {burned_trees}, Florestadas: {forested_trees}")
            self.update_idletasks()

        self.add_log("\nSimulação finalizada!")
        self.add_log(f"Número de incêndios criados: {self.model.fires_created}")
        self.add_log(f"Número de incêndios detectados: {self.model.fires_detected}")

        self.update_plot()

    def stop_fire(self):
        self.model.stop_fire()
        self.add_log("Fogo apagado manualmente!")

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("Evolução de Árvores Queimadas x Florestadas")
        self.ax.set_xlabel("Iterações")
        self.ax.set_ylabel("Quantidade")
        self.ax.grid(True)

        if self.timesteps:
            self.ax.plot(self.timesteps, self.burned_area_evol, label='Árvores Queimadas', color='red')
            self.ax.plot(self.timesteps, self.forested_area_evol, label='Árvores Florestadas', color='green')
            self.ax.legend()

        self.canvas.draw()


if __name__ == "__main__":
    app = SimulationApp()
    app.mainloop()
