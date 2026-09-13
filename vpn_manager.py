import asyncio
import os
import random
import pyautogui
from playwright.async_api import async_playwright

# URL exacta de la extensión en la Chrome Web Store
URL_EXT_VPN = "https://chromewebstore.google.com/detail/residential-vpn-tuxler/jpgljfpmoofbmlieejglhonfofmahini"

async def secuencia_completa_vpn():
    print("[INFO] Conectando Playwright al navegador en ejecución...")
    
    async with async_playwright() as p:
        try:
            # Conexión al puerto de depuración del navegador
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            contexto = browser.contexts[0]
            
            # Buscamos si hay una pestaña activa de la tienda o usamos una disponible
            pagina = None
            for p_activa in contexto.pages:
                if "chromewebstore.google.com" in p_activa.url:
                    pagina = p_activa
                    break
            
            if not pagina:
                if contexto.pages:
                    pagina = contexto.pages[0]
                else:
                    pagina = await contexto.new_page()

            await pagina.bring_to_front()
            print(f"[INFO] Navegando a la Chrome Web Store de Tuxler...")
            await pagina.goto(URL_EXT_VPN)
            await asyncio.sleep(2)

            # ==========================================================
            # PASO 1: Hacer clic en "Añadir a Chrome" y confirmar pop-up nativo
            # ==========================================================
            try:
                print("\n--- PASO 1: Buscando el botón 'Añadir a Chrome' ---")
                boton_anadir = pagina.locator("button:has-text('Añadir a Chrome')")
                
                if await boton_anadir.is_visible(timeout=5000):
                    print("[INFO] ¡Botón visible! Haciendo clic...")
                    await boton_anadir.click()
                    await asyncio.sleep(1.5)

                    # Confirmación rápida con PyAutoGUI sobre el cuadro nativo
                    ancho_pantalla, alto_pantalla = pyautogui.size()
                    pyautogui.click(ancho_pantalla // 2, alto_pantalla // 2)
                    pyautogui.press('left')
                    pyautogui.press('enter')
                    
                    print("[INFO] Pop-up nativo confirmado con éxito.")
                    await asyncio.sleep(4)
            except Exception as e:
                print(f"[INFO] El botón no es visible o la extensión ya se encuentra instalada: {e}")

            # ==========================================================
            # PASO 1.5: Cerrar la pestaña de bienvenida de Tuxler si aparece
            # ==========================================================
            for p_activa in contexto.pages:
                if "tuxlervpn.com" in p_activa.url:
                    print("[INFO] Cerrando la pestaña de bienvenida de Tuxler...")
                    await p_activa.close()
                    await asyncio.sleep(0.5)

            # ==========================================================
            # PASO 2: Obtener el ID interno de Tuxler y abrir su interfaz por URL
            # ==========================================================
            print("\n--- PASO 2: Buscando el ID interno de la extensión ---")
            
            pagina_ext = await contexto.new_page()
            await pagina_ext.goto("chrome://extensions/")
            
            # Extraemos el ID analizando los Shadow DOMs de la página de extensiones
            extension_id = await pagina_ext.evaluate("""() => {
                const manager = document.querySelector('extensions-manager');
                if (!manager) return null;
                const list = manager.shadowRoot.querySelector('extensions-item-list');
                if (!list) return null;
                const items = list.shadowRoot.querySelectorAll('extensions-item');
                
                for (let item of items) {
                    const name = item.shadowRoot.querySelector('#name');
                    if (name && name.textContent.toLowerCase().includes('tuxler')) {
                        return item.id;
                    }
                }
                return null;
            }""")
            
            await pagina_ext.close()

            if extension_id:
                print(f"[OK] ¡ID de Tuxler encontrado con éxito: {extension_id}!")
                
                # Construimos y abrimos la URL interna del popup de la VPN
                url_vpn = f"chrome-extension://{extension_id}/popup.html"
                print(f"[INFO] Abriendo directamente la interfaz en: {url_vpn}")
                
                pagina_vpn = await contexto.new_page()
                await pagina_vpn.goto(url_vpn)
                print("[OK] ¡Interfaz de la VPN abierta correctamente por URL!")
                
            else:
                print("[ERROR] No se pudo encontrar el ID de Tuxler automáticamente en chrome://extensions/.")

        except Exception as e:
            print(f"[ERROR] Ocurrió un fallo durante el proceso: {e}")

async def loguear_y_configurar_vpn():
    print("[INFO] Conectando Playwright al navegador en ejecución para configurar...")
    
    async with async_playwright() as p:
        try:
            # 1. Conexión al puerto de depuración actual
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            contexto = browser.contexts[0]
            
            # Buscamos la pestaña que tenga la interfaz de la VPN (popup de Tuxler)
            pagina_vpn = None
            for p_activa in contexto.pages:
                if "extension://" in p_activa.url and "popup.html" in p_activa.url:
                    pagina_vpn = p_activa
                    break
            
            if not pagina_vpn:
                print("[ERROR] No se encontró abierta la ventana de la VPN. Por favor ábrela primero.")
                return

            await pagina_vpn.bring_to_front()
            print("[INFO] Ventana de la VPN localizada.")

            # ==========================================================
            # PASO 1 y 2 (Inteligente): Abrir menú y verificar sesión
            # ==========================================================
            print("\n--- PASO 1 y 2: Abriendo menú y verificando estado ---")
            try:
                await pagina_vpn.locator(".ham").click(timeout=3000)
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"[INFO] No se pudo hacer clic en el menú .ham: {e}")

            membership_locator = pagina_vpn.locator("text=MEMBERSHIP INFORMATION")
            is_logged_in = await membership_locator.is_visible()

            if is_logged_in:
                print("[OK] Sesión ya iniciada (detectado 'MEMBERSHIP INFORMATION'). Omitiendo login.")
            else:
                print("[INFO] No hay sesión activa. Buscando opción de acceso...")
                try:
                    await pagina_vpn.locator("text=UPGRADE TO PREMIUM").click(timeout=2000)
                    await asyncio.sleep(1.0)
                except:
                    pass

                # ==========================================================
                # PASOS 3 y 4: Ingreso de credenciales si era necesario
                # ==========================================================
                input_email = pagina_vpn.locator("input[type='text'][placeholder='EMAIL ADDRESS']")
                if await input_email.is_visible():
                    print("[INFO] Procediendo a loguearse con credenciales...")
                    ruta_archivo = "credenciales_vpn.txt"
                    if not os.path.exists(ruta_archivo):
                        print(f"[ERROR] No se encontró el archivo {ruta_archivo} en la carpeta.")
                        return

                    with open(ruta_archivo, "r", encoding="utf-8") as f:
                        lineas = [l.strip() for l in f.readlines() if l.strip()]

                    if len(lineas) < 2:
                        print("[ERROR] El archivo de credenciales debe tener al menos el correo y la contraseña.")
                        return

                    correo = lineas[0].split(":")[-1].strip() if ":" in lineas[0] else lineas[0]
                    contrasena = lineas[1].split(":")[-1].strip() if ":" in lineas[1] else lineas[1]

                    print(f"[INFO] Ingresando credenciales para: {correo}")
                    await input_email.fill(correo)
                    await pagina_vpn.locator("input[type='password'][placeholder='PASSWORD']").fill(contrasena)
                    await asyncio.sleep(0.5)

                    await pagina_vpn.locator("a.btn.main.gold:has-text('LOG IN')").click()
                    print("[INFO] Esperando carga del dashboard principal...")
                    await asyncio.sleep(3.0)

            # ==========================================================
            # PASO 5: Verificar si la VPN está conectada para reiniciar el Switch
            # ==========================================================
            print("\n--- PASO 5: Verificando estado del interruptor (Switch) ---")
            badge_protected = pagina_vpn.locator("text=PROTECTED")
            is_protected = await badge_protected.is_visible()

            switch_locator = pagina_vpn.locator("div.v-switch-core, .vue-switcher, input[type='checkbox']").first

            if is_protected:
                print("[INFO] La VPN ya se encuentra conectada (PROTECTED). Reiniciando el switch para refrescar IP...")
                await switch_locator.click()
                print("[INFO] Primer clic realizado (Apagando)...")
                await asyncio.sleep(1.5)
                
                await switch_locator.click()
                print("[OK] Segundo clic realizado (Encendiendo de nuevo)...")
                await asyncio.sleep(1.0)
            else:
                print("[INFO] La VPN está apagada. Encendiéndola directamente...")
                await switch_locator.click()
                print("[OK] Switch encendido.")
                await asyncio.sleep(1.0)

            # ==========================================================
            # PASO 6: Verificar pestaña "RESIDENTIAL"
            # ==========================================================
            print("\n--- PASO 6: Verificando pestaña 'RESIDENTIAL' ---")
            tab_residential = pagina_vpn.locator("div.type:has-text('RESIDENTIAL')")
            clase_tab = await tab_residential.get_attribute("class") or ""
            
            if "active" in clase_tab:
                print("[OK] La pestaña 'RESIDENTIAL' ya está seleccionada.")
            else:
                print("[INFO] Seleccionando pestaña 'RESIDENTIAL'...")
                await tab_residential.click()
                await asyncio.sleep(0.5)

            # ==========================================================
            # PASO 7 y 8: Verificación inteligente de país (México)
            # ==========================================================
            print("\n--- PASO 7 y 8: Verificando país actual ---")
            selector_pais = pagina_vpn.locator("div.select-selected").first
            texto_actual = await selector_pais.inner_text()
            print(f"[INFO] País seleccionado actualmente: '{texto_actual.strip()}'")

            if "Mexico" in texto_actual:
                print("[OK] México ya se encuentra seleccionado. Omitiendo selección de país.")
            else:
                print("[INFO] México no está seleccionado. Abriendo menú y seleccionándolo...")
                await selector_pais.click()
                await asyncio.sleep(0.8)
                await pagina_vpn.locator("div.select-item").filter(has_text="Mexico").first.click()
                print("[OK] ¡México seleccionado con éxito!")
                await asyncio.sleep(1.5)

            # ==========================================================
            # PASO 9: Abrir el segundo selector de región/ciudad
            # ==========================================================
            print("\n--- PASO 9: Abriendo el selector de región/ciudad ---")
            await asyncio.sleep(1.0)
            await pagina_vpn.locator("div.select-selected").nth(1).click()
            print("[OK] ¡Menú de regiones/ciudades desplegado con éxito!")
            await asyncio.sleep(1.0)

            # ==========================================================
            # PASO 10: Seleccionar una ciudad de forma aleatoria
            # ==========================================================
            print("\n--- PASO 10: Seleccionando una ciudad aleatoria ---")
            lista_ciudades = pagina_vpn.locator("div.select-item")
            cantidad_ciudades = await lista_ciudades.count()
            
            if cantidad_ciudades > 0:
                indice_aleatorio = random.randint(0, cantidad_ciudades - 1)
                ciudad_seleccionada = lista_ciudades.nth(indice_aleatorio)
                nombre_ciudad = await ciudad_seleccionada.inner_text()
                print(f"[INFO] Ciudad aleatoria elegida (índice {indice_aleatorio}): {nombre_ciudad.strip()}")
                
                await ciudad_seleccionada.click()
                print("[OK] ¡Ciudad configurada con éxito y VPN lista!")
                await asyncio.sleep(1.0)
            else:
                print("[ERROR] No se encontraron ciudades disponibles en el menú desplegable.")

            # ==========================================================
            # PASO 11: Cerrar todas las demás pestañas y dejar solo la VPN
            # ==========================================================
            print("\n--- PASO 11: Limpiando pestañas adicionales ---> cleaner")
            paginas_actuales = contexto.pages
            for p_activa in paginas_actuales:
                if p_activa != pagina_vpn:
                    try:
                        await p_activa.close()
                    except Exception:
                        pass
            
            await pagina_vpn.bring_to_front()
            print("[OK] ¡Todas las pestañas sobrantes fueron cerradas. Solo queda la interfaz de la VPN!")

        except Exception as e:
            print(f"[ERROR] Ocurrió un fallo durante el proceso: {e}")

async def main():
    print("=== INICIANDO SECUENCIA COMPLETA DE VPN ===")
    await secuencia_completa_vpn()
    print("\n=== ESPERANDO ANTES DE LA CONFIGURACIÓN ===")
    await asyncio.sleep(2)
    await loguear_y_configurar_vpn()

if __name__ == "__main__":
    asyncio.run(main())