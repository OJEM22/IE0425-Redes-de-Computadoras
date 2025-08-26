# ==============================
# DEFINICIÓN DE DIRECCIONES SIMPLIFICADAS
# ==============================

# Usaremos números simples para las direcciones como se solicitó
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

# ==============================
# DEFINICIÓN DE CAPAS Y ENCAPSULACIÓN
# ==============================

class CapaAplicacion:
    @staticmethod
    def encapsular(mensaje, protocolo, puerto_destino):
        """Capa 5: Añade información de aplicación"""
        # En esta simulación simplificada, solo añadimos el protocolo y puerto
        encabezado = f"[AP:{protocolo}:{puerto_destino}]"
        return encabezado + mensaje
    
    @staticmethod
    def desencapsular(datos):
        """Remueve encabezado de aplicación"""
        # Buscamos el final del encabezado
        fin_encabezado = datos.find(']') + 1
        encabezado = datos[:fin_encabezado]
        mensaje = datos[fin_encabezado:]
        
        # Extraemos información del encabezado
        partes = encabezado[1:-1].split(':')  # Removemos corchetes y dividimos
        protocolo = partes[1]
        puerto = partes[2]
        
        return mensaje, protocolo, puerto

class CapaTransporte:
    @staticmethod
    def encapsular(datos_app, puerto_origen):
        """Capa 4: Añade información de transporte"""
        # Simplemente añadimos el puerto de origen
        encabezado = f"[TR:{puerto_origen}]"
        return encabezado + datos_app
    
    @staticmethod
    def desencapsular(segmento):
        """Remueve encabezado de transporte"""
        fin_encabezado = segmento.find(']') + 1
        encabezado = segmento[:fin_encabezado]
        datos_app = segmento[fin_encabezado:]
        
        partes = encabezado[1:-1].split(':')
        puerto_origen = partes[1]
        
        return datos_app, puerto_origen

class CapaRed:
    @staticmethod
    def encapsular(segmento, ip_origen, ip_destino):
        """Capa 3: Añade información de red (direcciones IP)"""
        encabezado = f"[RE:{ip_origen}:{ip_destino}]"
        return encabezado + segmento
    
    @staticmethod
    def desencapsular(paquete):
        """Remueve encabezado de red"""
        fin_encabezado = paquete.find(']') + 1
        encabezado = paquete[:fin_encabezado]
        segmento = paquete[fin_encabezado:]
        
        partes = encabezado[1:-1].split(':')
        ip_origen = partes[1]
        ip_destino = partes[2]
        
        return segmento, ip_origen, ip_destino

class CapaEnlace:
    @staticmethod
    def encapsular(paquete, mac_origen, mac_destino):
        """Capa 2: Añade información de enlace (direcciones MAC)"""
        encabezado = f"[EN:{mac_origen}:{mac_destino}]"
        return encabezado + paquete
    
    @staticmethod
    def desencapsular(trama):
        """Remueve encabezado de enlace"""
        fin_encabezado = trama.find(']') + 1
        encabezado = trama[:fin_encabezado]
        paquete = trama[fin_encabezado:]
        
        partes = encabezado[1:-1].split(':')
        mac_origen = partes[1]
        mac_destino = partes[2]
        
        return paquete, mac_origen, mac_destino

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
# DISPOSITIVOS DE RED SIMPLIFICADOS
# ==============================

class Dispositivo:
    def __init__(self, nombre):
        self.nombre = nombre
        self.tabla_red = {}  # Tabla de ruteo simplificada: IP -> siguiente salto MAC
        self.tabla_enlace = {}  # Tabla de forwarding simplificada: MAC -> interfaz
    
    def recibir(self, datos, capa_actual, dispositivo_anterior=None):
        """Método genérico para recibir datos"""
        print(f"{self.nombre} recibió datos en capa {capa_actual}:")
        print(datos)
        print("---")
        
        # Determinar qué hacer según la capa
        if capa_actual == 1:  # Capa física
            trama = CapaFisica.desencapsular(datos)
            self.recibir(trama, 2, dispositivo_anterior)
            
        elif capa_actual == 2:  # Capa de enlace
            paquete, mac_origen, mac_destino = CapaEnlace.desencapsular(datos)
            
            # Verificar si es para nosotros
            if mac_destino in [getattr(self, attr) for attr in dir(self) if attr.endswith('_MAC')]:
                print(f"Trama destinada a este dispositivo ({self.nombre})")
                self.recibir(paquete, 3, dispositivo_anterior)
            else:
                # Forwardear a siguiente dispositivo
                siguiente_mac = self.tabla_enlace.get(mac_destino)
                if siguiente_mac:
                    print(f"Forwardeando trama a MAC {siguiente_mac}")
                    # Re-encapsular con nuevas MACs
                    nueva_trama = CapaEnlace.encapsular(paquete, getattr(self, 'MAC', 'X'), siguiente_mac)
                    # Enviar a capa física
                    bits = CapaFisica.encapsular(nueva_trama)
                    # En simulación real, aquí enviaríamos al siguiente dispositivo
                else:
                    print("No se encuentra MAC destino en tabla de forwarding")
        
        elif capa_actual == 3:  # Capa de red
            segmento, ip_origen, ip_destino = CapaRed.desencapsular(datos)
            
            # Verificar si es para nosotros
            if ip_destino in [getattr(self, attr) for attr in dir(self) if attr.endswith('_IP')]:
                print(f"Paquete IP destinado a este dispositivo ({self.nombre})")
                self.recibir(segmento, 4, dispositivo_anterior)
            else:
                # Ruteo a siguiente salto
                siguiente_mac = self.tabla_red.get(ip_destino)
                if siguiente_mac:
                    print(f"Ruteando paquete a MAC {siguiente_mac}")
                    # Re-encapsular con nuevas direcciones
                    # En simulación real, aquí pasaríamos a capa de enlace
                else:
                    print("No se encuentra ruta para IP destino")
        
        elif capa_actual == 4:  # Capa de transporte
            datos_app, puerto_origen = CapaTransporte.desencapsular(datos)
            self.recibir(datos_app, 5, dispositivo_anterior)
        
        elif capa_actual == 5:  # Capa de aplicación
            mensaje, protocolo, puerto_destino = CapaAplicacion.desencapsular(datos)
            print(f"Mensaje recibido: {mensaje}")

class PC(Dispositivo):
    def __init__(self, nombre, ip, mac):
        super().__init__(nombre)
        self.IP = ip
        self.MAC = mac
    
    def enviar_mensaje(self, mensaje, ip_destino, protocolo="TCP", puerto_destino=80):
        """Envía un mensaje a través de la red"""
        print(f"\n=== {self.nombre} ENVIANDO MENSAJE ===")
        
        # Encapsulación capa por capa
        print("Capa 5 (Aplicación):")
        datos_app = CapaAplicacion.encapsular(mensaje, protocolo, puerto_destino)
        print(datos_app)
        
        print("\nCapa 4 (Transporte):")
        puerto_origen = 5000  # Puerto efímero
        segmento = CapaTransporte.encapsular(datos_app, puerto_origen)
        print(segmento)
        
        print("\nCapa 3 (Red):")
        paquete = CapaRed.encapsular(segmento, self.IP, ip_destino)
        print(paquete)
        
        print("\nCapa 2 (Enlace):")
        # Determinar siguiente salto (MAC del router o switch)
        siguiente_mac = self.tabla_red.get(ip_destino, ROUTER_MAC_LEFT)
        trama = CapaEnlace.encapsular(paquete, self.MAC, siguiente_mac)
        print(trama)
        
        print("\nCapa 1 (Física):")
        bits = CapaFisica.encapsular(trama)
        print(bits)
        
        print("\n=== ENVÍO COMPLETO ===")
        
        # En simulación real, aquí enviaríamos los bits al siguiente dispositivo
        return bits

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
# CONFIGURACIÓN DE LA RED
# ==============================

def configurar_red():
    """Configura la red según el diagrama"""
    
    # Crear dispositivos
    pc1 = PC("PC 1", PC1_IP, PC1_MAC)
    pc2 = PC("PC 2", PC2_IP, PC2_MAC)
    router = Router("Router 1", ROUTER_IP_LEFT, ROUTER_MAC_LEFT, ROUTER_IP_RIGHT, ROUTER_MAC_RIGHT)
    switch1 = Switch("Switch 1", SWITCH1_MAC)
    switch2 = Switch("Switch 2", SWITCH2_MAC)
    
    # Configurar tablas de ruteo (simplificado)
    pc1.tabla_red = {PC2_IP: ROUTER_MAC_LEFT}  # Para llegar a PC2, usar MAC del router
    pc2.tabla_red = {PC1_IP: ROUTER_MAC_RIGHT}  # Para llegar a PC1, usar MAC del router
    
    router.tabla_red = {
        PC1_IP: SWITCH1_MAC,  # Para llegar a PC1, usar MAC del switch1
        PC2_IP: SWITCH2_MAC   # Para llegar a PC2, usar MAC del switch2
    }
    
    # Configurar tablas de forwarding (simplificado)
    pc1.tabla_enlace = {ROUTER_MAC_LEFT: "eth0"}
    pc2.tabla_enlace = {ROUTER_MAC_RIGHT: "eth0"}
    
    switch1.tabla_enlace = {
        PC1_MAC: "puerto1",
        ROUTER_MAC_LEFT: "puerto2"
    }
    
    switch2.tabla_enlace = {
        PC2_MAC: "puerto1",
        ROUTER_MAC_RIGHT: "puerto2"
    }
    
    router.tabla_enlace = {
        SWITCH1_MAC: "interfaz_izq",
        SWITCH2_MAC: "interfaz_der"
    }
    
    return pc1, pc2, router, switch1, switch2

# ==============================
# INTERFAZ DE USUARIO
# ==============================

def main():
    """Función principal"""
    print("=== SIMULADOR DE REDES ===")
    print("Configurando red...")
    pc1, pc2, router, switch1, switch2 = configurar_red()
    
    while True:
        print("\n¿Qué deseas hacer?")
        print("1. Enviar mensaje de PC1 a PC2")
        print("2. Enviar mensaje de PC2 a PC1")
        print("3. Salir")
        
        opcion = input("Selecciona una opción (1-3): ")
        
        if opcion == "1":
            mensaje = input("Ingresa el mensaje a enviar: ")
            pc1.enviar_mensaje(mensaje, PC2_IP)
            
            # Simular recepción en PC2 (simplificado)
            print(f"\n=== SIMULANDO RECEPCIÓN EN {pc2.nombre} ===")
            bits = pc1.enviar_mensaje(mensaje, PC2_IP)
            pc2.recibir(bits, 1, pc1)
            
        elif opcion == "2":
            mensaje = input("Ingresa el mensaje a enviar: ")
            pc2.enviar_mensaje(mensaje, PC1_IP)
            
            # Simular recepción en PC1 (simplificado)
            print(f"\n=== SIMULANDO RECEPCIÓN EN {pc1.nombre} ===")
            bits = pc2.enviar_mensaje(mensaje, PC1_IP)
            pc1.recibir(bits, 1, pc2)
            
        elif opcion == "3":
            print("Saliendo del simulador...")
            break
        
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
