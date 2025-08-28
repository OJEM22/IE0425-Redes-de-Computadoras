# ==============================
# Direcciones simplificadas (8 bits como pide la tarea)
# ==============================
PC1_IP = "1"
PC2_IP = "2"

# Router tiene dos interfaces (izq/der) con IPs
ROUTER_IP_LEFT = "3"
ROUTER_IP_RIGHT = "4"

# MACs de 8 bits (representadas como strings de 2 hex o 1 char)
PC1_MAC = "A"
PC2_MAC = "B"
ROUTER_MAC_LEFT = "C"
ROUTER_MAC_RIGHT = "D"
SWITCH1_MAC = "E"
SWITCH2_MAC = "F"

# Puertos ejemplo: TCP = 80, UDP = 53 (elegidos y documentados)
TCP_PORT = 80
UDP_PORT = 53

# ==============================
# CAPAS
# ==============================
class CapaAplicacion:
    @staticmethod
    def encapsular(mensaje, protocolo, puerto_destino):
        # Capa 5: Solo el mensaje (sin encabezado)
        return mensaje
    
    @staticmethod
    def desencapsular(datos):
        # Capa 5: Solo extrae el mensaje
        return datos, "TCP", 80  # Valores por defecto

class CapaTransporte:
    @staticmethod
    def encapsular(datos_app, puerto_origen, protocolo):
        # Capa 4: Añade encabezado de transporte
        encabezado = f"[H4:{protocolo}:{puerto_origen}]"
        return encabezado + datos_app
    
    @staticmethod
    def desencapsular(segmento):
        # Capa 4: Remueve encabezado de transporte
        fin = segmento.find(']') + 1
        encabezado = segmento[:fin]
        datos_app = segmento[fin:]
        partes = encabezado[1:-1].split(':')
        protocolo = partes[1]
        puerto_origen = int(partes[2])
        return datos_app, protocolo, puerto_origen

class CapaRed:
    @staticmethod
    def encapsular(segmento, ip_origen, ip_destino):
        # Capa 3: Añade encabezado de red
        encabezado = f"[H3:{ip_origen}:{ip_destino}]"
        return encabezado + segmento
    
    @staticmethod
    def desencapsular(paquete):
        # Capa 3: Remueve encabezado de red
        fin = paquete.find(']') + 1
        encabezado = paquete[:fin]
        segmento = paquete[fin:]
        partes = encabezado[1:-1].split(':')
        ip_origen = partes[1]
        ip_destino = partes[2]
        return segmento, ip_origen, ip_destino

class CapaEnlace:
    @staticmethod
    def encapsular(paquete, mac_origen, mac_destino):
        # Capa 2: Añade encabezado de enlace
        encabezado = f"[H2:{mac_origen}:{mac_destino}]"
        return encabezado + paquete
    
    @staticmethod
    def desencapsular(trama):
        # Capa 2: Remueve encabezado de enlace
        fin = trama.find(']') + 1
        encabezado = trama[:fin]
        paquete = trama[fin:]
        partes = encabezado[1:-1].split(':')
        mac_origen = partes[1]
        mac_destino = partes[2]
        return paquete, mac_origen, mac_destino

#FIXME: Ricardo, aqui se transforma en bits para la capa fisica 2 , pero no se si es lo que quiere el profe
# para que revise eso y le eche un ojo bien si todo dentro de cada capa tiene sentido (revise si teoricamente 
# cada capa hace lo que deberia) PD:haga los cambios que quiera.
# Tambien que los bits recibidos se imprimen unicamente en las PC no en los switch o en los routers, 
# para que se fije que es lo que quiere el profe

class CapaFisica:
    @staticmethod
    def encapsular(trama):
        """Capa 1: Convierte a bits (simulación muy simplificada)"""
        # Simulamos la conversión a bits representándolo como una cadena de 0s y 1s
        bits = ''.join(format(ord(c), '08b') for c in trama)
        return bits
    
    @staticmethod
    def desencapsular(bits):
        """Convierte bits a trama"""
        # Convertimos la cadena de bits de vuelta a caracteres
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            chars.append(chr(int(byte, 2)))
        return ''.join(chars)
    
# ==============================
# Dispositivos
# ==============================
class Dispositivo:
    def __init__(self, nombre):
        self.nombre = nombre
        # conexiones: nombre_interfaz_local -> (dispositivo_remoto, interfaz_remota)
        self.conexiones = {}
        # tablas
        self.tabla_enlace = {}  # MAC -> interfaz_local (simple)
        self.tabla_red = {}     # IP -> next_hop_MAC (simple)

    def conectar(self, interfaz_local, dispositivo_destino, interfaz_remota):
        self.conexiones[interfaz_local] = (dispositivo_destino, interfaz_remota)

    # enviar por interfaz local (pasa por capa física antes de llegar al vecino)
    def enviar_por_interfaz(self, interfaz_local, trama_o_bits):
        if interfaz_local not in self.conexiones:
            print(f"{self.nombre}: interfaz {interfaz_local} no conectada")
            return
        dispositivo_destino, interfaz_remota = self.conexiones[interfaz_local]
        # en el "medio" la señal viaja por la interfaz remota del destino:
        # simulamos enviando al dispositivo destino el contenido por Capa Física (layer 1)
        print(f"{self.nombre} -> enviando por {interfaz_local} a {dispositivo_destino.nombre}.{interfaz_remota}")
        # envolver en física (si corresponde) antes de colocar en el medio
        medio = CapaFisica.encapsular(trama_o_bits)
        
        dispositivo_destino.recibir(medio, 1, self, interfaz_remota)

    # recibir: layer indica la capa a la que llegan los datos (1..5)
    def recibir(self, datos, capa_actual, dispositivo_anterior=None, interfaz_local=None):
        print(f"{self.nombre} recibió datos en capa {capa_actual}:")
        
        if capa_actual == 1:
            if isinstance(self,PC):
                # MOSTRAR BITS RECIBIDOS EN CONSOLA
                print(f"  Bits recibidos ({len(datos)} bits): {datos[:64]}...")  # Mostrar primeros 64 bits
            trama = CapaFisica.desencapsular(datos)
            self.recibir(trama, 2, dispositivo_anterior, interfaz_local)
            return

        if capa_actual == 2:
            paquete, mac_origen, mac_destino = CapaEnlace.desencapsular(datos)
            print(f"  Enlace: origen MAC={mac_origen}, destino MAC={mac_destino}")
            print(" Capa2 ->", datos)
            
            # VERIFICAR SI LA MAC DESTINO ES PARA ESTE ROUTER
            maces_locales = []
            if hasattr(self, 'MAC_IZQ'):
                maces_locales.append(self.MAC_IZQ)
            if hasattr(self, 'MAC_DER'):
                maces_locales.append(self.MAC_DER)
            if hasattr(self, 'MAC'):
                maces_locales.append(self.MAC)
                
            if mac_destino in maces_locales:
                print(f"  Trama para {self.nombre} (MAC destino {mac_destino} coincide). Entregando a Capa 3.")
                self.recibir(paquete, 3, dispositivo_anterior, interfaz_local)
                return
            
            # Si no es para el router, hacer forwarding
            interfaz_salida = self.tabla_enlace.get(mac_destino)
            if interfaz_salida:
                print(f"  {self.nombre} forwardea trama por interfaz {interfaz_salida}")
                
                # Determinar qué MAC usar como origen
                if interfaz_salida == "if_izq":
                    nueva_mac_origen = self.MAC_IZQ
                elif interfaz_salida == "if_der":
                    nueva_mac_origen = self.MAC_DER
                else:
                    nueva_mac_origen = getattr(self, 'MAC', 'X')
                    
                nueva_trama = CapaEnlace.encapsular(paquete, nueva_mac_origen, mac_destino)
                self.enviar_por_interfaz(interfaz_salida, nueva_trama)
            else:
                print(f"  {self.nombre}: MAC destino {mac_destino} desconocida -> descartar")
            return

        if capa_actual == 3:
            segmento, ip_origen, ip_destino = CapaRed.desencapsular(datos)
            print(f"  Red: origen IP={ip_origen}, destino IP={ip_destino}")
            print(" Capa3 ->", datos)
            
            # VERIFICAR SI LA IP DESTINO ES PARA ESTE ROUTER
            ips_locales = []
            if hasattr(self, 'IP_IZQ'):
                ips_locales.append(self.IP_IZQ)
            if hasattr(self, 'IP_DER'):
                ips_locales.append(self.IP_DER)
            if hasattr(self, 'IP'):
                ips_locales.append(self.IP)
                
            if ip_destino in ips_locales:
                print(f"  Paquete IP destinado a {self.nombre}. Entregando a Capa 4.")
                self.recibir(segmento, 4, dispositivo_anterior, interfaz_local)
                return
            
            # Hacer routing basado en IP destino
            siguiente_mac = self.tabla_red.get(ip_destino)
            if siguiente_mac:
                print(f"  {self.nombre} rutea IP {ip_destino} hacia MAC {siguiente_mac}")
                
                # Determinar interfaz de salida para esa MAC
                interfaz_salida = self.tabla_enlace.get(siguiente_mac)
                if interfaz_salida:
                    # Determinar qué MAC usar como origen
                    if interfaz_salida == "if_izq":
                        nueva_mac_origen = self.MAC_IZQ
                    elif interfaz_salida == "if_der":
                        nueva_mac_origen = self.MAC_DER
                    else:
                        nueva_mac_origen = getattr(self, 'MAC', 'X')
                    
                    # Re-encapsular con nuevas MACs
                    nueva_trama = CapaEnlace.encapsular(datos, nueva_mac_origen, siguiente_mac)
                    self.enviar_por_interfaz(interfaz_salida, nueva_trama)
                else:
                    print(f"  {self.nombre}: No hay interfaz para la MAC {siguiente_mac}")
            else:
                print(f"  {self.nombre}: No hay ruta para IP {ip_destino}")
            return

        if capa_actual == 4:
            datos_app, protocolo, puerto_origen = CapaTransporte.desencapsular(datos)
            print(f"  Transporte: protocolo={protocolo}, puerto_origen={puerto_origen}")
            print(" Capa4 ->", datos)
            self.recibir(datos_app, 5, dispositivo_anterior, interfaz_local)
            return

        if capa_actual == 5:
            mensaje, protocolo, puerto_destino = CapaAplicacion.desencapsular(datos)
            print(f"  Aplicación: mensaje recibido: '{mensaje}'")
            print(" Capa5 ->", datos)
            return

# ====== Dispositivos concretos ======
class PC(Dispositivo):
    def __init__(self, nombre, ip, mac):
        super().__init__(nombre)
        self.IP = ip
        self.MAC = mac

    def enviar_mensaje(self, mensaje, ip_destino, protocolo="TCP", puerto_destino=TCP_PORT):
        print(f"\n=== {self.nombre} ENVIANDO ===")
        
        # Capa 5: Aplicación (solo el mensaje)
        datos_app = CapaAplicacion.encapsular(mensaje, protocolo, puerto_destino)
        print(" Capa5 ->", datos_app)
        
        # Capa 4: Transporte (añade H4)
        puerto_origen = 5000
        segmento = CapaTransporte.encapsular(datos_app, puerto_origen, protocolo)
        print(" Capa4 ->", segmento)
        
        # Capa 3: Red (añade H3)
        paquete = CapaRed.encapsular(segmento, self.IP, ip_destino)
        print(" Capa3 ->", paquete)
        
        # Capa 2: Enlace (añade H2)
        siguiente_mac = self.tabla_red.get(ip_destino)
        if not siguiente_mac:
            print(f" {self.nombre}: No hay entrada de ruta para IP destino {ip_destino}")
            return
        trama = CapaEnlace.encapsular(paquete, self.MAC, siguiente_mac)
        print(" Capa2 ->", trama)
        
        # Capa 1: Física
        bits = CapaFisica.encapsular(trama)
        print(f" Capa1 -> Bits: {bits[:64]}...")  # Mostrar primeros 64 bits

        # Enviar por la interfaz
        interfaz_local = self.tabla_enlace.get(siguiente_mac)
        if not interfaz_local:
            print(f" {self.nombre}: No hay interfaz de enlace para enviar a MAC {siguiente_mac}")
            return
        
        self.enviar_por_interfaz(interfaz_local, trama)

class Router(Dispositivo):
    def __init__(self, nombre, ip_izq, mac_izq, ip_der, mac_der):
        super().__init__(nombre)
        self.IP_IZQ = ip_izq
        self.MAC_IZQ = mac_izq
        self.IP_DER = ip_der
        self.MAC_DER = mac_der

class Switch(Dispositivo):
    def __init__(self, nombre, mac):
        super().__init__(nombre)
        self.MAC = mac

# ==============================
# Configuración topología y tablas
# ==============================
def configurar_red():
    pc1 = PC("PC1", PC1_IP, PC1_MAC)
    pc2 = PC("PC2", PC2_IP, PC2_MAC)
    router = Router("Router1", ROUTER_IP_LEFT, ROUTER_MAC_LEFT, ROUTER_IP_RIGHT, ROUTER_MAC_RIGHT)
    switch1 = Switch("Switch1", SWITCH1_MAC)
    switch2 = Switch("Switch2", SWITCH2_MAC)

    # Conexiones físicas
    pc1.conectar("eth0", switch1, "puerto1")
    switch1.conectar("puerto1", pc1, "eth0")
    switch1.conectar("puerto2", router, "if_izq")
    router.conectar("if_izq", switch1, "puerto2")
    router.conectar("if_der", switch2, "puerto2")
    switch2.conectar("puerto2", router, "if_der")
    switch2.conectar("puerto1", pc2, "eth0")
    pc2.conectar("eth0", switch2, "puerto1")

    # Tablas de enlace y routing CORREGIDAS
    # PC1: Para llegar a PC2, debe enviar al router (no al switch directamente)
    pc1.tabla_red = {PC2_IP: ROUTER_MAC_LEFT}  # IP destino -> MAC del router
    pc1.tabla_enlace = {ROUTER_MAC_LEFT: "eth0"}  # MAC router -> interfaz eth0

    # PC2: Para llegar a PC1, debe enviar al router
    pc2.tabla_red = {PC1_IP: ROUTER_MAC_RIGHT}  # IP destino -> MAC del router
    pc2.tabla_enlace = {ROUTER_MAC_RIGHT: "eth0"}  # MAC router -> interfaz eth0

    # Switch1: Conoce las MACs conectadas a sus puertos
    switch1.tabla_enlace = {
        PC1_MAC: "puerto1",           # PC1 conectado al puerto1
        ROUTER_MAC_LEFT: "puerto2"    # Router conectado al puerto2
    }

    # Switch2: Conoce las MACs conectadas a sus puertos
    switch2.tabla_enlace = {
        PC2_MAC: "puerto1",           # PC2 conectado al puerto1
        ROUTER_MAC_RIGHT: "puerto2"   # Router conectado al puerto2
    }

    # Router: tabla de routing - enviar a la MAC del host destino
    router.tabla_red = {
        PC1_IP: PC1_MAC,  # IP 1 -> MAC A (PC1)
        PC2_IP: PC2_MAC   # IP 2 -> MAC B (PC2)
    }

    # Router: tabla de enlace - saber por qué interfaz enviar para llegar a esas MACs
    router.tabla_enlace = {
        PC1_MAC: "if_izq",  # MAC A -> interfaz izquierda (vía Switch1)
        PC2_MAC: "if_der"   # MAC B -> interfaz derecha (vía Switch2)
    }

    return pc1, pc2, router, switch1, switch2

#FIXME: Leonardo, necesito que revise si el flujo de como recibe cada dispositivo las varas es teoricamente correcto
# ==============================
# Interfaz simple CLI
# ==============================
def main():
    pc1, pc2, router, switch1, switch2 = configurar_red()
    print("=== SIMULADOR DE RED SIMPLE ===")
    print("Topología: PC1 - Switch1 - Router1 - Switch2 - PC2")
    while True:
        print("\nOpciones para enviar mensaje:")
        print("1) PC1 -> PC2")
        print("2) PC2 -> PC1")
        print("3) Salir")
        opt = input("Selecciona (1-3): ").strip()
        if opt == "1":
            msg = input("Mensaje desde PC1: ")
            pc1.enviar_mensaje(msg, PC2_IP, protocolo="TCP", puerto_destino=TCP_PORT)
        elif opt == "2":
            msg = input("Mensaje desde PC2: ")
            pc2.enviar_mensaje(msg, PC1_IP, protocolo="TCP", puerto_destino=TCP_PORT)
        elif opt == "3":
            break
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()
