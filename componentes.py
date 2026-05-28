import pygame
import math

class CaptacionMar:
    def __init__(self, x, y, ancho, alto):
        # CORRECCIÓN: Quitamos el '+ 40'. Ahora el mar inicia exactamente en 'y' 
        # rellenando todo el espacio superior izquierdo del tablero gris.
        self.rect_mar = pygame.Rect(x, y, ancho, alto)
        
        # La bomba se mantiene fija y perfectamente conectada a la primera tubería (Y = 170)
        self.rect_bomba = pygame.Rect(x + ancho - 50, y + 90, 40, 40)
        self.caudal_salida = 5.0

    def actualizar(self, estado_sistema):
        if estado_sistema in ["FALLA_ELECTRICA", "FALLA_CAPTACION"]:
            return 0.0
        return self.caudal_salida

    def dibujar(self, pantalla, estado_sistema, fuente):
        # Dibujamos el océano completo usando el radio superior izquierdo redondeado
        pygame.draw.rect(pantalla, (0, 119, 182), self.rect_mar, border_top_left_radius=10, border_bottom_left_radius=10)
        
        # Color dinámico según fallas mecánicas, eléctricas o de filtros [cite: 31, 38]
        col_bomba = (50, 220, 100) if estado_sistema == "OPERATIVO" else (255, 50, 50)
        if estado_sistema == "MANTENIMIENTO_FILTROS":
            col_bomba = (200, 160, 40)
        pygame.draw.rect(pantalla, col_bomba, self.rect_bomba, border_radius=5)
        
        # Ajustamos el texto para que se renderice limpiamente dentro del agua azul
        txt = fuente.render("CAPTACIÓN", True, (255, 255, 255))
        pantalla.blit(txt, (self.rect_mar.x + 15, self.rect_mar.y + 15))


class TuberiaAnimada:
    def __init__(self, x_inicio, y_inicio, x_fin, y_fin):
        self.x_inicio = x_inicio
        self.y_inicio = y_inicio
        self.x_fin = x_fin
        self.y_fin = y_fin
        self.particulas = [0.0, 0.25, 0.5, 0.75, 1.0] # Posiciones relativas (0 a 1)
        self.velocidad = 0.02

    def actualizar(self, estado_sistema):
        # Las tuberías solo se mueven si la planta está operando de forma continua
        if estado_sistema == "OPERATIVO":
            for i in range(len(self.particulas)):
                self.particulas[i] += self.velocidad
                if self.particulas[i] > 1.0:
                    self.particulas[i] = 0.0

    def dibujar(self, pantalla):
        # Dibujar la tubería base (Gris metálico)
        pygame.draw.line(pantalla, (100, 100, 105), (self.x_inicio, self.y_inicio), (self.x_fin, self.y_fin), 6)
        
        # Dibujar gotas de agua en movimiento interno (Círculos celestes)
        for p in self.particulas:
            x_actual = self.x_inicio + (self.x_fin - self.x_inicio) * p
            y_actual = self.y_inicio + (self.y_fin - self.y_inicio) * p
            pygame.draw.circle(pantalla, (72, 202, 228), (int(x_actual), int(y_actual)), 4)


# --- REEMPLAZAR LA CLASE TANQUE PULMÓN (Para quitar el consumo artificial) ---
class TanquePulmon:
    def __init__(self, x, y, ancho, alto, capacidad_maxima):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.capacidad_maxima = capacity_maxima = capacidad_maxima
        self.nivel_actual = 800.0  # Empezamos con una base saludable de agua

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

        pygame.draw.rect(pantalla, (60, 64, 70), self.rect, border_radius=10)
        pygame.draw.rect(pantalla, (200, 200, 200), self.rect, width=2, border_radius=10)
        
        if alto_agua > 0:
            rect_agua = pygame.Rect(self.rect.x + 2, self.rect.bottom - alto_agua - 2, self.rect.width - 4, alto_agua)
            pygame.draw.rect(pantalla, col_agua, rect_agua, border_radius=8)

        txt_nom = fuente.render("TANQUE PULMÓN", True, (255, 255, 255))
        txt_volumen = fuente.render(f"{int(self.nivel_actual)} L / {int(self.capacidad_maxima)} L", True, (220, 220, 220))
        txt_porcentaje = fuente.render(f"{int(porcentaje * 100)}%", True, (255, 255, 255))
        
        pantalla.blit(txt_nom, (self.rect.x - 10, self.rect.y - 22))
        pantalla.blit(txt_volumen, (self.rect.x - 10, self.rect.bottom + 8))
        pantalla.blit(txt_porcentaje, (self.rect.centerx - 12, self.rect.centery - 8))


# --- AGREGAR ESTA CLASE NUEVA AL FINAL DE COMPONENTES.PY ---
# --- CLASE CAMIÓN ACTUALIZADA CON CONTADOR DE REPORTES ---
class Camion:
    def __init__(self, x_inicio, y_llenadero):
        self.x = x_inicio
        self.y = y_llenadero
        self.ancho = 50
        self.alto = 25
        self.velocidad = 2
        self.capacidad_total = 400.0  
        self.carga_actual = 0.0
        # Estados: "AVANZANDO", "CARGANDO", "SALIENDO", "DESVIANDO"
        self.estado = "AVANZANDO"  

    def actualizar(self, x_destino, es_primero, tanque):
        if self.estado == "AVANZANDO":
            if self.x > x_destino:
                self.x -= self.velocidad
            elif es_primero:
                self.estado = "CARGANDO"

        elif self.estado == "CARGANDO":
            # --- VÁLVULA DE CONTROL INDUSTRIAL PROPORCIONAL ---
            # Calculamos el porcentaje actual del tanque (de 0.0 a 1.0)
            porcentaje_tanque = tanque.nivel_actual / tanque.capacidad_maxima
            
            # La succión máxima permitida será de 1.2, pero se reduce si el tanque está vacío.
            # Si el tanque está al 10%, la tasa será 1.2 * 0.10 = 0.12 (Carga muy lento).
            # Si el tanque está al 100%, la tasa será 1.2 * 1.0 = 1.2 (Carga a máxima velocidad).
            tasa_succion = 1.2 * porcentaje_tanque
            
            # Garantizamos un mínimo de succión para que no se quede completamente trabado cerca de 0
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
                self.x = 235 # Ajuste milimétrico para centrar el chasis en el carril
                self.estado = "DESVIANDO"

        elif self.estado == "DESVIANDO":
            # El camión gira y avanza verticalmente hacia abajo para salir de la pantalla
            self.y += self.velocidad

    def dibujar(self, pantalla, fuente):
        # Ocultar si está en la cola invisible por la derecha (X > 940)
        # Pero permitir que se dibuje si va bajando (aunque X sea menor, Y cambia)
        if self.x > 940 and self.estado == "AVANZANDO":
            return  

        if self.estado == "CARGANDO":
            col_cabina = (255, 200, 50)  
            col_cisterna = (0, 180, 220)
        elif self.estado in ["SALIENDO", "DESVIANDO"]:
            col_cabina = (50, 180, 90)   
            col_cisterna = (0, 100, 200)
        else:
            col_cabina = (140, 140, 150) 
            col_cisterna = (90, 95, 100)

        # Renderizar la geometría según la dirección del movimiento
        if self.estado == "DESVIANDO":
            # Como va hacia abajo, la cabina se dibuja en la parte INFERIOR del camión
            pygame.draw.rect(pantalla, col_cisterna, (self.x, self.y, self.alto, self.ancho - 12), border_radius=3)
            pygame.draw.rect(pantalla, col_cabina, (self.x, self.y + self.ancho - 12, self.alto, 12), border_radius=2)
        else:
            # Renderizado estándar horizontal (marcha a la izquierda)
            pygame.draw.rect(pantalla, col_cisterna, (self.x, self.y, 38, self.alto), border_radius=3)
            pygame.draw.rect(pantalla, col_cabina, (self.x - 12, self.y + 4, 12, 17), border_radius=2)
        
        # Barra de carga (solo visible mientras no esté completo)
        if self.estado in ["AVANZANDO", "CARGANDO"]:
            pct = self.carga_actual / self.capacidad_total
            pygame.draw.rect(pantalla, (80, 80, 80), (self.x, self.y - 7, 38, 4))
            pygame.draw.rect(pantalla, (50, 220, 100), (self.x, self.y - 7, int(38 * pct), 4))

class FiltradoArena:
    def __init__(self, x, y, ancho, alto):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.saturacion = 0.0  # Porcentaje de obstrucción de los filtros

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
        # Color según estado
        if estado_sistema == "MANTENIMIENTO_FILTROS":
            col_bloque = (200, 160, 40)  # Amarillo/Naranja de mantenimiento
        elif estado_sistema == "FALLA_ELECTRICA":
            col_bloque = (120, 120, 125)  # Gris muerto sin energía
        else:
            # Va pasando de gris oscuro a un tono marrón texturizado según la saturación
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
        pantalla.blit(txt_sat, (self.rect.x + 10, self.rect.centery - 6))


class OsmosisInversa:
    def __init__(self, x, y, ancho, alto):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.presion_psi = 0.0

    def actualizar(self, agua_entrada, estado_sistema):
        # La ósmosis requiere alta presión mecánica (mucha electricidad)
        if estado_sistema in ["FALLA_ELECTRICA", "FALLA_CAPTACION"]:
            self.presion_psi = max(0.0, self.presion_psi - 15.0)  # Cae la presión
            return 0.0
            
        if agua_entrada > 0:
            self.presion_psi = min(800.0, self.presion_psi + 10.0)  # Sube a presión nominal (800 PSI)
        else:
            self.presion_psi = max(0.0, self.presion_psi - 5.0)

        # Solo produce agua purificada si las membranas superan el umbral de presión (ej: 600 PSI)
        if self.presion_psi >= 600.0:
            return agua_entrada * 0.45  # El 45% se convierte en agua dulce (conversión real de desalinizadoras)
        return 0.0

    def dibujar(self, pantalla, estado_sistema, fuente):
        # Color dinámico por presión u operación
        if estado_sistema == "FALLA_ELECTRICA":
            col_bloque = (150, 50, 50)
        elif self.presion_psi >= 600.0:
            col_bloque = (0, 180, 160)  # Turquesa operativo de alta presión
        else:
            col_bloque = (70, 80, 95)

        pygame.draw.rect(pantalla, col_bloque, self.rect, border_radius=6)
        pygame.draw.rect(pantalla, (200, 200, 200), self.rect, width=2, border_radius=6)

        # Textos informativos
        txt_nom = fuente.render("ÓSMOSIS INVERSA", True, (255, 255, 255))
        txt_psi = fuente.render(f"{int(self.presion_psi)} PSI", True, (255, 255, 255))
        
        pantalla.blit(txt_nom, (self.rect.x, self.rect.y - 20))
        pantalla.blit(txt_psi, (self.rect.x + 12, self.rect.centery - 6))




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
        self.frases = [
            "¡Foso en cero! Detengan el llenadero de inmediato.",
            "Sin presión en el buffer. ¡Parada de emergencia!",
            "El tanque está seco. Reporten la anomalía al centro de control."
        ]
        self.frase_actual = self.frases[0]
        self.activo = False

    def actualizar(self, nivel_tanque):
        if nivel_tanque <= 0:
            if not self.activo:
                import random
                self.frase_actual = random.choice(self.frases)
                self.activo = True
        else:
            self.activo = False

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