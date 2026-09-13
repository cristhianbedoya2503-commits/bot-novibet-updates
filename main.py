import sys
import io
import os
import subprocess
import threading
import asyncio
import customtkinter as ctk

# Importamos nuestros módulos independientes
import limpieza
import vpn_manager
import novibet_bot

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Evento global para manejar la Pausa / Reanudación
evento_pausa = threading.Event()
evento_pausa.set()

class TextRedirector(io.IOBase):
    """Clase para redirigir la consola con colores elegantes hacia la interfaz[cite: 2]."""
    def __init__(self, widget):
        self.widget = widget

    def write(self, str_text):
        self.widget.after(0, self.append_colored_text, str_text)
        return len(str_text)

    def append_colored_text(self, text):
        self.widget.configure(state="normal")
        
        tag = "blanco"
        t_upper = text.upper()
        if "===" in text or "MÓDULO" in t_upper or "COMPLETADA" in t_upper:
            tag = "cyan"
        elif "[INFO]" in text:
            tag = "azul"
        elif "[OK]" in text or "ÉXITO" in t_upper or "LIBERADOS" in t_upper:
            tag = "verde"
        elif "[LIMPIEZA]" in text or "[EXCEL]" in text:
            tag = "amarillo"
        elif "->" in text or "C:\\" in text or "USERS" in t_upper or "PROPIEDAD" in t_upper:
            tag = "morado"
        elif "[ERROR]" in text or "[AVISO]" in text or "FALLO" in t_upper or "DETENIDO" in t_upper or "PAUSADO" in t_upper:
            tag = "rojo"

        self.widget.insert("end", text, tag)
        self.widget.see("end")
        self.widget.configure(state="disabled")

class AppNovibetCTK(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Panel de Control - ACTUALIZADO DESDE GITHUB")
        self.geometry("1050x650")
        self.minsize(950, 540)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL LATERAL (SIDEBAR)[cite: 2] ---
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="⚡ Novibet Panel", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 15))

        btn_font = ctk.CTkFont(size=14, weight="bold")

        # Botón 1: Ejecutar Todo en Secuencia Automática
        self.sidebar_btn_todo = ctk.CTkButton(
            self.sidebar_frame, text="🚀 Ejecutar Todo (Auto)", fg_color="#107C41", 
            text_color="white", hover_color="#0b5329", anchor="w",
            height=44, font=btn_font, command=self.ejecutar_hilo_secuencia_total
        )
        self.sidebar_btn_todo.grid(row=1, column=0, padx=15, pady=8, sticky="ew")

        # Botón 2: Limpieza
        self.sidebar_btn_limpieza = ctk.CTkButton(
            self.sidebar_frame, text="🧹 Limpieza Total", fg_color="transparent", 
            text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
            height=40, font=btn_font, command=self.ejecutar_hilo_limpieza
        )
        self.sidebar_btn_limpieza.grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        # Botón 3: VPN
        self.sidebar_btn_vpn = ctk.CTkButton(
            self.sidebar_frame, text="🌐 Configurar VPN", fg_color="transparent", 
            text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
            height=40, font=btn_font, command=self.ejecutar_hilo_vpn
        )
        self.sidebar_btn_vpn.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        # Botón 4: Novibet (Multicuenta)
        self.sidebar_btn_novibet = ctk.CTkButton(
            self.sidebar_frame, text="🎰 Ejecutar Novibet", fg_color="transparent", 
            text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", 
            height=40, font=btn_font, command=self.ejecutar_hilo_novibet
        )
        self.sidebar_btn_novibet.grid(row=4, column=0, padx=15, pady=6, sticky="ew")

        # Botón 5: Bonus
        self.sidebar_btn_bonus = ctk.CTkButton(
            self.sidebar_frame, text="🎁 Bonus", fg_color="transparent", 
            text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", 
            height=40, font=btn_font, command=self.click_bonus
        )
        self.sidebar_btn_bonus.grid(row=5, column=0, padx=15, pady=6, sticky="ew")

        # BOTÓN REEMPLAZADO: Corte Forzado de Emergencia
        self.sidebar_btn_cortar = ctk.CTkButton(
            self.sidebar_frame, text="🛑 Detener / Cortar Todo", fg_color="#D32F2F", 
            text_color="white", hover_color="#B71C1C", anchor="w", 
            height=42, font=btn_font, command=self.cortar_todo_forzado
        )
        self.sidebar_btn_cortar.grid(row=6, column=0, padx=15, pady=6, sticky="ew")

        # Botón de Pausa / Reanudar
        self.sidebar_btn_detener_iniciar = ctk.CTkButton(
            self.sidebar_frame, text="⏸️ Pausar / Esperar", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#FF9800", text_color="white", hover_color="#F57C00", anchor="w", 
            height=44, command=self.toggle_pausa_reanudar
        )
        self.sidebar_btn_detener_iniciar.grid(row=7, column=0, padx=15, pady=(15, 10), sticky="ew")

        # Selector de Tema
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=15, pady=(5, 15), sticky="ew")
        self.appearance_mode_optionemenu.set("Dark")

        # --- CONTENEDOR PRINCIPAL (DERECHA)[cite: 2] ---
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        # --- CONSOLA DE REGISTRO EN VIVO[cite: 2] ---
        self.frame_consola = ctk.CTkFrame(self.main_content_frame)
        self.frame_consola.grid(row=0, column=0, sticky="nsew")
        self.frame_consola.grid_columnconfigure(0, weight=1)
        self.frame_consola.grid_rowconfigure(1, weight=1)

        self.lbl_consola = ctk.CTkLabel(self.frame_consola, text="Consola de Registro en Vivo:", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_consola.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        self.consola = ctk.CTkTextbox(self.frame_consola, font=("Consolas", 12), fg_color="#080F14")
        self.consola.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Etiquetas de colores para la consola[cite: 2]
        self.consola.tag_config("cyan", foreground="#00E5FF")
        self.consola.tag_config("azul", foreground="#42A5F5")
        self.consola.tag_config("verde", foreground="#66BB6A")
        self.consola.tag_config("amarillo", foreground="#FFB74D")
        self.consola.tag_config("morado", foreground="#BA68C8")
        self.consola.tag_config("rojo", foreground="#FF5252")
        self.consola.tag_config("blanco", foreground="#E0E0E0")

        self.consola.configure(state="disabled")

        sys.stdout = TextRedirector(self.consola)
        sys.stderr = TextRedirector(self.consola)
        print(" -> [SISTEMA] Panel listo. Si el bot se congela, use '🛑 Detener / Cortar Todo'.")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def click_bonus(self):
        print("[INFO] Botón 'Bonus' presionado.")

    def cortar_todo_forzado(self):
        """Corta de raíz cualquier proceso abierto de Chrome y WhatsApp al instante."""
        print("\n==================================================")
        print(" [CORTE TOTAL] Deteniendo de emergencia todos los procesos...")
        print("==================================================")
        
        try:
            # Mata instancias de Chrome y de WhatsApp para liberar la pantalla de golpe
            subprocess.run("taskkill /f /im chrome.exe /t >nul 2>&1", shell=True)
            subprocess.run("taskkill /f /im chromedriver.exe /t >nul 2>&1", shell=True)
            subprocess.run("taskkill /f /im WhatsApp.exe /t >nul 2>&1", shell=True)
            
            # Asegura que el evento de pausa vuelva a su estado libre
            evento_pausa.set()
            self.sidebar_btn_detener_iniciar.configure(text="⏸️ Pausar / Esperar", fg_color="#FF9800", hover_color="#F57C00")

            print(" -> [OK] Procesos de navegador y aplicaciones liquidados exitosamente.")
            print(" -> [INFO] El sistema quedó liberado. Puede volver a iniciar cuando guste.")
        except Exception as e:
            print(f" -> [ERROR AL FORZAR CIERRE]: {e}")

    def toggle_pausa_reanudar(self):
        if evento_pausa.is_set():
            evento_pausa.clear()
            self.sidebar_btn_detener_iniciar.configure(text="▶️ Reanudar", fg_color="#66BB6A", hover_color="#43A047")
            print("\n[ADVERTENCIA] ⏸️ Proceso PAUSADO por el usuario. El bot quedará en espera...")
        else:
            evento_pausa.set()
            self.sidebar_btn_detener_iniciar.configure(text="⏸️ Pausar / Esperar", fg_color="#FF9800", hover_color="#F57C00")
            print("\n[INFO] ▶️ Proceso REANUDADO. Continuando donde iba...")

    def ejecutar_hilo_limpieza(self):
        def tarea():
            evento_pausa.wait()
            try:
                limpieza.ejecutar_limpieza_y_arranque()
            except Exception as e:
                print(f"[ERROR EN LIMPIEZA]: {e}")
        threading.Thread(target=tarea, daemon=True).start()

    def ejecutar_hilo_vpn(self):
        def tarea():
            evento_pausa.wait()
            try:
                asyncio.run(vpn_manager.main())
            except Exception as e:
                print(f"[ERROR EN VPN]: {e}")
        threading.Thread(target=tarea, daemon=True).start()

    def ejecutar_hilo_novibet(self):
        def tarea():
            evento_pausa.wait()
            print("\n[INICIO] Ejecutando automatización inteligente de Novibet...")
            try:
                asyncio.run(novibet_bot.flujo_secuencial_completo())
                print(" -> [FIN] Secuencia de cuentas finalizada.")
            except Exception as e:
                print(f" -> [ERROR CRÍTICO EN NOVIBET]: {e}")
        threading.Thread(target=tarea, daemon=True).start()

    def ejecutar_hilo_secuencia_total(self):
        def secuencia_maestra():
            try:
                print("\n==================================================")
                print("   INICIANDO SECUENCIA AUTOMÁTICA COMPLETA       ")
                print("==================================================")
                
                print("\n[PASO 1/3] Ejecutando Limpieza Total...")
                evento_pausa.wait()
                limpieza.ejecutar_limpieza_y_arranque()
                
                print("\n[INFO] Espera de 3 segundos...")
                import time
                time.sleep(3)

                print("\n[PASO 2/3] Configurando VPN...")
                evento_pausa.wait()
                asyncio.run(vpn_manager.main())

                print("\n[INFO] Espera de 3 segundos...")
                time.sleep(3)

                print("\n[PASO 3/3] Iniciando Novibet Bot...")
                evento_pausa.wait()
                asyncio.run(novibet_bot.flujo_secuencial_completo())

                print("\n==================================================")
                print("   ¡SECUENCIA TOTAL COMPLETADA CON ÉXITO!        ")
                print("==================================================")

            except Exception as e:
                print(f"\n[ERROR EN SECUENCIA TOTAL]: {e}")

        threading.Thread(target=secuencia_maestra, daemon=True).start()

if __name__ == "__main__":
    app = AppNovibetCTK()
    app.mainloop()
