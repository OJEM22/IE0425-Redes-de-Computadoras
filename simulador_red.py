# ==============================
# Simulador simple de red con capas

# Estudiantes:
# Olman Espinoza
# Ricardo Carmona
# Leonardo Serrano
# ==============================


# ==============================
# Direcciones simplificadas (8 bits)
# ==============================
PC1_IP = "1"
PC2_IP = "2"

ROUTER_IP_LEFT = "3"
ROUTER_IP_RIGHT = "4"

PC1_MAC = "A"
PC2_MAC = "B"
ROUTER_MAC_LEFT = "C"
ROUTER_MAC_RIGHT = "D"
SWITCH1_MAC = "E"
SWITCH2_MAC = "F"

TCP_PORT = 80
UDP_PORT = 53

APP_CODES = {
    "WhatsApp": "11",
    "Messenger": "12",
    "Telegram": "13"
}

# ==============================
# CAPAS
# ==============================
class CapaAplicacion:
    # Encapsula el mensaje de la aplicación agregando una etiqueta [APP:<codigo>]
    @staticmethod
    def encapsular(mensaje, app="GENERICA"):
        return f"[APP:{app}]" + mensaje
    
    # Extrae la cabecera de aplicación y devuelve (payload, app)
    @staticmethod
    def desencapsular(datos):
        if datos.startswith("[APP:"):
            fin = datos.find(']') + 1  # índice del cierre de la etiqueta
            app = datos[5:fin-1]       # obtiene el texto entre "APP:" y "]"
            return datos[fin:], app    # payload sin la cabecera y código de app
        # Si no viene etiquetado, se asume genérica
        return datos, "GENERICA"

class CapaTransporte:
    # Construye un segmento de transporte con protocolo y puertos: [H4:PROTO:src:dst]
    @staticmethod
    def encapsular(datos_app, puerto_origen, puerto_destino, protocolo):
        encabezado = f"[H4:{protocolo}:{puerto_origen}:{puerto_destino}]"
        return encabezado + datos_app
    
    # Extrae cabecera de transporte y retorna (datos_app, protocolo, puerto_origen, puerto_destino)
    @staticmethod
    def desencapsular(segmento):
        fin = segmento.find(']') + 1        # localiza fin de cabecera
        encabezado = segmento[:fin]
        datos_app = segmento[fin:]          # resto es el payload de aplicación
        partes = encabezado[1:-1].split(':')  # quita [ ] y separa por :
        protocolo = partes[1]
        puerto_origen = int(partes[2])
        puerto_destino = int(partes[3])
        return datos_app, protocolo, puerto_origen, puerto_destino

class CapaRed:
    # Añade cabecera IP simplificada [H3:ip_origen:ip_destino]
    @staticmethod
    def encapsular(segmento, ip_origen, ip_destino):
        return f"[H3:{ip_origen}:{ip_destino}]" + segmento
    
    # Quita cabecera IP y retorna (segmento_transporte, ip_origen, ip_destino)
    @staticmethod
    def desencapsular(paquete):
        fin = paquete.find(']') + 1
        segmento = paquete[fin:]                 # payload de capa 4
        partes = paquete[1:fin-1].split(':')     # [H3:...]
        return segmento, partes[1], partes[2]

class CapaEnlace:
    # Encapsula en una trama de enlace [H2:mac_origen:mac_destino]
    @staticmethod
    def encapsular(paquete, mac_origen, mac_destino):
        return f"[H2:{mac_origen}:{mac_destino}]" + paquete
    
    # Desencapsula la trama de enlace y retorna (paquete_red, mac_origen, mac_destino)
    @staticmethod
    def desencapsular(trama):
        fin = trama.find(']') + 1
        paquete = trama[fin:]                    # payload de capa 3
        partes = trama[1:fin-1].split(':')
        return paquete, partes[1], partes[2]

class CapaFisica:
    # Convierte la cadena (trama) a bits ASCII (8 bits por carácter)
    @staticmethod
    def encapsular(trama):
        # Cada char -> su código ASCII binario con longitud 8
        return ''.join(format(ord(c), '08b') for c in trama)
    
    # Convierte los bits en texto interpretando cada 8 bits como un byte ASCII
    @staticmethod
    def desencapsular(bits):
        chars = []
        # Recorre de 8 en 8; asume longitud múltiplo de 8
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            chars.append(chr(int(byte, 2)))
        return ''.join(chars)

# ==============================
# Dispositivos
# ==============================
class Dispositivo:
    # Inicializa un dispositivo genérico con:
    # - nombre identificador
    # - conexiones: mapa de interfaz_local -> (dispositivo_destino, interfaz_destino)
    # - tabla_enlace: MAC -> interfaz_salida (conmutación/N2)
    # - tabla_red: IP -> MAC siguiente salto (encaminamiento simple/N3)
    def __init__(self, nombre):
        self.nombre = nombre
        self.conexiones = {}
        self.tabla_enlace = {}
        self.tabla_red = {}

    # Conecta este dispositivo: interfaz_local <-> (otro_dispositivo, interfaz_remota)
    def conectar(self, interfaz_local, dispositivo_destino, interfaz_remota):
        self.conexiones[interfaz_local] = (dispositivo_destino, interfaz_remota)

    # Envía una trama por una interfaz. Simula capa física convirtiendo a bits y llamando al receptor.
    def enviar_por_interfaz(self, interfaz_local, trama):
        if interfaz_local not in self.conexiones:
            print(f"{self.nombre}: interfaz {interfaz_local} no conectada")
            return
        dispositivo_destino, interfaz_remota = self.conexiones[interfaz_local]
        print(f"{self.nombre} -> enviando por {interfaz_local} a {dispositivo_destino.nombre}.{interfaz_remota}")
        medio = CapaFisica.encapsular(trama)  # simulación del medio
        # El destino recibe "por el medio" en capa 1
        dispositivo_destino.recibir(medio, 1, self, interfaz_remota)

    # Recibe datos en una capa dada y procesa desencapsulando hasta llegar a aplicación o reenviando
    def recibir(self, datos, capa_actual, dispositivo_anterior=None, interfaz_local=None):
        print(f"{self.nombre} recibió datos en capa {capa_actual}:")
        
        if capa_actual == 1:
            # Capa física: siempre mostramos los bits para depuración
            print(f"  Bits recibidos ({len(datos)} bits): {datos[:64]}...")
            trama = CapaFisica.desencapsular(datos)
            # Sube a capa 2 con la trama de enlace ya decodificada
            self.recibir(trama, 2, dispositivo_anterior, interfaz_local)
            return

        if capa_actual == 2:
            paquete, mac_origen, mac_destino = CapaEnlace.desencapsular(datos)
            print(f"  Enlace: origen MAC={mac_origen}, destino MAC={mac_destino}")
            
            # Determina las MACs locales soportadas por el dispositivo (PC, Switch o Router)
            maces_locales = []
            if hasattr(self, 'MAC_IZQ'): maces_locales.append(self.MAC_IZQ)
            if hasattr(self, 'MAC_DER'): maces_locales.append(self.MAC_DER)
            if hasattr(self, 'MAC'): maces_locales.append(self.MAC)
                
            if mac_destino in maces_locales:
                # La trama es para este dispositivo -> sube a capa 3
                print(f"  Trama para {self.nombre}. Entregando a Capa 3.")
                self.recibir(paquete, 3, dispositivo_anterior, interfaz_local)
                return
            
            # Si la dirección MAC destino no coincide con ninguna dirección local,
            # se consulta la tabla de enlace para determinar la interfaz de salida (conmutación L2).
            interfaz_salida = self.tabla_enlace.get(mac_destino)
            if interfaz_salida:
                if isinstance(self, Router):
                    # Router reescribe MAC origen según la interfaz de salida
                    nueva_mac_origen = self.MAC_IZQ if interfaz_salida == "if_izq" else \
                                       self.MAC_DER if interfaz_salida == "if_der" else getattr(self, 'MAC', 'X')
                    print(f"  Router: reescribo MAC origen -> {nueva_mac_origen} y reenvío por {interfaz_salida}")
                    nueva_trama = CapaEnlace.encapsular(paquete, nueva_mac_origen, mac_destino)
                    self.enviar_por_interfaz(interfaz_salida, nueva_trama)
                else:
                    # Switch no modifica la trama
                    print(f"  Switch: reenvío sin cambios por {interfaz_salida}")
                    self.enviar_por_interfaz(interfaz_salida, datos)
            else:
                print(f"  {self.nombre}: MAC destino {mac_destino} desconocida -> descartar")
            return

        if capa_actual == 3:
            segmento, ip_origen, ip_destino = CapaRed.desencapsular(datos)
            print(f"  Red: origen IP={ip_origen}, destino IP={ip_destino}")
            
            # IPs locales que este dispositivo posee
            ips_locales = []
            if hasattr(self, 'IP_IZQ'): ips_locales.append(self.IP_IZQ)
            if hasattr(self, 'IP_DER'): ips_locales.append(self.IP_DER)
            if hasattr(self, 'IP'): ips_locales.append(self.IP)
                
            if ip_destino in ips_locales:
                # El paquete IP es para mí -> sube a capa 4
                print(f"  Paquete IP destinado a {self.nombre}. Entregando a Capa 4.")
                self.recibir(segmento, 4, dispositivo_anterior, interfaz_local)
                return
            
            # Encaminamiento por IP (router o host con puerta de enlace): IP -> MAC siguiente salto
            siguiente_mac = self.tabla_red.get(ip_destino)
            if siguiente_mac:
                interfaz_salida = self.tabla_enlace.get(siguiente_mac)
                if interfaz_salida:
                    # Determina la MAC origen correcta según interfaz de salida (en router)
                    nueva_mac_origen = self.MAC_IZQ if interfaz_salida == "if_izq" else \
                                       self.MAC_DER if interfaz_salida == "if_der" else getattr(self, 'MAC', 'X')
                    print(f"  Router: siguiente salto MAC {siguiente_mac} por {interfaz_salida} (MAC origen {nueva_mac_origen})")
                    # Re-encapsula a nivel 2 el paquete IP original
                    nueva_trama = CapaEnlace.encapsular(datos, nueva_mac_origen, siguiente_mac)
                    self.enviar_por_interfaz(interfaz_salida, nueva_trama)
                else:
                    print(f"  {self.nombre}: No hay interfaz para la MAC {siguiente_mac}")
            else:
                print(f"  {self.nombre}: No hay ruta para IP {ip_destino}")
            return

        if capa_actual == 4:
            datos_app, protocolo, psrc, pdst = CapaTransporte.desencapsular(datos)
            print(f"  Transporte: protocolo={protocolo}, src={psrc}, dst={pdst}")
            # Entrega a capa de aplicación
            self.recibir(datos_app, 5, dispositivo_anterior, interfaz_local)
            return

        if capa_actual == 5:
            mensaje, app = CapaAplicacion.desencapsular(datos)
            print(f"  Aplicación ({app}): mensaje recibido: '{mensaje}'")
            return

# ====== Dispositivos concretos ======
class PC(Dispositivo):
    # PC con una sola IP y una sola MAC
    def __init__(self, nombre, ip, mac):
        super().__init__(nombre)
        self.IP = ip
        self.MAC = mac

    # Construye y envía un mensaje desde la PC:
    # 1) Capa 5: etiqueta de aplicación
    # 2) Capa 4: segmento transporte
    # 3) Capa 3: paquete IP
    # 4) Capa 2: trama enlace hacia el siguiente salto (MAC)
    # 5) Capa 1: bits y envío por interfaz correspondiente
    def enviar_mensaje(self, mensaje, ip_destino, protocolo="TCP", puerto_destino=TCP_PORT, app="GENERICA"):
        print(f"\n=== {self.nombre} ENVIANDO ({app}) ===")
        
        # Capa de aplicación
        datos_app = CapaAplicacion.encapsular(mensaje, app)
        print(" Capa5 ->", datos_app)
        
        # Capa de transporte (puerto_origen arbitrario fijo 5000 para demo)
        segmento = CapaTransporte.encapsular(datos_app, puerto_origen=5000,
                                             puerto_destino=puerto_destino,
                                             protocolo=protocolo)
        print(" Capa4 ->", segmento)
        
        # Capa de red (IP origen = self.IP)
        paquete = CapaRed.encapsular(segmento, self.IP, ip_destino)
        print(" Capa3 ->", paquete)
        
        # Búsqueda del siguiente salto (MAC) en la tabla de red local de la PC
        siguiente_mac = self.tabla_red.get(ip_destino)
        if not siguiente_mac:
            print(f" {self.nombre}: No hay ruta para {ip_destino}")
            return
        
        # Capa de enlace: MAC origen local y MAC destino = siguiente salto
        trama = CapaEnlace.encapsular(paquete, self.MAC, siguiente_mac)
        print(" Capa2 ->", trama)
        
        # Capa física: mostrar prefijo de bits
        bits = CapaFisica.encapsular(trama)
        print(f" Capa1 -> Bits: {bits[:64]}...")
        
        # Obtener interfaz por la que se alcanza esa MAC (desde tabla_enlace de la PC)
        interfaz_local = self.tabla_enlace.get(siguiente_mac)
        if not interfaz_local:
            print(f" {self.nombre}: No hay interfaz de enlace")
            return
        
        # Envío por la interfaz
        self.enviar_por_interfaz(interfaz_local, trama)

class Router(Dispositivo):
    # Router con dos interfaces: izquierda y derecha (IP y MAC por interfaz)
    def __init__(self, nombre, ip_izq, mac_izq, ip_der, mac_der):
        super().__init__(nombre)
        self.IP_IZQ = ip_izq
        self.MAC_IZQ = mac_izq
        self.IP_DER = ip_der
        self.MAC_DER = mac_der

class Switch(Dispositivo):
    # Switch con una MAC administrativa (para mostrar) y tabla de conmutación
    def __init__(self, nombre, mac):
        super().__init__(nombre)
        self.MAC = mac

# ==============================
# Configuración topología y tablas
# ==============================
# Crea los dispositivos, conecta las interfaces y define tablas de enlace (N2) y de red (N3)
def configurar_red():
    pc1 = PC("PC1", PC1_IP, PC1_MAC)
    pc2 = PC("PC2", PC2_IP, PC2_MAC)
    router = Router("Router1", ROUTER_IP_LEFT, ROUTER_MAC_LEFT, ROUTER_IP_RIGHT, ROUTER_MAC_RIGHT)
    switch1 = Switch("Switch1", SWITCH1_MAC)
    switch2 = Switch("Switch2", SWITCH2_MAC)

    # Conexiones físicas (cableado lógico)
    pc1.conectar("eth0", switch1, "puerto1")
    switch1.conectar("puerto1", pc1, "eth0")
    switch1.conectar("puerto2", router, "if_izq")
    router.conectar("if_izq", switch1, "puerto2")
    router.conectar("if_der", switch2, "puerto2")
    switch2.conectar("puerto2", router, "if_der")
    switch2.conectar("puerto1", pc2, "eth0")
    pc2.conectar("eth0", switch2, "puerto1")

    # Tablas de red/enlace en cada equipo
    # PCs: IP destino -> MAC de siguiente salto (puerta de enlace)
    pc1.tabla_red = {PC2_IP: ROUTER_MAC_LEFT}
    pc1.tabla_enlace = {ROUTER_MAC_LEFT: "eth0"}

    pc2.tabla_red = {PC1_IP: ROUTER_MAC_RIGHT}
    pc2.tabla_enlace = {ROUTER_MAC_RIGHT: "eth0"}

    # Switches: MAC destino -> puerto de salida
    switch1.tabla_enlace = {PC1_MAC: "puerto1", ROUTER_MAC_LEFT: "puerto2"}
    switch2.tabla_enlace = {PC2_MAC: "puerto1", ROUTER_MAC_RIGHT: "puerto2"}

    # Router:
    # - tabla_red: IP destino -> MAC del host final (modelo simplificado sin ARP)
    # - tabla_enlace: MAC -> interfaz por la que alcanzarla
    router.tabla_red = {PC1_IP: PC1_MAC, PC2_IP: PC2_MAC}
    router.tabla_enlace = {PC1_MAC: "if_izq", PC2_MAC: "if_der"}

    return pc1, pc2, router, switch1, switch2

# ==============================
# Interfaz simple CLI
# ==============================
# Bucle principal de interacción: permite elegir dirección, mensaje y aplicación, y dispara el envío
def main():
    pc1, pc2, router, switch1, switch2 = configurar_red()
    print("=== SIMULADOR DE RED SIMPLE ===")
    print("Topología: PC1 - Switch1 - Router1 - Switch2 - PC2")
    
    while True:
        print("\nOpciones para enviar mensaje:")
        print("1) PC1 -> PC2 (UDP)")
        print("2) PC2 -> PC1 (TCP)")
        print("3) Salir")
        opt = input("Selecciona (1-3): ").strip()
        
        if opt in ["1", "2"]:
            msg = input("Mensaje: ")
            print("Selecciona aplicación:")
            print("1) WhatsApp")
            print("2) Messenger")
            print("3) Telegram")
            app_opt = input("App (1-3): ").strip()

            # Mapeo de selección a nombre de app
            if app_opt == "1": app = "WhatsApp"
            elif app_opt == "2": app = "Messenger"
            elif app_opt == "3": app = "Telegram"
            else:
                print("Opción inválida. Se cancela.")
                continue
            
            # Obtiene el código numérico de la app (p. ej., "11" para WhatsApp)
            codigo_app = APP_CODES.get(app, 99)
            if opt == "1":
                # PC1 -> PC2 usando UDP: puerto destino = UDP_PORT
                pc1.enviar_mensaje(msg, PC2_IP, protocolo="UDP", puerto_destino=UDP_PORT, app=codigo_app)
            elif opt == "2":
                # PC2 -> PC1 usando TCP: puerto destino = TCP_PORT
                pc2.enviar_mensaje(msg, PC1_IP, protocolo="TCP", puerto_destino=TCP_PORT, app=codigo_app)
        
        elif opt == "3":
            break
        else:
            print("Opción inválida.")

# Punto de entrada cuando se ejecuta como script
if __name__ == "__main__":
    main()
