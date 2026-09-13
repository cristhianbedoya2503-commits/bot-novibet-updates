import asyncio
import random
import time
import os
import subprocess
import pandas as pd
import openpyxl
import pyautogui
pyautogui.PAUSE = 0.001
import cv2
import numpy as np
import pyperclip
import io
from PIL import Image
from playwright.async_api import async_playwright


def leer_credenciales_excel():
    """Busca la primera cuenta pendiente (vacía o con 'Error') y devuelve sus credenciales."""
    try:
        df = pd.read_excel("credenciales.xlsx")
        
        # Si la columna 'Proceso' no existe, la creamos vacía
        if 'Proceso' not in df.columns:
            df['Proceso'] = ""
            df.to_excel("credenciales.xlsx", index=False)
            
        # Recorremos fila por fila buscando qué procesar
        for index, row in df.iterrows():
            estado = str(row.get('Proceso', '')).strip().lower()
            
            # Si está vacía (nan/'') o dice 'error', es una cuenta válida para procesar
            if estado == '' or estado == 'nan' or 'error' in estado:
                usuario = str(row['usuario'])
                contrasena = str(row['contrasena'])
                
                motivo = "Pendiente" if estado == '' or estado == 'nan' else "Reintento por Error previo"
                print(f" -> [EXCEL] Cuenta seleccionada ({motivo} - Fila {index + 2}): {usuario}")
                return usuario, contrasena
                
        print(" -> [EXCEL] No hay cuentas pendientes ni con errores por reintentar.")
        return None, None
        
    except Exception as e:
        print(f" -> [ERROR EXCEL] No se pudo leer el archivo 'credenciales.xlsx': {e}")
        return None, None

def actualizar_estado_cuenta(usuario_objetivo, nuevo_estado):
    """Busca al usuario en el Excel y actualiza su columna 'Proceso' con 'Procesada' o 'Error'."""
    try:
        ruta_excel = "credenciales.xlsx"
        wb = openpyxl.load_workbook(ruta_excel)
        ws = wb.active
        
        col_proceso = None
        col_usuario = None
        
        for col in range(1, ws.max_column + 1):
            header = str(ws.cell(row=1, column=col).value).strip().lower()
            if header == 'proceso':
                col_proceso = col
            elif header == 'usuario':
                col_usuario = col
                
        if not col_proceso or not col_usuario:
            print(" -> [ERROR EXCEL] No se encontraron las columnas 'usuario' o 'Proceso' en el archivo.")
            return

        for row in range(2, ws.max_row + 1):
            val_usuario = str(ws.cell(row=row, column=col_usuario).value).strip()
            if val_usuario == str(usuario_objetivo).strip():
                ws.cell(row=row, column=col_proceso).value = nuevo_estado
                wb.save(ruta_excel)
                print(f" -> [EXCEL] Cuenta {usuario_objetivo} actualizada en Excel como: [{nuevo_estado}]")
                return
                
    except Exception as e:
        print(f" -> [ERROR EXCEL] No se pudo actualizar el estado de la cuenta: {e}")
        return None


async def escribir_paso_a_paso(pagina, selector, texto):
    """Simula la escritura humana letra por letra con alta velocidad optimizada."""
    elemento = pagina.locator(selector).first
    await elemento.click()
    for letra in texto:
        # Velocidad optimizada: de 30 a 70 milisegundos por letra
        await pagina.keyboard.type(letra, delay=random.randint(30, 70))

async def cerrar_ventanas_emergentes(pagina):
    """Función defensiva rápida para cerrar pop-ups si aparecen."""
    print(" -> [LIMPIEZA] Verificando ventanas emergentes...")
    await asyncio.sleep(1) # Pausa rápida
    
    try:
        btn_cierre_bienvenida = pagina.locator("cm-icon[name='close'], button:has(cm-icon[name='close']), .registerOrLogin_closeButtonIcon").first
        if await btn_cierre_bienvenida.is_visible(timeout=1500):
            await btn_cierre_bienvenida.click(force=True)
            print("   -> Ventana de bienvenida inicial cerrada ('X').")
            await asyncio.sleep(0.5)
    except Exception:
        pass

    try:
        btn_no_gracias = pagina.locator("button:has-text('No, gracias'), button:has-text('No gracias'), div:has-text('No, gracias')").first
        if await btn_no_gracias.is_visible(timeout=1000):
            await btn_no_gracias.click(force=True)
            print("   -> Notificación cerrada ('No, gracias').")
            await asyncio.sleep(0.5)
    except Exception:
        pass

    try:
        btn_x = pagina.locator("button.dialog-close, button[aria-label*='Close' i], .modal-close, button:has-text('✕')").first
        if await btn_x.is_visible(timeout=1000):
            await btn_x.click(force=True)
            print("   -> Pop-up central cerrado.")
            await asyncio.sleep(0.5)
    except Exception:
        pass

    try:
        btn_tooltip = pagina.locator("text='Lo entiendo', text='Entendido'").first
        if await btn_tooltip.is_visible(timeout=1000):
            await btn_tooltip.click(force=True)
            print("   -> Tooltip superior cerrado.")
            await asyncio.sleep(0.5)
    except Exception:
        pass

    try:
        btn_cookies = pagina.locator("button:has-text('Aceptar'), button:has-text('Acepto')").first
        if await btn_cookies.is_visible(timeout=1000):
            await btn_cookies.click(force=True)
            print("   -> Aviso de cookies aceptado.")
            await asyncio.sleep(0.5)
    except Exception:
        pass

async def flujo_secuencial_completo():
    print("==================================================")
    print("   SECUENCIA RÁPIDA: ENLACE + LOGIN + PAGO")
    print("==================================================")

    # ---> CAMBIA AQUÍ A "spei" O "mercadopago" SEGÚN LO QUE NECESITES <---
    METODO_PAGO = "mercadopago" 

    
    usuario, contrasena = leer_credenciales_excel()
    if not usuario or not contrasena:
        print("[EXCEL] No hay más cuentas pendientes ni con errores por procesar. Finalizando bot.")
        return

    URL_INICIAL = "https://www.novibet.mx/casino?promocode=NOVI300&bannerId=NOVI300NEW_MX&aff=2475&cq_src=google_ads&cq_cmp=22367301481&cq_con=173669306541&cq_term=novibet%20casino&cq_med=&cq_plac=&cq_net=g&cq_plt=gp&gad_source=1&gad_campaignid=22367301481&gbraid=0AAAAADNTZsBuqqITkv4MFcNhqwNdZUGUe&gclid=EAIaIQobChMIyZ6LmODSlgMVLivUAR3IuyWZEAAYASAAEgJ5OvD_BwE"

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            contexto = browser.contexts[0]
            pagina = contexto.pages[0] if contexto.pages else await contexto.new_page()

            print("\n[INFO] Abriendo el enlace principal de Novibet...")
            await pagina.goto(URL_INICIAL)
            # Cambiamos domcontentloaded por networkidle o esperas de elementos para asegurar renderizado completo
            await pagina.wait_for_load_state("load")
            
            await cerrar_ventanas_emergentes(pagina)

            # Bucle general de reintentos para todo el bloque de inicio de sesión (Pasos 1 al 4)
            hacer_proceso_recarga = True
            exito_login_total = False
            
            for intento_general in range(3):
                try:
                    if intento_general > 0:
                        print(f"\n[REINTENTO] Recargando página y repitiendo desde el Paso 1 (Intento {intento_general + 1}/3)...")
                        await pagina.reload()
                        await asyncio.sleep(4)

                    # [PASO 1] Iniciar Sesión
                    print("\n[PASO 1] Buscando y haciendo clic en el menú 'INICIAR SESIÓN'...")
                    await cerrar_ventanas_emergentes(pagina)
                    boton_login_menu = pagina.locator("div.headerMenuAnonymous_buttonText:visible").filter(has_text="Iniciar sesión").first
                    await boton_login_menu.wait_for(state="visible", timeout=10000)
                    await boton_login_menu.click()
                    print(" -> [OK] Clic exitoso en el menú superior.")

                    # [PASO 2] Usuario rápido
                    print("\n[PASO 2] Escribiendo el usuario...")
                    await cerrar_ventanas_emergentes(pagina)
                    campo_usuario = pagina.locator("input[type='text'], input[type='email']").first
                    await campo_usuario.wait_for(state="visible", timeout=20000)
                    await escribir_paso_a_paso(pagina, "input[type='text'], input[type='email']", usuario)
                    print(" -> [OK] Usuario escrito con velocidad optimizada.")

                    # [PASO 3] Contraseña rápida
                    print("\n[PASO 3] Escribiendo la contraseña...")
                    campo_password = pagina.locator("input[type='password']").first
                    await campo_password.wait_for(state="visible", timeout=20000)
                    await escribir_paso_a_paso(pagina, "input[type='password']", contrasena)
                    print(" -> [OK] Contraseña escrita con velocidad optimizada.")

                    # [PASO 4] Clic botón verde acceso
                    print("\n[PASO 4] Haciendo clic en el botón verde de acceso...")
                    boton_enviar = pagina.locator("button:has-text('Iniciar sesión'), div:has-text('Iniciar sesión')").last
                    await boton_enviar.wait_for(state="visible", timeout=15000)
                    await boton_enviar.click()
                    print(" -> [OK] ¡Clic final de acceso realizado!")

                    # Espera inteligente a que la sesión cargue tras el login
                    try:
                        await pagina.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    await cerrar_ventanas_emergentes(pagina)

                    # =========================================================================
                    # [PASO 4.1] Verificación anticipada de saldo tras el login
                    # =========================================================================
                    print("\n[PASO 4.1] Verificando saldo actual en la plataforma...")
                    try:
                        elemento_saldo = pagina.locator("text=/\\$[0-9,.]+/").first
                        await elemento_saldo.wait_for(state="visible", timeout=5000)
                        texto_saldo = await elemento_saldo.inner_text()

                        saldo_limpio = float(texto_saldo.replace('$', '').replace(',', '').strip())
                        print(f" -> Saldo detectado en pantalla: {saldo_limpio}")

                        if saldo_limpio > 0.00:
                            print(" -> [AVISO] El saldo es superior a 0.00. Omitiendo pasos de recarga...")
                            hacer_proceso_recarga = False
                        else:
                            print(" -> Saldo en 0.00. Continuando con el flujo normal de recarga...")
                            hacer_proceso_recarga = True
                                                        
                    except Exception as e:
                        print(f" -> [AVISO] No se pudo leer el saldo automáticamente ({e}). Continuando flujo normal...")
                        hacer_proceso_recarga = True

                    exito_login_total = True
                    break

                except Exception as e:
                    print(f" -> [AVISO] El proceso de inicio de sesión falló en este intento. Preparando reintento...")
                    await asyncio.sleep(2)

            if not exito_login_total:
                raise Exception("No se pudo completar el inicio de sesión tras agotar los 3 reintentos.")

            # =========================================================================
            # FLUJO CONDICIONAL: Si hay saldo (hacer_proceso_recarga = False), se omite del 5 al 12
            # =========================================================================
            if hacer_proceso_recarga:
                             
                      
            # [PASO 5] Extracción de datos con espera inteligente y dinámica
                exito_paso5 = False
                nombre_completo_cliente = ""
                
                for intento_p5 in range(3):
                    try:
                        print(f"\n[PASO 5] Extrayendo datos de la cuenta (Intento {intento_p5 + 1}/3)...")
                        
                        pagina_pago = pagina
                        
                        await pagina_pago.goto("https://www.novibet.mx/useraccount/settings", timeout=30000)
                        await pagina_pago.wait_for_load_state("domcontentloaded")
                        
                        nombre_cliente = ""
                        apellido_cliente = ""
                        
                        # Bucle inteligente: revisa cada 0.4 segundos (hasta por 8 segundos máximo).
                        # Tan pronto como el texto aparezca en pantalla, rompe el bucle de inmediato.
                        for _ in range(20):
                            try:
                                nombre_cliente = await pagina_pago.locator("text='Nombre' >> xpath=following-sibling::*").inner_text(timeout=400)
                                apellido_cliente = await pagina_pago.locator("text='Apellido' >> xpath=following-sibling::*").inner_text(timeout=400)
                                
                                nombre_cliente = nombre_cliente.strip() if nombre_cliente else ""
                                apellido_cliente = apellido_cliente.strip() if apellido_cliente else ""
                                
                                if len(nombre_cliente) > 1 and len(apellido_cliente) > 1:
                                    break # ¡Los datos ya cargaron! Avanzamos al instante
                            except Exception:
                                pass
                            await asyncio.sleep(0.4)
                        
                        nombre_completo_cliente = f"{nombre_cliente} {apellido_cliente}".strip()
                        
                        if not nombre_completo_cliente or len(nombre_completo_cliente) < 3:
                            raise Exception("Los datos tardaron en aparecer en este intento.")
                            
                        print(f" -> [OK] Nombre real extraído al instante: {nombre_completo_cliente}")

                        print(" -> Redirigiendo a la pasarela de depósitos...")
                        await pagina_pago.goto("https://www.novibet.mx/useraccount/deposit", timeout=30000)
                        await pagina_pago.wait_for_load_state("domcontentloaded")
                        await asyncio.sleep(2)
                        
                        exito_paso5 = True
                        break
                        
                    except Exception as e:
                        print(f" -> [AVISO] Reintentando extracción... ({e})")
                        await asyncio.sleep(1)
                
                if not exito_paso5:
                    raise Exception("No se pudo completar la extracción de datos tras 3 intentos.")   
                
                # Bucle general de reintentos para los pasos del 6 al 11
                exito_flujo_pago = False
                
                for intento_general_pago in range(3):
                    try:
                        if intento_general_pago > 0:
                            print(f"\n[REINTENTO] El flujo de pago falló. Recargando pasarela y reintentando (Intento {intento_general_pago + 1}/3)...")
                            await pagina_pago.goto("https://www.novibet.mx/useraccount/deposit", timeout=30000)
                            await pagina_pago.wait_for_load_state("domcontentloaded")
                            await asyncio.sleep(2)

                        # [PASO 6] Seleccionando método de pago con espera dinámica inteligente
                        print(f"\n[PASO 6] Seleccionando método de pago: {METODO_PAGO.upper()}...")
                        
                        try:
                            await pagina_pago.locator("div.payment-methods, .payment-container, form").first.wait_for(state="visible", timeout=10000)
                        except Exception:
                            pass
                        
                        if METODO_PAGO == "mercadopago":
                            tarjeta_mp = pagina_pago.locator(".mercadopagowallet, img[src*='mercadopago']").first
                            await tarjeta_mp.wait_for(state="visible", timeout=15000)
                            await tarjeta_mp.click(force=True)
                            print(" -> [OK] Mercado Pago seleccionado.")
                            
                        elif METODO_PAGO == "spei":
                            opcion_spei = pagina_pago.locator("text='SPEI'").first
                            if not await opcion_spei.is_visible(timeout=3000):
                                opcion_spei = pagina_pago.locator("text='Transferencia'").first
                            
                            await opcion_spei.wait_for(state="visible", timeout=15000)
                            await opcion_spei.click(force=True)
                            print(" -> [OK] SPEI seleccionado.")

                        # [PASO 7] Escribir cantidad (80)
                        print("\n[PASO 7] Escribiendo la cantidad de depósito (80)...")
                        await asyncio.sleep(1)
                        
                        campo_cantidad = pagina_pago.locator("input[type='text'], input[type='number'], input").filter(has_not=pagina_pago.locator("input[type='hidden']")).first
                        await campo_cantidad.wait_for(state="visible", timeout=10000)
                        
                        await campo_cantidad.click()
                        for digito in "80":
                            await pagina_pago.keyboard.type(digito, delay=random.randint(30, 70))
                        print(" -> [OK] Cantidad escrita rápidamente.")

                        # [PASO 8] Botón Continuar
                        print("\n[PASO 8] Dando clic en 'Continuar'...")
                        await asyncio.sleep(0.5)
                        
                        boton_continuar = pagina_pago.locator("button:has-text('Continuar'), div:has-text('Continuar')").last
                        await boton_continuar.wait_for(state="visible", timeout=10000)
                        await boton_continuar.click(force=True)
                        print(" -> [OK] Continuar presionado.")

                        # [PASO 9 y 10] Flujo específico según el método elegido y captura
                        if METODO_PAGO == "mercadopago":
                            print("\n[PASO 9] Seleccionando 'Usar la app de Mercado Pago'...")
                            await asyncio.sleep(1)
                            opcion_qr = pagina_pago.locator("text=Usar la app de Mercado Pago").first
                            await opcion_qr.wait_for(state="visible", timeout=15000)
                            await opcion_qr.click(force=True)
                            
                            print("\n[PASO 10] Capturando el código QR...")
                            await asyncio.sleep(2.5)
                            ruta_screenshot_pago = "qr_mercadopago.png"
                            
                        elif METODO_PAGO == "spei":
                            print("\n[PASO 10] Esperando a que carguen los datos de SPEI...")
                            await asyncio.sleep(4)
                            ruta_screenshot_pago = "datos_spei.png"
                        
                        await pagina_pago.screenshot(path=ruta_screenshot_pago)
                        print(f" -> [OK] Captura de pago guardada como '{ruta_screenshot_pago}'.")

                        # =========================================================================
                        # [PASO 11] WhatsApp Desktop: Copiar imagen, enviar con texto y cerrar app
                        # =========================================================================
                        print("\n[PASO 11] Enviando información por WhatsApp Desktop...")

                        contacto_destino = "Cargas"  
                        archivo_pago = "qr_mercadopago.png" if METODO_PAGO == "mercadopago" else "datos_spei.png"

                        print(f" -> Destino: {contacto_destino}")
                        print(f" -> Método de pago: {METODO_PAGO} (Archivo: {archivo_pago})")
                        print(f" -> Cliente: {nombre_completo_cliente}")

                        # 1. Abrir la aplicación de WhatsApp de Escritorio
                        print(" -> Abriendo la aplicación de WhatsApp...")
                        subprocess.run(["start", "whatsapp://"], shell=True)
                        time.sleep(4.0)  # Esperar a que la app abra y enfoque

                        # 2. Buscar el chat en la barra de búsqueda de WhatsApp
                        print(f" -> Buscando el chat de: {contacto_destino}")
                        pyautogui.hotkey('ctrl', 'f')
                        time.sleep(1.0)
                        
                        pyperclip.copy(contacto_destino)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(1.5)
                        
                        pyautogui.press('enter')
                        time.sleep(2.0)  # Esperar a que abra el chat

                        # 3. Copiar la imagen como archivo real usando PowerShell (Sin errores de win32clipboard)
                        if not os.path.exists(archivo_pago):
                            print(f" -> [ADVERTENCIA] El archivo {archivo_pago} no se encuentra. Creando imagen temporal...")
                            with open(archivo_pago, "wb") as f:
                                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82')

                        ruta_absoluta = os.path.abspath(archivo_pago)
                        print(f" -> Copiando la imagen al portapapeles de Windows: {archivo_pago}")
                        
                        # Comando nativo de Windows para copiar el archivo de imagen de forma limpia
                        comando_ps = f"powershell -command \"Set-Clipboard -Path '{ruta_absoluta}'\""
                        subprocess.run(comando_ps, shell=True)
                        time.sleep(1.5)

                        # 4. Pegar la imagen en el chat (Abre la previsualización con pie de foto)
                        print(" -> Pegando la imagen en el chat con Ctrl + V...")
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(2.5)  # Dar tiempo a que cargue la previsualización

                        # 5. Escribir el nombre del cliente como pie de foto de la imagen
                        print(" -> Escribiendo el nombre del cliente como pie de foto...")
                        mensaje_texto = f"Cliente: {nombre_completo_cliente}"
                        pyperclip.copy(mensaje_texto)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(1.0)

                        # 6. Enviar todo presionando Enter
                        print(" -> Enviando el mensaje completo (imagen + texto)...")
                        pyautogui.press('enter')
                        time.sleep(1.0)  # Breve pausa para que procese el envío

                        # 7. CIERRE FORZADO E INFALIBLE USANDO POWERSHELL Y TASKKILL
                        print(" -> Cerrando la aplicación de WhatsApp para liberar la pantalla...")
                        
                        # Método A: Forzar cierre por nombre exacto con comodines de proceso
                        subprocess.run("taskkill /f /im WhatsApp.exe /t >nul 2>&1", shell=True)
                        
                        # Método B: Matar el proceso mediante PowerShell por si quedó suspendido en la tienda
                        subprocess.run("powershell -command \"Stop-Process -Name 'WhatsApp' -Force -ErrorAction SilentlyContinue\"", shell=True)
                        
                        # Método C: Por si acaso tuviera el foco, enviamos Alt + F4 para cerrarla visualmente de golpe
                        pyautogui.hotkey('alt', 'f4')
                        
                        time.sleep(1.5)  # Pausa para asegurar que la pantalla quede limpia

                        print(f" -> [OK] Captura de {METODO_PAGO} y nombre enviados, y WhatsApp cerrado por completo.")

                        # Si todo salió bien, marcamos el éxito para romper el ciclo de reintentos
                        exito_flujo_pago = True
                        break

                    except Exception as e:
                        print(f" -> [AVISO] Ocurrió un error en el bloque de pago (Intento {intento_general_pago + 1}): {e}")
                        await asyncio.sleep(3)

                if not exito_flujo_pago:
                    raise Exception("No se pudo completar el flujo de pago y reporte tras agotar los 3 reintentos.")
                
                # --- RETORNO A LA PÁGINA PRINCIPAL PARA EL MONITOREO ---
                print("\n[INFO] Regresando a la página principal para iniciar el monitoreo de saldo...")
                await pagina.goto(URL_INICIAL, timeout=30000)
                await pagina.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3) 

                # [PASO 12] Monitoreo inteligente del saldo en la pestaña principal
                print("\n[PASO 12] Iniciando monitoreo de saldo acreditado...")
                
                # Aseguramos que nos ubicamos en la pestaña principal donde está la interfaz
                await pagina.bring_to_front()
                
                # 1. Clic inicial en el icono del muñequito para desplegar el panel del saldo
                print(" -> Haciendo clic en el icono del perfil (muñequito)...")
                try:
                    muñequito = pagina.locator("cm-icon[name='user-outline'], button:has(cm-icon[name='user-outline'])").first
                    await muñequito.wait_for(state="visible", timeout=10000)
                    await muñequito.click(force=True)
                    print(" -> [OK] Menú de usuario desplegado.")
                except Exception as e:
                    print(f" -> [AVISO] No se pudo hacer clic automático en el muñequito: {e}")
                
                await asyncio.sleep(2)
                
                # Capturamos el saldo inicial de referencia
                try:
                    elemento_saldo = pagina.locator("div.headerMenuAuthenticated_balance, .balance-amount").first
                    await elemento_saldo.wait_for(state="visible", timeout=10000)
                    saldo_inicial = (await elemento_saldo.inner_text()).strip()
                except Exception:
                    saldo_inicial = "$0.00"
                    
                print(f" -> [OK] Saldo inicial de referencia: {saldo_inicial}. Monitoreando cambios cada 30 segundos...")
                
                saldo_acreditado = False
                tiempo_maximo_espera = 600  # Tiempo límite de espera (10 minutos máximo)
                tiempo_transcurrido = 0
                
                while tiempo_transcurrido < tiempo_maximo_espera:
                    try:
                        # 2. Hacer clic en el botón de recargar (la bolita con flecha circular)
                        print(" -> Haciendo clic en el botón de recargar saldo...")
                        btn_recargar = pagina.locator("button:has(svg), svg path[d*='M'], .fa-redo, .fa-sync").last
                        await btn_recargar.click(timeout=5000)
                    except Exception:
                        try:
                            # Respaldo buscando el botón de refresco cerca de "Saldo total"
                            await pagina.locator("text='Saldo total' >> xpath=following::button[1]").click(timeout=3000)
                        except Exception:
                            pass
                    
                    # Breve pausa para que la plataforma procese la actualización
                    await asyncio.sleep(3)
                    
                    try:
                        current_saldo = (await elemento_saldo.inner_text()).strip()
                        print(f" -> [MONITOREO] Saldo actual en pantalla: {current_saldo}")
                        
                        # Limpiamos el texto del saldo para extraer solo números y evaluar si es mayor a 0.00
                        # Esto remueve símbolos como '$', comas, etc., para convertirlo a float de forma segura
                        saldo_limpio = current_saldo.replace('$', '').replace(',', '').strip()
                        
                        # Intentamos convertir el valor a float para una comparación numérica exacta
                        valor_numerico = float(saldo_limpio) if saldo_limpio else 0.0
                        
                        # Si el saldo es superior a 0.00 o cambió respecto al inicial
                        if valor_numerico > 0.0 or (current_saldo != saldo_inicial and "$0.00" not in current_saldo and "0.00" not in current_saldo):
                            print("\n" + "="*50)
                            print(f" ¡ALERTA! ¡EL SALDO HA SIDO ACREDITADO A {current_saldo}!")
                            print("="*50 + "\n")
                            saldo_acreditado = True
                            break # Rompe el ciclo del monitor y pasa de inmediato al Paso 13
                            
                    except Exception as e:
                        print(f" -> [AVISO] Error leyendo o parseando el saldo en este ciclo: {e}")
                    
                    # Esperar 30 segundos antes de la siguiente verificación
                    await asyncio.sleep(30)
                    tiempo_transcurrido += 30

                if not saldo_acreditado:
                    print("\n[AVISO] Se agotó el tiempo de espera de los 10 minutos y el saldo no cambió automáticamente.")
                
            # [PASO 13] Navegación directa a la URL del juego omitiendo los pasos anteriores
            url_juego = "https://www.novibet.mx/casino/juego/playtech/age-of-the-gods-god-of-storms-iii"
            print(f"\n[PASO DIRECTO] Navegando directamente al juego:\n{url_juego}")
            await pagina.goto(url_juego, wait_until="domcontentloaded")
            await asyncio.sleep(4)

            # [PASO 14] Ventanas emergentes previas / carga inicial
            print("\n[VERIFICACIÓN] Esperando carga inicial y pantallas emergentes...")

            async def descartar_tooltip_informativo():
                try:
                    btn_lo_entiendo = pagina.locator("text='Lo entiendo'").first
                    if await btn_lo_entiendo.is_visible(timeout=1500):
                        await btn_lo_entiendo.click(force=True)
                        print(" -> [OK] Tooltip 'Lo entiendo' detectado y cerrado.")
                        await asyncio.sleep(1)
                except:
                    pass

            async def cerrar_modal_lucky_rush():
                print("\n[VERIFICACIÓN] Buscando ventana modal o publicidad ('Lucky Rush', 'No, gracias', 'X')...")
                cerrado_exitoso = False
                entornos_a_buscar = [pagina] + pagina.frames

                for entorno in entornos_a_buscar:
                    try:
                        btn_no_gracias = entorno.locator("text='No, gracias'").first
                        if await btn_no_gracias.is_visible(timeout=1500):
                            await btn_no_gracias.click(force=True)
                            print(" -> [OK] ¡Publicidad/Modal cerrada haciendo clic en 'No, gracias'!")
                            cerrado_exitoso = True
                            break

                        btn_cerrar_x = entorno.locator("button:has(svg), [class*='close'], [aria-label*='Close']").first
                        if await btn_cerrar_x.is_visible(timeout=1000):
                            await btn_cerrar_x.click(force=True)
                            print(" -> [OK] ¡Publicidad/Modal cerrada haciendo clic en la 'X'!")
                            cerrado_exitoso = True
                            break
                    except:
                        continue

                if not cerrado_exitoso:
                    try:
                        await pagina.get_by_text("No, gracias").click(timeout=2000)
                        print(" -> [OK] ¡Modal cerrada usando selector de respaldo de Playwright!")
                        cerrado_exitoso = True
                    except:
                        pass

                if not cerrado_exitoso:
                    print(" -> [INFO] No hay modales activas en este momento.")
                await asyncio.sleep(1)

            await descartar_tooltip_informativo()

            # --- BARRIDO DINÁMICO UNIFICADO (OK -> ACEPTAR -> USAR AHORA) ---
            print("\n[VERIFICACIÓN] Escaneando pantallas emergentes ('OK', 'Aceptar', 'Usar ahora')...")

            entornos_juego = [pagina] + pagina.frames
            paso_completado = False

            # Intentamos durante varios ciclos cortos para darle tiempo al casino de renderizar sin volverse lento
            for intento in range(15):
                detectado_en_ciclo = False
                
                for entorno in entornos_juego:
                    try:
                        # 1. Buscar ventana 'OK'
                        btn_ok = entorno.locator("text='OK'").first
                        if await btn_ok.is_visible(timeout=200):
                            await btn_ok.click(force=True)
                            print(f" -> [OK] Ventana 'OK' detectada y presionada (Intento #{intento + 1}).")
                            detectado_en_ciclo = True
                            await asyncio.sleep(1.0)
                            break
                        
                        # 2. Buscar botón 'Aceptar'
                        btn_aceptar = entorno.locator("text='Aceptar'").first
                        if await btn_aceptar.is_visible(timeout=200):
                            await btn_aceptar.click(force=True)
                            print(f" -> [OK] Botón 'Aceptar' detectado y presionado (Intento #{intento + 1}).")
                            detectado_en_ciclo = True
                            await asyncio.sleep(1.0)
                            break
                            
                        # 3. Buscar botón 'Usar ahora'
                        btn_usar = entorno.locator("text='Usar ahora'").first
                        if await btn_usar.is_visible(timeout=200):
                            await btn_usar.click(force=True)
                            print(f" -> [OK] Botón 'Usar ahora' detectado y presionado (Intento #{intento + 1}).")
                            detectado_en_ciclo = True
                            await asyncio.sleep(1.0)
                            break
                    except:
                        continue
                        
                if detectado_en_ciclo:
                    # Damos un respiro corto por si aparece otro cartel consecutivo
                    await asyncio.sleep(0.5)
                    continue
                
                # Si en este intento no vio nada, esperamos un pelito antes del siguiente ciclo
                await asyncio.sleep(0.3)

            print(" -> [INFO] Secuencia de pantallas emergentes previas finalizada. Continuando con el juego...")

            # ==========================================
            # PASO 15: Búsqueda obligatoria, persistente e infinita de "Aceptar" y "Usar ahora"
            # ==========================================
            print("\n[BUSCANDO] Vigilancia activa: Buscando botones emergentes ('Aceptar' / 'Usar ahora')...")
            clicked_usar = False
            intento_15 = 0

            while not clicked_usar:
                intento_15 += 1
                try:
                    # Descartar cualquier tooltip o ventana estorbosa que aparezca
                    await descartar_tooltip_informativo()
                    
                    # Recorrer los iframes del juego buscando primero el botón "Aceptar" del bono y luego "Usar ahora"
                    for frame in pagina.frames:
                        try:
                            # 1. Verificar si aparece el botón "Aceptar" del modal de giros gratis
                            btn_aceptar = frame.locator("text=/Aceptar/i").first
                            if await btn_aceptar.is_visible(timeout=200):
                                await btn_aceptar.click(force=True)
                                print(f"\n -> [OK] ¡Botón 'Aceptar' detectado y presionado (en el intento #{intento_15})!")
                                await asyncio.sleep(1.0)
                                break # Rompe el loop de frames para continuar buscando el siguiente paso

                            # 2. Buscar el botón "Usar ahora"
                            btn_frame = frame.locator("text=/Usar ahora/i").first
                            if await btn_frame.is_visible(timeout=500):
                                await btn_frame.click(force=True)
                                print(f"\n -> [OK] ¡Clic exitoso y obligatorio en 'Usar ahora' (en el intento #{intento_15})!")
                                clicked_usar = True
                                break
                        except Exception:
                            continue
                            
                    if clicked_usar:
                        break

                except Exception:
                    pass

                # Mostrar aviso cada 10 intentos para ver que sigue trabajando sin salirse
                if intento_15 % 10 == 0:
                    print(f" -> [ESPERANDO] El bot sigue buscando los botones de acceso... (Intento #{intento_15})")

                await asyncio.sleep(1)

            print("[INFO] Botón final presionado con éxito. Avanzando al siguiente paso.")


            # =========================================================
            # PASO 16: Búsqueda visual del botón "CONTINUAR" con doble clic directo
            # =========================================================
            print("\n[ESPERANDO] Buscando visualmente el botón 'CONTINUAR'...")
            clic_visual_exitoso = False
            tiempo_limite_v = 30
            intentos_totales = tiempo_limite_v * 2

            for intento in range(intentos_totales):
                try:
                    await descartar_tooltip_informativo()
                    ubicacion = pyautogui.locateOnScreen("boton_continuar.png", confidence=0.8)

                    if ubicacion:
                        centro_x, centro_y = pyautogui.center(ubicacion)
                        
                        # Ejecutamos doble clic inmediato y seguro sobre el botón encontrado
                        pyautogui.click(centro_x, centro_y)
                        time.sleep(0.1)
                        pyautogui.click(centro_x, centro_y)
                        
                        print(f"\n -> [OK] Doble clic aplicado en 'CONTINUAR' en ({centro_x}, {centro_y}).")
                        clic_visual_exitoso = True
                        break
                except Exception:
                    pass

                await asyncio.sleep(0.5)
                segundos_transcurridos = (intento + 1) / 2
                print(f" -> [CARGANDO] El juego está cargando... ({segundos_transcurridos:.1f}s)", end="\r")

            if not clic_visual_exitoso:
                print("\n -> [AVISO] Se agotó el tiempo de espera para el botón 'Continuar', procediendo...")
            else:
                print("\n[INFO] ¡Pantalla de juego cargada y confirmada con éxito!")
            
            # =========================================================
            # [PASO 17] Bucle de giros gratis con lectura por plantillas y control de velocidad
            # =========================================================
            print("\n[LECTURA] Publicidades cerradas. Leyendo contador de giros por plantillas...")
            await asyncio.sleep(1)

            carpeta_plantillas = "numeros"
            plantillas = {}
            
            for i in range(10):
                ruta = os.path.join(carpeta_plantillas, f"{i}.png")
                if os.path.exists(ruta):
                    img_temp = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
                    if img_temp is not None:
                        plantillas[i] = cv2.resize(img_temp, (20, 30))
                        
            giros_restantes_leidos = 300

            if not plantillas:
                print(f"\n -> [ERROR] No se encontraron plantillas en la carpeta '{carpeta_plantillas}'.")
            else:
                intentos_lectura = 0
                while intentos_lectura < 5:
                    intentos_lectura += 1
                    captura = pyautogui.screenshot()
                    imagen_np = np.array(captura)
                    imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
                    alto_p, ancho_p, _ = imagen_bgr.shape
                    
                    y1, y2, x1, x2 = int(alto_p * 0.88), int(alto_p * 0.98), int(ancho_p * 0.55), int(ancho_p * 0.70)
                    recorte = imagen_bgr[y1:y2, x1:x2]
                    
                    hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
                    lower_orange = np.array([5, 150, 150])
                    upper_orange = np.array([25, 255, 255])
                    mascara = cv2.inRange(hsv, lower_orange, upper_orange)
                    
                    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    cajas = []
                    for c in contornos:
                        x, y, w, h = cv2.boundingRect(c)
                        if h > 8:
                            cajas.append((x, y, w, h))
                            
                    cajas = sorted(cajas, key=lambda item: item[0])
                    digitos_detectados = []
                    
                    for idx_dig, (x, y, w, h) in enumerate(cajas):
                        digito_img = mascara[y:y+h, x:x+w]
                        digito_std = cv2.resize(digito_img, (20, 30))
                        
                        mejor_puntaje = -1
                        mejor_digito = None
                        
                        for num, plantilla in plantillas.items():
                            resultado = cv2.matchTemplate(digito_std, plantilla, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(resultado)
                            
                            if max_val > mejor_puntaje:
                                mejor_puntaje = max_val
                                mejor_digito = num
                                
                        if mejor_digito is not None:
                            digitos_detectados.append(str(mejor_digito))

                    if digitos_detectados:
                        giros_restantes_leidos = int("".join(digitos_detectados))
                        print(f" -> Giros detectados en pantalla: {giros_restantes_leidos}")
                        break
                    else:
                        print(" -> [AVISO] No se detectaron dígitos. Verificando si hay modales estorbando...")
                        
                        # Barrido rápido anti-modales antes de rendirse
                        modal_limpiado = False
                        for _ in range(3):
                            for entorno in [pagina] + pagina.frames:
                                try:
                                    btn_no = entorno.locator("text='No, gracias', text='No gracias'").first
                                    if await btn_no.is_visible(timeout=150):
                                        await btn_no.click(force=True)
                                        print(" -> [OK] Modal cerrado por 'No, gracias'.")
                                        modal_limpiado = True
                                        break
                                    
                                    btn_x = entorno.locator("button.dialog-close, [class*='close' i], [aria-label*='Close' i], button:has(svg)").first
                                    if await btn_x.is_visible(timeout=150):
                                        await btn_x.click(force=True)
                                        print(" -> [OK] Modal cerrado haciendo clic en la 'X'.")
                                        modal_limpiado = True
                                        break
                                except:
                                    continue
                            if modal_limpiado:
                                break
                            await asyncio.sleep(0.2)
                        
                        if modal_limpiado:
                            print(" -> [INFO] Modal limpiado con éxito. Reintentando la lectura de giros...")
                            await asyncio.sleep(1.5)
                        else:
                            await asyncio.sleep(0.5)

            # =========================================================
            # PASO 18: Bucle principal de ejecución de giros con lectura inteligente
            # =========================================================
            giros_totales = giros_restantes_leidos
            giros_restantes_actual = giros_totales

            print(f"\n[INICIO DE RONDA] Ejecutando {giros_totales} giros en total...")

            while giros_restantes_actual > 0:
                # --- BARRIDO PRIORITARIO ANTI-TORNEO / PUBLICIDAD ---
                try:
                    for entorno in [pagina] + pagina.frames:
                        try:
                            btn_later = entorno.locator("text=/Maybe Later/i, text=/Más tarde/i, button:has-text('Maybe Later')").first
                            if await btn_later.is_visible(timeout=150):
                                await btn_later.click(force=True)
                                print(" -> [OK] ¡Torneo central 'Grito de Fortuna' cerrado!")
                                await asyncio.sleep(0.5)
                                break
                        except:
                            continue
                    btn_notif = pagina.locator("text='No, gracias', text='No gracias'").first
                    if await btn_notif.is_visible(timeout=150):
                        await btn_notif.click(force=True)
                        print(" -> [OK] Notificación superior cerrada.")
                except:
                    pass

                encontrado = False
                intentos_espera = 0
                max_intentos_espera = 20
                
                while not encontrado and intentos_espera < max_intentos_espera:
                    try:
                        ubicacion_grande = pyautogui.locateOnScreen("boton_free_spins.png", confidence=0.75)
                        if ubicacion_grande:
                            centro_x, centro_y = pyautogui.center(ubicacion_grande)
                            for _ in range(5):
                                pyautogui.click(centro_x, centro_y)
                                time.sleep(0.01)
                            encontrado = True
                    except:
                        pass
                    
                    if not encontrado:
                        intentos_espera += 1
                        await asyncio.sleep(0.15)
                
                if encontrado:
                    # Esperamos un momento a que el giro se procese en la pantalla
                    await asyncio.sleep(1.2)
                    print(" -> [RE-LECTURA] Leyendo giros restantes reales desde la pantalla...")
                    
                    giros_anterior = giros_restantes_actual
                    
                    captura_nueva = pyautogui.screenshot()
                    imagen_np_n = np.array(captura_nueva)
                    imagen_bgr_n = cv2.cvtColor(imagen_np_n, cv2.COLOR_RGB2BGR)
                    alto_pn, ancho_pn, _ = imagen_bgr_n.shape
                    y1_n, y2_n, x1_n, x2_n = int(alto_pn * 0.88), int(alto_pn * 0.98), int(ancho_pn * 0.55), int(ancho_pn * 0.70)
                    recorte_n = imagen_bgr_n[y1_n:y2_n, x1_n:x2_n]
                    
                    hsv_n = cv2.cvtColor(recorte_n, cv2.COLOR_BGR2HSV)
                    mascara_n = cv2.inRange(hsv_n, lower_orange, upper_orange)
                    contornos_n, _ = cv2.findContours(mascara_n, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    cajas_n = []
                    for cn in contornos_n:
                        xn, yn, wn, hn = cv2.boundingRect(cn)
                        if hn > 8:
                            cajas_n.append((xn, yn, wn, hn))
                    cajas_n = sorted(cajas_n, key=lambda item: item[0])
                    
                    digitos_nuevos = []
                    for idx_dn, (xn, yn, wn, hn) in enumerate(cajas_n):
                        dig_img = mascara_n[yn:yn+hn, xn:xn+wn]
                        dig_std = cv2.resize(dig_img, (20, 30))
                        mejor_p = -1
                        mejor_d = None
                        for num, plantilla in plantillas.items():
                            res = cv2.matchTemplate(dig_std, plantilla, cv2.TM_CCOEFF_NORMED)
                            _, max_v, _, _ = cv2.minMaxLoc(res)
                            if max_v > mejor_p:
                                mejor_p = max_v
                                mejor_d = num
                        if mejor_d is not None:
                            digitos_nuevos.append(str(mejor_d))
                            
                    if digitos_nuevos:
                        giros_restantes_actual = int("".join(digitos_nuevos))
                        print(f" -> [ACTUALIZADO] Giros reales leídos en pantalla: {giros_restantes_actual}")
                    else:
                        print(" -> [AVISO] No se pudo leer el número. Posible torneo u opacidad bloqueando...")
                        
                        modal_cerrado_mid = False

                        # 1. Clic prioritario a 'Maybe Later' por porcentaje (despeja el torneo opaco)
                        try:
                            ancho_w, alto_w = pyautogui.size()
                            clic_x = int(ancho_w * 0.538)
                            clic_y = int(alto_w * 0.785)
                            
                            pyautogui.click(clic_x, clic_y)
                            print(f" -> [OK] Clic anti-torneo 'Maybe Later' ejecutado en ({clic_x}, {clic_y}).")
                            modal_cerrado_mid = True
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f" -> [AVISO] Error al hacer clic anti-torneo: {e}")

                        # 2. Clic en notificación superior del navegador si está activa
                        try:
                            btn_notif = pagina.locator("text='No, gracias', text='No gracias'").first
                            if await btn_notif.is_visible(timeout=150):
                                await btn_notif.click(force=True)
                                print(" -> [OK] Notificación superior cerrada.")
                        except:
                            pass

                        if modal_cerrado_mid:
                            # Reintenta el ciclo para releer los números ya con el brillo normal
                            await asyncio.sleep(0.5)
                            continue
                        else:
                            giros_restantes_actual -= 1

                    # --- VERIFICACIÓN INTELIGENTE SI EL NÚMERO NO CAMBIÓ ---
                    if digitos_nuevos and giros_restantes_actual == giros_anterior:
                        print(" -> [VERIFICACIÓN] El contador sigue igual. Comprobando si hay publicidad bloqueando...")
                        modal_cerrado_mid = False
                        try:
                            for entorno in [pagina] + pagina.frames:
                                try:
                                    btn_dismiss = entorno.locator("text='Maybe Later', text='No gracias', text='No, gracias', text='Later', text='Más tarde'").first
                                    if await btn_dismiss.is_visible(timeout=300):
                                        await btn_dismiss.click(force=True)
                                        print(" -> [OK] Publicidad sorpresa cerrada tras bloqueo de lectura.")
                                        modal_cerrado_mid = True
                                        break
                                    
                                    btn_x_gen = entorno.locator("button.dialog-close, [class*='close' i], [aria-label*='Close' i], [aria-label*='Cerrar' i]").first
                                    if await btn_x_gen.is_visible(timeout=300):
                                        await btn_x_gen.click(force=True)
                                        print(" -> [OK] Publicidad 'X' cerrada tras bloqueo de lectura.")
                                        modal_cerrado_mid = True
                                        break
                                except:
                                    continue
                        except:
                            pass

                        if modal_cerrado_mid:
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            print(" -> [INFO] No hay publicidad. Asumiendo animación o premio especial de la máquina, continuando...")

                    # Si el contador en pantalla llegó a 0 o menos, salimos del bucle
                    if giros_restantes_actual <= 0:
                        print(f" -> [GIRO EJECUTADO] ¡Los giros en pantalla llegaron a 0! Saliendo del bucle...")
                        break
                        
                else:
                    print("\n[RECUPERACIÓN] Buscando botón pequeño de FreeSpin...")
                    
                    # --- FILTRO INTELIGENTE MID-GAME (ANTI-PUBLICIDAD / TORNEOS) ---
                    modal_cerrado_mid = False
                    try:
                        for entorno in [pagina] + pagina.frames:
                            try:
                                btn_dismiss = entorno.locator("text='Maybe Later', text='No gracias', text='No, gracias', text='Later', text='Más tarde'").first
                                if await btn_dismiss.is_visible(timeout=300):
                                    await btn_dismiss.click(force=True)
                                    print(" -> [OK] Publicidad sorpresa cerrada a mitad de ronda haciendo clic en 'Maybe Later' / 'No gracias'.")
                                    modal_cerrado_mid = True
                                    break
                                
                                btn_x_gen = entorno.locator("button.dialog-close, [class*='close' i], [aria-label*='Close' i], [aria-label*='Cerrar' i]").first
                                if await btn_x_gen.is_visible(timeout=300):
                                    await btn_x_gen.click(force=True)
                                    print(" -> [OK] Publicidad sorpresa cerrada a mitad de ronda haciendo clic en la 'X'.")
                                    modal_cerrado_mid = True
                                    break
                            except:
                                continue
                    except:
                        pass

                    if modal_cerrado_mid:
                        await asyncio.sleep(1.0)
                        print(" -> [INFO] Publicidad cerrada con éxito. Reintentando buscar el botón principal de giro...")
                        continue
                    # -------------------------------------------------------------

                    rescatado = False
                    try:
                        ubicacion_pequeno = pyautogui.locateOnScreen("boton_pequeno.png", confidence=0.75)
                        if ubicacion_pequeno:
                            px, py = pyautogui.center(ubicacion_pequeno)
                            pyautogui.click(px, py)
                            print(f" -> [ACCIÓN] ¡Clic de rescate en botón pequeño en ({px}, {py})!")
                            rescatado = True
                    except:
                        pass

                    if not rescatado:
                        entornos_juego = [pagina] + pagina.frames
                        selectores_pequenos = [
                            "[title*='giro' i]",
                            "[title*='spin' i]",
                            "[aria-label*='giro' i]",
                            "[aria-label*='spin' i]"
                        ]
                        for entorno in entornos_juego:
                            for sel in selectores_pequenos:
                                try:
                                    els = entorno.locator(sel)
                                    if await els.count() > 0:
                                        el = els.nth(0)
                                        if await el.is_visible(timeout=500):
                                            box = await el.bounding_box()
                                            if box:
                                                bx = box["x"] + (box["width"] * 0.5)
                                                by = box["y"] + (box["height"] * 0.5)
                                                await pagina.mouse.click(bx, by)
                                                print(f" -> [OK] ¡Rescate DOM exitoso en ({bx:.1f}, {by:.1f})!")
                                                rescatado = True
                                                break
                                except:
                                    continue
                            if rescatado:
                                break

                    if rescatado:
                        await asyncio.sleep(2.0)
                        print(" -> [RE-LECTURA] Actualizando contador de giros tras el rescate...")
                        captura_nueva = pyautogui.screenshot()
                        imagen_np_n = np.array(captura_nueva)
                        imagen_bgr_n = cv2.cvtColor(imagen_np_n, cv2.COLOR_RGB2BGR)
                        alto_pn, ancho_pn, _ = imagen_bgr_n.shape
                        y1_n, y2_n, x1_n, x2_n = int(alto_pn * 0.88), int(alto_pn * 0.98), int(ancho_pn * 0.55), int(ancho_pn * 0.70)
                        recorte_n = imagen_bgr_n[y1_n:y2_n, x1_n:x2_n]
                        
                        hsv_n = cv2.cvtColor(recorte_n, cv2.COLOR_BGR2HSV)
                        mascara_n = cv2.inRange(hsv_n, lower_orange, upper_orange)
                        contornos_n, _ = cv2.findContours(mascara_n, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        
                        cajas_n = []
                        for cn in contornos_n:
                            xn, yn, wn, hn = cv2.boundingRect(cn)
                            if hn > 8:
                                cajas_n.append((xn, yn, wn, hn))
                        cajas_n = sorted(cajas_n, key=lambda item: item[0])
                        
                        digitos_nuevos = []
                        for idx_dn, (xn, yn, wn, hn) in enumerate(cajas_n):
                            dig_img = mascara_n[yn:yn+hn, xn:xn+wn]
                            dig_std = cv2.resize(dig_img, (20, 30))
                            mejor_p = -1
                            mejor_d = None
                            for num, plantilla in plantillas.items():
                                res = cv2.matchTemplate(dig_std, plantilla, cv2.TM_CCOEFF_NORMED)
                                _, max_v, _, _ = cv2.minMaxLoc(res)
                                if max_v > mejor_p:
                                    mejor_p = max_v
                                    mejor_d = num
                            if mejor_d is not None:
                                digitos_nuevos.append(str(mejor_d))
                                
                        if digitos_nuevos:
                            giros_restantes_actual = int("".join(digitos_nuevos))
                            print(f" -> [ACTUALIZADO] Faltan: {giros_restantes_actual} giros.")
                        else:
                            print(" -> [AVISO] No se pudo re-leer el contador, manteniendo valor.")
                            
                        continue
                    else:
                        print("\n[ALERTA] No se encontró el botón. Reintentando...")
                        await asyncio.sleep(1.0)

            print(f"\n[FIN] ¡Ronda de bonos finalizada! Último giro ejecutado. Procediendo a leer saldo y enviar WhatsApp...")   

            # =========================================================================
            # [PASO 19] Captura del saldo final y envío por WhatsApp Desktop (App Nativa)
            # =========================================================================
            print("\n[PASO 19] Ronda de giros terminada. Actualizando página para leer el saldo...")
            
            await pagina.bring_to_front()
            await asyncio.sleep(1)

            # Recargar la página para forzar la actualización del saldo
            try:
                await pagina.reload(timeout=30000)
                print(" -> [OK] Página recargada con éxito. Esperando que cargue el saldo...")
                await asyncio.sleep(4)
            except Exception as e:
                print(f" -> [AVISO] No se pudo recargar automáticamente: {e}. Intentando leer con el saldo actual...")

            # 1. Capturar el saldo actual desde la barra superior visible
            saldo_final = "No se pudo leer"
            try:
                elemento_saldo = pagina.locator("div.headerMenuAuthenticated_balance, [class*='balance'], .header-balance").first
                await elemento_saldo.wait_for(state="visible", timeout=5000)
                saldo_final = (await elemento_saldo.inner_text()).strip()
            except Exception:
                try:
                    elemento_saldo_2 = pagina.locator("text=/DEPÓSITO/i >> xpath=preceding::div[1]").first
                    if await elemento_saldo_2.is_visible(timeout=2000):
                        saldo_final = (await elemento_saldo_2.inner_text()).strip()
                except:
                    pass

            print(f" -> [OK] Saldo final capturado: {saldo_final}")

            # 2. Interacción con la app de WhatsApp Desktop
            contacto_destino = "Cargas"
            print(f"\n[PASO 19.2] Enviando reporte final por WhatsApp Desktop (Destino: {contacto_destino})...")

            # Abrir la aplicación de Escritorio
            subprocess.run(["start", "whatsapp:/"], shell=True)
            time.sleep(5.0)

            # Buscar el chat
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1.5)
            pyperclip.copy(contacto_destino)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2.0)
            pyautogui.press('enter')
            time.sleep(2.5)

            # Escribir y enviar el mensaje con el saldo final capturado
            mensaje_reporte = f"¡Ronda de giros finalizada! Saldo final: {saldo_final}"
            pyperclip.copy(mensaje_reporte)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(2.0)

            # 3. Cierre forzado e infalible (Combo de seguridad idéntico al Paso 11)
            print(" -> Cerrando la aplicación de WhatsApp para liberar la pantalla...")
            subprocess.run("taskkill /f /im WhatsApp.exe /t >nul 2>&1", shell=True)
            subprocess.run("powershell -command \"Stop-Process -Name 'WhatsApp' -Force -ErrorAction SilentlyContinue\"", shell=True)
            pyautogui.hotkey('alt', 'f4')
            time.sleep(1.5)

            print(" -> [OK] Reporte final enviado por WhatsApp con éxito. ¡Proceso terminado!")
            print("\n[INFO] ¡Flujo completo 100% completado!")
            await asyncio.sleep(2)
            
            # Marca automáticamente como Procesada en el Excel al terminar con éxito
            actualizar_estado_cuenta(usuario, "Procesada")
            print(f" -> [EXCEL] Cuenta {usuario} marcada como Procesada.")

        except Exception as e:
            print(f"\n[ERROR] Ocurrió un error en la secuencia: {e}")
            # Marca automáticamente como Error en el Excel si algo falla a mitad de camino
            actualizar_estado_cuenta(usuario, "Error - Falla en ejecución")
            raise e
dddddd
if __name__ == "__main__":
    asyncio.run(flujo_secuencial_completo())
