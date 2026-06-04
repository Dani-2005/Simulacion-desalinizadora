import pygame
import math
import random

class CaptacionMar:
    def __init__(self, x, y, ancho, alto):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto
        
        # Caudal base de captación
        self.caudal_nominal = 15.0  
        
        # Animación estilo juego 2D: Inicializamos parches de brillo/espuma flotantes
        # Cada brillo tiene: [x_relativa, y_relativa, ancho, alto, desfase_tiempo, velocidad]
        self.brillos_mar = []
        random.seed(42) # Semilla fija para mantener consistencia visual al arrancar
        
        # Generamos una matriz de 15 texturas de agua flotantes distribuidas por el foso
        for _ in range(15):
            self.brillos_mar.append({
                'x': random.randint(10, self.ancho - 30),
                'y': random.randint(10, self.alto - 15),
                'ancho': random.randint(12, 28),
                'alto': random.randint(3, 5),
                'desfase': random.uniform(0, 100),
                'velocidad': random.choice([0.03, 0.05, 0.07])
            })

    def actualizar(self, estado_sistema):
        # Enfoque de videojuego: Los brillos flotan horizontalmente y oscilan
        if estado_sistema != "FALLA_ELECTRICA":
            for brillo in self.brillos_mar:
                # Movimiento horizontal continuo hacia la izquierda (simulando corriente de succión)
                brillo['x'] -= 0.4
                # Si el brillo sale del foso por la izquierda, reaparece en la derecha
                if brillo['x'] < 5:
                    brillo['x'] = self.ancho - random.randint(20, 40)
                    brillo['y'] = random.randint(10, self.alto - 15)
                
                # Avanzar el ciclo de oscilación para el efecto de parpadeo/escalado
                brillo['desfase'] += brillo['velocidad']
                
        # Retorno de caudales del simulador
        if estado_sistema == "FALLA_ELECTRICA":
            return 0.0
        elif estado_sistema == "FALLA_CAPTACION":
            return self.caudal_nominal * 0.15
        elif estado_sistema == "MANTENIMIENTO_FILTROS":
            return self.caudal_nominal * 0.5
        else:
            return self.caudal_nominal

    def dibujar(self, superficie, estado_sistema, fuente):
        # 1. PALETA DE COLORES ESTILO VIDEOJUEGO RETRO (Colores planos y contrastantes)
        if estado_sistema == "FALLA_ELECTRICA":
            color_fondo_mar = (24, 44, 61)     # Azul apagado estancado
            color_brillo_agua = (33, 58, 79)   # Brillos opacados casi invisibles
        else:
            color_fondo_mar = (18, 93, 152)    # Azul plano vivo de juego arcade
            color_brillo_agua = (79, 175, 227) # Celeste cian vibrante para la espuma

        # Pintar el contenedor base del agua
        pygame.draw.rect(superficie, color_fondo_mar, (self.x, self.y, self.ancho, self.alto))

        # 2. RENDERIZADO DE LOS PARCHES DE BRILLO 2D
        # Dibujamos píldoras redondeadas de color cian que cambian de tamaño con math.cos
        for brillo in self.brillos_mar:
            # Escalado senoidal dinámico: hace que los brillos se estiren y encojan estéticamente
            factor_escala = math.cos(brillo['desfase'])
            ancho_dinamico = int(brillo['ancho'] * (0.7 + abs(factor_escala) * 0.5))
            
            # Posición final en pantalla sumando las coordenadas absolutas del módulo
            pos_x = int(self.x + brillo['x'])
            pos_y = int(self.y + brillo['y'])
            
            # Asegurar que el estiramiento visual no dibuje elementos fuera del recuadro
            if pos_x + ancho_dinamico < self.x + self.ancho - 5:
                # Dibujamos las "cápsulas" de brillo de agua típicas de los juegos pixelados
                pygame.draw.rect(
                    superficie, 
                    color_brillo_agua, 
                    (pos_x, pos_y, ancho_dinamico, brillo['alto']), 
                    border_radius=2
                )
                
                # Un pequeño detalle extra de espuma blanca en el centro si el sistema está a tope
                if estado_sistema == "OPERATIVO" and brillo['ancho'] > 20:
                    pygame.draw.rect(
                        superficie, 
                        (230, 245, 255), 
                        (pos_x + 4, pos_y + 1, ancho_dinamico // 2, 2), 
                        border_radius=1
                    )

        # 3. MARCO / BORDE GRUESO DEL ESCENARIO
        pygame.draw.rect(superficie, (41, 45, 50), (self.x, self.y, self.ancho, self.alto), width=3, border_radius=2)

        # 4. TEXTO DE LA INTERFAZ CON COLORES AGRESIVOS/RETRO
        texto = fuente.render("FOSO DE CAPTACIÓN", True, (240, 245, 250))
        superficie.blit(texto, (self.x + 12, self.y + 12))


class TuberiaAnimada:
    def __init__(self, x_inicio, y_inicio, x_fin, y_fin):
        self.x_inicio = x_inicio
        self.y_inicio = y_inicio
        self.x_fin = x_fin
        self.y_fin = y_fin
        
        # MEJORA: Sistema de partículas dinámicas fluidas (incrementado a un comportamiento estocástico continuo)
        self.particulas = []
        distancia_total = math.hypot(x_fin - x_inicio, y_fin - y_inicio)
        num_particulas = max(5, int(distancia_total / 18))
        for _ in range(num_particulas):
            self.particulas.append(random.uniform(0.0, 1.0))
            
        self.velocidad = 0.02

    def actualizar(self, estado_sistema):
        # Las tuberías solo se mueven si la planta está operando de forma continua
        if estado_sistema == "OPERATIVO":
            for i in range(len(self.particulas)):
                self.particulas[i] += self.velocidad
                if self.particulas[i] > 1.0:
                    self.particulas[i] = 0.0

    def dibujar(self, pantalla):
        # Dibujar la tubería base avanzada (Fondo metalizado multicapa estilo SCADA)
        pygame.draw.line(pantalla, (45, 50, 60), (self.x_inicio, self.y_inicio), (self.x_fin, self.y_fin), 8)
        pygame.draw.line(pantalla, (80, 85, 95), (self.x_inicio, self.y_inicio), (self.x_fin, self.y_fin), 4)
        
        # Dibujar gotas de agua en movimiento interno (Círculos celestes brillantes)
        for p in self.particulas:
            x_actual = self.x_inicio + (self.x_fin - self.x_inicio) * p
            y_actual = self.y_inicio + (self.y_fin - self.y_inicio) * p
            pygame.draw.circle(pantalla, (0, 210, 255), (int(x_actual), int(y_actual)), 3)


class TanquePulmon:
    def __init__(self, x, y, ancho, alto, capacidad_maxima):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.capacidad_maxima = capacidad_maxima
        self.nivel_actual = 800.0  # Empezamos con una base saludable de agua

        # MEJORA: Carga del sprite de almacenamiento industrial
        try:
            self.sprite_tanque = pygame.image.load("assets/pulmon.png").convert_alpha()
            self.sprite_tanque = pygame.transform.scale(self.sprite_tanque, (ancho, alto))
        except:
            self.sprite_tanque = None

    def actualizar(self, agua_entrada, estado_sistema):
        # El agua que entra de la ósmosis llena el tanque
        self.nivel_actual += agua_entrada
        
        # NOTA: El consumo artificial de -0.8 SE ELIMINÓ. 
        # Ahora el agua se restará ÚNICAMENTE cuando un camión esté en el llenadero.
        
        # Mantener los niveles dentro de los límites físicos
        if self.nivel_actual < 0: self.nivel_actual = 0
        if self.nivel_actual > self.capacidad_maxima: self.nivel_actual = self.capacidad_maxima

    def dibujar(self, pantalla, fuente):
        porcentaje = self.nivel_actual / self.capacidad_maxima
        alto_agua = int(self.rect.height * porcentaje)
        
        col_agua = (0, 150, 255)
        if porcentaje < 0.20:
            col_agua = (255, 50, 50) if (pygame.time.get_ticks() // 250) % 2 == 0 else (100, 0, 0)

        # Si el sprite existe, dibujamos la estructura industrial limpia (sin agua detrás)
        if self.sprite_tanque:
            # Dibujamos el armazón metalizado y escaleras del tanque
            pantalla.blit(self.sprite_tanque, (self.rect.x, self.rect.y))
        else:
            # Respaldo geométrico tradicional (limpio, sin agua interna)
            pygame.draw.rect(pantalla, (60, 64, 70), self.rect, border_radius=10)
            pygame.draw.rect(pantalla, (200, 200, 200), self.rect, width=2, border_radius=10)

        # NUEVA LÓGICA: Dibujamos el agua como una línea vertical indicadora al lado derecho
        if alto_agua > 0:
            x_linea = self.rect.right + 8      # Separación de 8 píxeles a la derecha del tanque
            y_base_linea = self.rect.bottom    # Punto inferior de la línea alineado a la base
            y_inicio_linea = y_base_linea - alto_agua
            
            # Dibujamos la línea indicadora con un grosor de 6 píxeles
            pygame.draw.line(pantalla, col_agua, (x_linea, y_base_linea), (x_linea, y_inicio_linea), width=6)

        txt_nom = fuente.render("TANQUE PULMÓN", True, (255, 255, 255))
        txt_volumen = fuente.render(f"{int(self.nivel_actual)} L / {int(self.capacidad_maxima)} L", True, (220, 220, 220))
        txt_porcentaje = fuente.render(f"{int(porcentaje * 100)}%", True, (255, 255, 255))
        
        pantalla.blit(txt_nom, (self.rect.x - 10, self.rect.y - 22))
        pantalla.blit(txt_volumen, (self.rect.x - 10, self.rect.bottom + 8))
        pantalla.blit(txt_porcentaje, (self.rect.centerx - 12, self.rect.centery - 8))


class Camion:
    def __init__(self, x_inicio, y_llenadero):
        self.x = x_inicio
        self.y = y_llenadero
        # Ajustamos el tamaño lógico a la escala real de la imagen horizontal
        self.ancho = 85
        self.alto = 38
        self.velocidad = 2
        self.capacidad_total = 400.0  
        self.carga_actual = 0.0
        # Estados: "AVANZANDO", "CARGANDO", "SALIENDO", "DESVIANDO"
        self.estado = "AVANZANDO"  

        # MEJORA: Carga y pre-configuración de la textura horizontal de la cisterna
        try:
            # Cargamos tu archivo modificado (asumiendo que se llama camion.png en assets)
            self.sprite_base = pygame.image.load("assets/camion.png").convert_alpha()
            
            # Como la imagen ya es horizontal, solo la escalamos al tamaño óptimo directo
            self.sprite_horizontal = pygame.transform.scale(self.sprite_base, (self.ancho, self.alto))
            
            # Para el desvío hacia abajo, rotamos la horizontal -90 grados (sentido horario)
            # para que la cabina apunte perfectamente hacia el fondo de la pantalla
            self.sprite_vertical = pygame.transform.scale(self.sprite_base, (self.ancho, self.alto))
            self.sprite_vertical = pygame.transform.rotate(self.sprite_vertical, -90)
        except:
            self.sprite_base = None

    def actualizar(self, x_destino, es_primero, tanque):
        if self.estado == "AVANZANDO":
            if self.x > x_destino:
                self.x -= self.velocidad
            elif es_primero:
                self.estado = "CARGANDO"

        elif self.estado == "CARGANDO":
            # --- VÁLVULA DE CONTROL INDUSTRIAL PROPORCIONAL ---
            porcentaje_tanque = tanque.nivel_actual / tanque.capacidad_maxima
            tasa_succion = 1.2 * porcentaje_tanque
            tasa_succion = max(0.1, tasa_succion)
            
            if tanque.nivel_actual > 0 and self.carga_actual < self.capacidad_total:
                vacio_camion = self.capacidad_total - self.carga_actual
                bombeo_real = min(tasa_succion, tanque.nivel_actual, vacio_camion)
                
                tanque.nivel_actual -= bombeo_real
                self.carga_actual += bombeo_real
            
            if self.carga_actual >= self.capacidad_total:
                self.estado = "SALIENDO"

        elif self.estado == "SALIENDO":
            # Camión lleno avanza a la izquierda rumbo al punto de cruce
            self.x -= self.velocidad
            
            # CORRECCIÓN: Sincronizado con el nuevo inicio de la carretera (X = 230)
            if self.x <= 230:
                self.x = 210 # Ajuste para que baje centrado en el canal vertical
                self.estado = "DESVIANDO"

        elif self.estado == "DESVIANDO":
            # El camión gira y avanza verticalmente hacia abajo para salir de la pantalla
            self.y += self.velocidad

    def dibujar(self, pantalla, fuente):
        # Ocultar si está en la cola invisible por la derecha (X > 940)
        if self.x > 940 and self.estado == "AVANZANDO":
            return  

        # Si el sprite cenital cargó exitosamente
        if self.sprite_base:
            if self.estado == "DESVIANDO":
                # Renderiza la orientación del camión apuntando hacia abajo
                pantalla.blit(self.sprite_vertical, (self.x, self.y))
            else:
                # Renderiza el camión horizontal usando sus coordenadas centradas en el carril
                # Restamos un pequeño offset en Y para que se alinee con la carretera del main
                pantalla.blit(self.sprite_horizontal, (self.x, self.y - 15))
        else:
            # Bloque geométrico de respaldo original por si no lee el PNG
            if self.estado == "CARGANDO":
                col_cabina = (255, 200, 50)  
                col_cisterna = (0, 180, 220)
            elif self.estado in ["SALIENDO", "DESVIANDO"]:
                col_cabina = (50, 180, 90)   
                col_cisterna = (0, 100, 200)
            else:
                col_cabina = (140, 140, 150) 
                col_cisterna = (90, 95, 100)

            if self.estado == "DESVIANDO":
                pygame.draw.rect(pantalla, col_cisterna, (self.x, self.y, self.alto, self.ancho - 12), border_radius=3)
                pygame.draw.rect(pantalla, col_cabina, (self.x, self.y + self.ancho - 12, self.alto, 12), border_radius=2)
            else:
                pygame.draw.rect(pantalla, col_cisterna, (self.x, self.y, 38, self.alto), border_radius=3)
                pygame.draw.rect(pantalla, col_cabina, (self.x - 12, self.y + 4, 12, 17), border_radius=2)
        
        # Barra de progreso de la logística (solo visible mientras no esté completo)
        if self.estado in ["AVANZANDO", "CARGANDO"]:
            pct = self.carga_actual / self.capacidad_total
            pygame.draw.rect(pantalla, (40, 45, 50), (self.x + 20, self.y - 22, 38, 4), border_radius=1)
            pygame.draw.rect(pantalla, (50, 220, 100), (self.x + 20, self.y - 22, int(38 * pct), 4), border_radius=1)


class FiltradoArena:
    def __init__(self, x, y, ancho, alto):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.saturacion = 0.0  # Porcentaje de obstrucción de los filtros

        # MEJORA: Carga del sprite de filtros multimedios
        try:
            self.sprite_filtro = pygame.image.load("assets/filtros.png").convert_alpha()
            self.sprite_filtro = pygame.transform.scale(self.sprite_filtro, (ancho, alto))
        except:
            self.sprite_filtro = None

    def actualizar(self, agua_entrada, estado_sistema):
        if estado_sistema == "FALLA_ELECTRICA":
            return 0.0
        
        if estado_sistema == "MANTENIMIENTO_FILTROS":
            # Si el usuario activa el mantenimiento, el filtro se limpia progresivamente
            self.saturacion = max(0.0, self.saturacion - 0.5)
            return 0.0  # Mientras se lava, no pasa agua hacia la ósmosis
        
        # En operación normal, el filtro retiene sedimentos y se satura poco a poco
        if agua_entrada > 0:
            self.saturacion = min(100.0, self.saturacion + 0.02)
            
        # A mayor saturación, menor es el caudal que deja pasar (pérdida de eficiencia)
        eficiencia = (100.0 - self.saturacion) / 100.0
        return agua_entrada * eficiencia

    def dibujar(self, pantalla, estado_sistema, fuente):
        if self.sprite_filtro:
            pantalla.blit(self.sprite_filtro, (self.rect.x, self.rect.y))
            # Superposición translúcida según las variaciones operativas y de mantenimiento
            superficie_estado = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            if estado_sistema == "MANTENIMIENTO_FILTROS":
                superficie_estado.fill((200, 160, 40, 80)) # Amarillo preventivo
                pantalla.blit(superficie_estado, (self.rect.x, self.rect.y))
            elif estado_sistema == "FALLA_ELECTRICA":
                superficie_estado.fill((80, 80, 85, 120)) # Capa de inactividad
                pantalla.blit(superficie_estado, (self.rect.x, self.rect.y))
            elif self.saturacion > 60.0:
                # Se opaca progresivamente de marrón por saturación de partículas
                superficie_estado.fill((139, 69, 19, int(self.saturacion * 0.9)))
                pantalla.blit(superficie_estado, (self.rect.x, self.rect.y))
        else:
            # Color según estado (respaldo geométrico)
            if estado_sistema == "MANTENIMIENTO_FILTROS":
                col_bloque = (200, 160, 40)  
            elif estado_sistema == "FALLA_ELECTRICA":
                col_bloque = (120, 120, 125)  
            else:
                r = int(50 + (self.saturacion * 0.5))
                g = int(54 + (self.saturacion * 0.2))
                b = 60
                col_bloque = (r, g, b)

            pygame.draw.rect(pantalla, col_bloque, self.rect, border_radius=6)
            pygame.draw.rect(pantalla, (200, 200, 200), self.rect, width=2, border_radius=6)

        # Textos informativos
        txt_nom = fuente.render("FILTRADO (ARENA)", True, (255, 255, 255))
        txt_sat = fuente.render(f"Sat: {int(self.saturacion)}%", True, (220, 220, 220))
        
        pantalla.blit(txt_nom, (self.rect.x, self.rect.y - 20))
        # CORRECCIÓN: Ahora se dibuja abajo, tomando como referencia el fondo del rectángulo (bottom) + un margen de 5px
        pantalla.blit(txt_sat, (self.rect.x + 10, self.rect.bottom + 5))


class OsmosisInversa:
    def __init__(self, x, y, ancho, alto):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.presion_psi = 0.0

        # MEJORA ANTI-APLASTAMIENTO: Carga y escalado proporcional
        try:
            imagen_base = pygame.image.load("assets/osmosis.png").convert_alpha()
            
            # Calculamos la proporción para que no se deforme
            ancho_orig, alto_orig = imagen_base.get_size()
            proporcion = min(ancho / ancho_orig, alto / alto_orig)
            nuevo_ancho = int(ancho_orig * proporcion)
            nuevo_alto = int(alto_orig * proporcion)
            
            # Escalamos proporcionalmente
            self.sprite_osmosis = pygame.transform.scale(imagen_base, (nuevo_ancho, nuevo_alto))
            
            # Centramos el sprite dentro del espacio asignado del rect
            self.sprite_x = x + (ancho - nuevo_ancho) // 2
            self.sprite_y = y + (alto - nuevo_alto) // 2
            
            # COORDENADAS DE CONEXIÓN REALES (Pegadas al sprite)
            self.entrada_x = self.sprite_x
            self.salida_x = self.sprite_x + nuevo_ancho
        except:
            self.sprite_osmosis = None
            # Si no hay imagen, las conexiones vuelven a los bordes del rect tradicional
            self.entrada_x = x
            self.salida_x = x + ancho

    def actualizar(self, agua_entrada, estado_sistema):
        if estado_sistema in ["FALLA_ELECTRICA", "FALLA_CAPTACION"]:
            self.presion_psi = max(0.0, self.presion_psi - 15.0)
            return 0.0
            
        if agua_entrada > 0:
            self.presion_psi = min(800.0, self.presion_psi + 10.0)
        else:
            self.presion_psi = max(0.0, self.presion_psi - 5.0)

        if self.presion_psi >= 600.0:
            return agua_entrada * 0.45
        return 0.0

    def dibujar(self, pantalla, estado_sistema, fuente):
        # Si el sprite existe, se dibuja la imagen limpia directamente sin rectángulos de fondo
        if self.sprite_osmosis:
            pantalla.blit(self.sprite_osmosis, (self.sprite_x, self.sprite_y))
        else:
            # Color dinámico de estado solo como respaldo si no se encuentra la imagen
            if estado_sistema == "FALLA_ELECTRICA":
                col_bloque = (150, 50, 50)
            elif self.presion_psi >= 600.0:
                col_bloque = (0, 180, 160)
            else:
                col_bloque = (70, 80, 95)
                
            pygame.draw.rect(pantalla, col_bloque, self.rect, border_radius=6)
            pygame.draw.rect(pantalla, (200, 200, 200), self.rect, width=2, border_radius=6)

        # TEXTOS: Mantienen su posición limpia
        txt_nom = fuente.render("ÓSMOSIS INVERSA", True, (255, 255, 255))
        txt_psi = fuente.render(f"{int(self.presion_psi)} PSI", True, (220, 220, 220))
        
        pantalla.blit(txt_nom, (self.rect.x, self.rect.y - 20))
        pantalla.blit(txt_psi, (self.rect.x + 12, self.rect.bottom + 5))


import pygame
import sys
import random
import math

class AlertaOperador:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ancho = 360  # Lo ensanchamos un poquito para dar espacio a los 88px de la foto
        self.alto = 110   # Le damos un poco más de altura para que quepa perfecta
        
        # Cargar tu imagen respetando sus dimensiones de 88x90
        try:
            self.avatar = pygame.image.load("ingeniero.png")
            self.avatar = pygame.transform.scale(self.avatar, (88, 90))
        except:
            self.avatar = None
            
        self.fuente = pygame.font.SysFont("Arial", 12, bold=True)
        
        # Banco de frases categorizadas por tipo de falla
        self.frases_tanque_seco = [
            "¡Foso en cero! Detengan el llenadero de inmediato.",
            "Sin presión en el buffer. ¡Parada de emergencia!",
            "El tanque está seco. Reporten la anomalía al centro de control."
        ]
        self.frases_filtros = [
            "¡Filtros colmados! Se requiere lavado de lechos de arena urgente.",
            "Saturación máxima en filtrado. Iniciando mantenimiento preventivo.",
            "Alerta de obstrucción en filtros. Caudal de entrada restringido."
        ]
        self.frases_captacion = [
            "Línea de captación obstruida. Revisar succión en las bombas de mar.",
            "Caída drástica de caudal marino. ¡Posible bloqueo en la entrada!",
            "Falla en bombas de captación. Verificando presiones físicas."
        ]
        self.frases_apagon = [
            "¡Apagón general en Punto Fijo! Copiando soporte de emergencia.",
            "Planta sin energía eléctrica. Sistemas de ósmosis detenidos.",
            "Corte de suministro eléctrico crítico. Monitoreando estatus del buffer."
        ]
        self.frases_valvula = [
            "¡Corte de distribución! Alguien cerró la llave general.",
            "Presión bloqueada en la salida. Abran la válvula de inmediato.",
            "Alerta en la línea troncal. Suministro hacia los camiones interrumpido."
        ]
        
        self.frase_actual = ""
        self.activo = False
        self.causa_actual = None # Para rastrear qué originó la alerta activa

    def actualizar(self, nivel_tanque, estado_sistema, filtros_saturados=False):
        import random
        
        # 1. PRIORIDAD CRÍTICA: Apagón Total
        if estado_sistema == "FALLA_ELECTRICA":
            if not self.activo or self.causa_actual != "APAGON":
                self.frase_actual = random.choice(self.frases_apagon)
                self.activo = True
                self.causa_actual = "APAGON"
                
        # 2. PRIORIDAD CRÍTICA COMPARTIDA: Válvula de Distribución Cerrada
        elif estado_sistema == "VALVULA_CERRADA":
            if not self.activo or self.causa_actual != "VALVULA":
                self.frase_actual = random.choice(self.frases_valvula)
                self.activo = True
                self.causa_actual = "VALVULA"

        # 3. PRIORIDAD ALTA: El tanque se vació por completo
        elif nivel_tanque <= 0:
            if not self.activo or self.causa_actual != "TANQUE_SECO":
                self.frase_actual = random.choice(self.frases_tanque_seco)
                self.activo = True
                self.causa_actual = "TANQUE_SECO"
                
        # 4. PRIORIDAD MEDIA: Falla o trigger manual de captación
        elif estado_sistema == "FALLA_CAPTACION":
            if not self.activo or self.causa_actual != "CAPTACION":
                self.frase_actual = random.choice(self.frases_captacion)
                self.activo = True
                self.causa_actual = "CAPTACION"
                
        # 5. PRIORIDAD BAJA: Filtros al máximo de saturación o en mantenimiento
        elif estado_sistema == "MANTENIMIENTO_FILTROS" or filtros_saturados:
            if not self.activo or self.causa_actual != "FILTROS":
                self.frase_actual = random.choice(self.frases_filtros)
                self.activo = True
                self.causa_actual = "FILTROS"
                
        # Si no hay ninguna condición de riesgo activa, apagamos la alerta
        else:
            self.activo = False
            self.causa_actual = None

    def dibujar(self, superficie):
        if not self.activo:
            return

        # Fondo del recuadro industrial
        pygame.draw.rect(superficie, (25, 25, 30), (self.x, self.y, self.ancho, self.alto), border_radius=8)
        pygame.draw.rect(superficie, (220, 50, 50), (self.x, self.y, self.ancho, self.alto), width=2, border_radius=8)
        
        # Pestaña superior roja
        pygame.draw.rect(superficie, (220, 50, 50), (self.x + 12, self.y - 12, 140, 15), border_radius=3)
        lbl_tag = self.fuente.render("INGENIERO DE GUARDIA", True, (255, 255, 255))
        superficie.blit(lbl_tag, (self.x + 18, self.y - 12))

        # Dibujar tu imagen de 88x90 con un margen de 10px
        if self.avatar:
            superficie.blit(self.avatar, (self.x + 10, self.y + 10))
        else:
            pygame.draw.rect(superficie, (50, 55, 60), (self.x + 10, self.y + 10, 88, 90), border_radius=4)

        # Ajuste del procesador de texto para que empiece después de los 88px de la foto
        palabras = self.frase_actual.split(' ')
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            if len(linea_actual + " " + palabra) < 28: # Bajamos el límite de caracteres por línea
                linea_actual += " " + palabra
            else:
                lineas.append(linea_actual.strip())
                linea_actual = palabra
        lineas.append(linea_actual.strip())

        # Imprimir el texto al lado derecho de la foto (X + 110 para que no se encima)
        desplazamiento_y = 25
        for linea in lineas:
            txt_surface = self.fuente.render(linea, True, (240, 240, 245))
            superficie.blit(txt_surface, (self.x + 110, self.y + desplazamiento_y))
            desplazamiento_y += 16


class OperadorPlanta:
    def __init__(self, x_inicio, y_piso, x_limite_izq, x_limite_der):
        self.x = x_inicio
        self.y_base = y_piso
        self.y = y_piso
        self.x_min = x_limite_izq  # <-- Definido como x_min
        self.x_max = x_limite_der  # <-- Definido como x_max
        
        self.velocidad = random.choice([0.5, 0.8, 1.0]) 
        self.direccion = random.choice([-1, 1]) 
        
        self.ancho = 8
        self.alto = 20
        self.angulo_caminata = random.uniform(0, 100) 
        
    def actualizar(self, estado_sistema):
        if estado_sistema == "FALLA_ELECTRICA":
            return
            
        self.x += self.velocidad * self.direccion
        
        # CORRECCIÓN: Cambiar self.min_x por self.x_min y self.max_x por self.x_max
        if self.x <= self.x_min:
            self.x = self.x_min
            self.direccion = 1
        elif self.x >= self.x_max:
            self.x = self.x_max
            self.direccion = -1
            
        self.angulo_caminata += 0.15
        import math
        self.y = self.y_base + int(math.sin(self.angulo_caminata) * 2)

    def dibujar(self, superficie):
        # Cuerpo / Overol industrial
        pygame.draw.rect(superficie, (40, 70, 120), (int(self.x), int(self.y), self.ancho, self.alto), border_radius=2)
        
        # Casco de seguridad
        pygame.draw.circle(superficie, (240, 200, 40), (int(self.x) + self.ancho // 2, int(self.y) - 3), 4)
        pygame.draw.rect(superficie, (220, 180, 30), (int(self.x) + (self.ancho // 2) - 1, int(self.y) - 4, 4, 2))
        
        # Botas de seguridad
        pygame.draw.rect(superficie, (20, 20, 20), (int(self.x), int(self.y) + self.alto, 3, 3))
        pygame.draw.rect(superficie, (20, 20, 20), (int(self.x) + self.ancho - 3, int(self.y) + self.alto, 3, 3))



