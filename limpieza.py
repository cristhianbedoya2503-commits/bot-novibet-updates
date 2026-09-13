import os
import shutil
import time
import winreg
import subprocess

# Cambiamos la URL por Google para que abra el navegador de forma normal
URL_VPN = "https://www.google.com"

def limpiar_carpeta(nombre_seccion, ruta):
    """Elimina los archivos y carpetas dentro de una ruta de forma segura, calculando espacio liberado."""
    if not os.path.exists(ruta):
        return 0
    
    print(f"[LIMPIEZA] Vaciando {nombre_seccion}: {ruta}")
    eliminados = 0
    fallidos = 0
    bytes_liberados = 0
    
    for item in os.listdir(ruta):
        item_path = os.path.join(ruta, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                bytes_liberados += os.path.getsize(item_path)
                os.unlink(item_path)
                eliminados += 1
            elif os.path.isdir(item_path):
                for root, dirs, files in os.walk(item_path):
                    for f in files:
                        try:
                            bytes_liberados += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass
                shutil.rmtree(item_path)
                eliminados += 1
        except Exception:
            fallidos += 1
            
    mb_liberados = bytes_liberados / (1024 * 1024)
    print(f"    -> Éxito: {eliminados} elementos borrados ({mb_liberados:.2f} MB liberados). Omitidos en uso: {fallidos}")
    return bytes_liberados

def limpiar_descargas_antiguas(ruta_descargas, dias=30):
    """Limpia archivos muy antiguos de la carpeta de descargas de Windows."""
    if not os.path.exists(ruta_descargas):
        return 0
    print(f"[LIMPIEZA] Vaciando archivos temporales en Descargas de Windows...")
    eliminados = 0
    bytes_liberados = 0
    ahora = time.time()
    limite_tiempo = dias * 86400

    try:
        for item in os.listdir(ruta_descargas):
            item_path = os.path.join(ruta_descargas, item)
            if os.path.isfile(item_path):
                mtime = os.path.getmtime(item_path)
                if (ahora - mtime) > limite_tiempo:
                    bytes_liberados += os.path.getsize(item_path)
                    os.unlink(item_path)
                    eliminados += 1
    except Exception:
        pass
    print(f"    -> Descargas limpiadas: {eliminados} archivos antiguos eliminados.")
    return bytes_liberados

def limpiar_registros_y_avanzados():
    """Limpia rastros avanzados, portapapeles y registros de Windows."""
    print("[LIMPIEZA] Ejecutando rutinas avanzadas y registros de Windows...")
    
    # 1. Historial RunMRU (Ejecuciones recientes de Windows)
    try:
        ruta_registro = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_registro, 0, winreg.KEY_ALL_ACCESS)
        i = 0
        while True:
            try:
                nombre_val, _, _ = winreg.EnumValue(key, i)
                if nombre_val != "MRUList":
                    winreg.DeleteValue(key, nombre_val)
                else:
                    i += 1
            except WindowsError:
                break
        winreg.SetValueEx(key, "MRUList", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        print("    -> [OK] Historial de ejecuciones recientes (RunMRU) limpiado.")
    except Exception:
        pass

    # 2. Portapapeles
    try:
        os.system("echo off | clip")
        print("    -> [OK] Portapapeles limpiado.")
    except Exception:
        pass

    # 3. Registros de eventos de Windows
    try:
        os.system("for /F \"tokens=*\" %1 in ('wevtutil.exe el') do wevtutil.exe cl \"%1\" >nul 2>&1")
        print("    -> [OK] Registros de eventos de Windows depurados.")
    except Exception:
        pass

def purgar_historial_todos_los_perfiles():
    """Busca y elimina historiales y sesiones en todos los perfiles de Chrome del equipo."""
    print("[INFO] Purgando historiales de navegación en todos los perfiles de Chrome...")
    
    rutas_a_revisar = [
        r"C:\ChromeDevSession",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    ]
    
    archivos_historial = ["History", "History-journal", "Top Sites", "Visited Links", "Favicons", "Current Session", "Last Session", "Current Tabs", "Last Tabs"]
    
    for ruta_base in rutas_a_revisar:
        if not os.path.exists(ruta_base):
            continue
            
        perfiles = ["Default"]
        try:
            for item in os.listdir(ruta_base):
                if item.startswith("Profile ") or item.startswith("Guest Profile") or item.startswith("System Profile"):
                    perfiles.append(item)
        except Exception:
            pass
            
        for perfil in perfiles:
            ruta_perfil = os.path.join(ruta_base, perfil)
            if not os.path.exists(ruta_perfil):
                continue
                
            for archivo in archivos_historial:
                archivo_path = os.path.join(ruta_perfil, archivo)
                if os.path.exists(archivo_path):
                    try:
                        os.remove(archivo_path)
                    except Exception:
                        pass
    print("    -> [OK] Historiales y sesiones eliminados de raíz.")

def preparar_plantilla_sesion():
    """Copia la PlantillaNovibet personalizada a la sesión de trabajo de Chrome."""
    carpeta_sesion = r"C:\ChromeDevSession"
    
    # Destruir sesión anterior si existe
    if os.path.exists(carpeta_sesion):
        try:
            shutil.rmtree(carpeta_sesion)
        except Exception:
            pass
            
    os.makedirs(carpeta_sesion, exist_ok=True)
    
    # Ruta donde tienes tu PlantillaNovibet en la misma carpeta del script
    ruta_plantilla = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PlantillaNovibet")
    
    if os.path.exists(ruta_plantilla):
        print("[INFO] Restaurando PlantillaNovibet (Cookies, Caché y WhatsApp)...")
        try:
            for item in os.listdir(ruta_plantilla):
                origen_item = os.path.join(ruta_plantilla, item)
                destino_item = os.path.join(carpeta_sesion, item)
                if os.path.isdir(origen_item):
                    shutil.copytree(origen_item, destino_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(origen_item, destino_item)
            print("    -> [OK] Plantilla aplicada con éxito.")
        except Exception as e:
            print(f"    -> [AVISO] No se pudo aplicar la plantilla completamente: {e}")
    else:
        print(f"    -> [AVISO] No se encontró la carpeta 'PlantillaNovibet' en {ruta_plantilla}. Se iniciará limpio.")

def abrir_navegador_vpn():
    """Abre Chrome utilizando la sesión restaurada con la plantilla y carga Google."""
    print("[INFO] Abriendo navegador con sesión optimizada...")
    
    rutas_posibles = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    
    chrome_path = next((r for r in rutas_posibles if os.path.exists(r)), None)

    if not chrome_path:
        print("[ERROR] No se encontró el ejecutable de Google Chrome.")
        return

    carpeta_sesion = r"C:\ChromeDevSession"

    # Comando para lanzar Chrome apuntando a nuestra sesión con la plantilla inyectada
    comando = (
        f'"{chrome_path}" --remote-debugging-port=9222'
        f' --user-data-dir="{carpeta_sesion}"'
        f' "{URL_VPN}"'
        " --no-first-run --start-maximized"
    )

    try:
        subprocess.Popen(comando, shell=True)
        print("    -> [OK] Navegador lanzado correctamente utilizando la plantilla.")
    except Exception as e:
        print(f"    -> [ERROR] No se pudo abrir el navegador: {e}")

def ejecutar_limpieza_y_arranque():
    print("==================================================")
    print("   MÓDULO DE LIMPIEZA TOTAL Y APERTURA DE CHROME  ")
    print("==================================================")
    
    tiempo_inicio = time.time()
    total_bytes = 0
    
    # 1. Cierre forzoso de Chrome y Drivers
    print("[INFO] Cerrando instancias activas de Google Chrome y Drivers...")
    os.system("taskkill /f /im chrome.exe /t >nul 2>&1")
    os.system("taskkill /f /im chromedriver.exe /t >nul 2>&1")
    time.sleep(3)

    # 2. RESTAURAR NAVEGADOR PERSONAL A FÁBRICA
    ruta_chrome_personal = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    if os.path.exists(ruta_chrome_personal):
        try:
            shutil.rmtree(ruta_chrome_personal)
            print("    -> [OK] Navegador personal restablecido a FÁBRICA (User Data eliminado).")
        except Exception as e:
            print(f"    -> [AVISO] No se pudo restablecer el navegador personal por completo: {e}")

    # 3. Purgar historiales residuales
    purgar_historial_todos_los_perfiles()

    # 4. Temporales del sistema y Prefetch
    temp_user = os.environ.get('TEMP')
    if temp_user:
        total_bytes += limpiar_carpeta("Temp de Usuario", temp_user)
        
    total_bytes += limpiar_carpeta("Temp de Windows", r"C:\Windows\Temp")
    
    try:
        total_bytes += limpiar_carpeta("Prefetch de Windows", r"C:\Windows\Prefetch")
    except Exception:
        pass

    # 5. Descargas antiguas de Windows
    user_profile = os.environ.get('USERPROFILE')
    if user_profile:
        total_bytes += limpiar_descargas_antiguas(os.path.join(user_profile, "Downloads"), dias=30)

    # 6. Limpiezas avanzadas de Windows y Registros
    limpiar_registros_y_avanzados()
    
    # 7. PREPARAR E INYECTAR LA PLANTILLA NOVIBET
    preparar_plantilla_sesion()

    tiempo_total = time.time() - tiempo_inicio
    espacio_total_mb = total_bytes / (1024 * 1024)

    print("==================================================")
    print(f"   ¡LIMPIEZA TOTAL COMPLETADA EN {tiempo_total:.2f} SEGUNDOS!")
    print(f"   Espacio total liberado aprox: {espacio_total_mb:.2f} MB")
    print("==================================================")

    # 8. APERTURA DEL NAVEGADOR
    time.sleep(1)
    abrir_navegador_vpn()

if __name__ == "__main__":
    ejecutar_limpieza_y_arranque()