import pygame
import sys
import random
import math  # Importamos math en el principal para la animación del rotor de la bomba
from interfaz import Boton
from componentes import CaptacionMar, TuberiaAnimada, TanquePulmon, FiltradoArena, OsmosisInversa, Camion, OperadorPlanta

pygame.init()
ANCHO, ALTO = 1000, 550  
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("AquaLogic: Simulador Desalinizadora Punto Fijo")
reloj = pygame.time.Clock()

fuente_titulo = pygame.font.SysFont("Arial", 20, bold=True)
fuente_interfaz = pygame.font.SysFont("Arial", 12, bold=True)
fuente_estado = pygame.font.SysFont("Arial", 15, bold=True)

estado_sistema = "OPERATIVO" 

# Componentes en la franja superior
mar_captacion = CaptacionMar(x=20, y=60, ancho=130, alto=340)
bloque_filtrado = FiltradoArena(x=230, y=140, ancho=110, alto=60)
bloque_osmosis = OsmosisInversa(x=430, y=140, ancho=110, alto=60)

tubo_1 = TuberiaAnimada(x_inicio=140, y_inicio=170, x_fin=250, y_fin=170)
tubo_2 = TuberiaAnimada(x_inicio=320, y_inicio=170, x_fin=bloque_osmosis.entrada_x, y_fin=170)
tubo_3 = TuberiaAnimada(x_inicio=bloque_osmosis.salida_x, y_inicio=170, x_fin=660, y_fin=170)

tanque_reserva = TanquePulmon(x=660, y=100, ancho=110, alto=180, capacidad_maxima=2000.0)

from componentes import AlertaOperador 
alerta_ingeniero = AlertaOperador(x=230, y=300)

# Logística vial zonificada
lista_camiones = []
X_LLENADERO = 715
Y_LLENADERO = 340  
TASA_LLEGADA_CAMION = 0.007 

y_panel = 465  
ancho_btn = 210
alto_btn = 40
espaciado = 25

botones = {
    "apagon": Boton(40, y_panel, ancho_btn, alto_btn, "TRIGGER APAGÓN TOTAL", (180, 40, 40), (220, 50, 50)),
    "captacion": Boton(40 + (ancho_btn + espaciado), y_panel, ancho_btn, alto_btn, "SIMULAR FALLA CAPTACIÓN", (200, 100, 40), (240, 120, 50)),
    "filtros": Boton(40 + (ancho_btn + espaciado) * 2, y_panel, ancho_btn, alto_btn, "MANTENIMIENTO FILTROS", (200, 160, 40), (240, 190, 50)),
    "estable": Boton(40 + (ancho_btn + espaciado) * 3, y_panel, ancho_btn, alto_btn, "RESETEAR SISTEMA (ESTABLE)", (40, 140, 70), (50, 180, 90))
}

historial_tiempo = []
historial_tanque = []
historial_camiones_fila = []
historial_deficit_acumulado = []

contador_camiones_atendidos = 0
agua_total_desalinizada = 0.0
tiempo_simulado = 0  

tiempo_falla_electrica = 0
tiempo_falla_filtros = 0
tiempo_falla_captacion = 0
tiempo_valvula_cerrada = 0  
deficit_hidrico_litros = 0.0

tanque_en_recuperacion = False

# Variable global para controlar el ángulo de giro del rotor de la bomba estilo juego
angulo_bomba_rotor = 0.0

# Coordenadas específicas de vegetación solicitadas
zonas_verdes = [
    # Dos árboles arriba de la carretera horizontal (Y_LLENADERO = 340)
    {"x": 450, "y": 315, "tipo": "arbol", "radio": 13},
    {"x": 600, "y": 315, "tipo": "arbol", "radio": 14},

    # Abajo de la salmuera / descarga costera
    {"x": 45,  "y": 380, "tipo": "arbol", "radio": 14},
    {"x": 80,  "y": 385, "tipo": "arbusto", "radio": 8},
    {"x": 115, "y": 382, "tipo": "arbol", "radio": 12},
    # Parte de arriba de la planta (Fondo norte)
    {"x": 260, "y": 80,  "tipo": "arbol", "radio": 13},
    {"x": 350, "y": 82,  "tipo": "arbol", "radio": 14},
    {"x": 470, "y": 78,  "tipo": "arbol", "radio": 12},
    {"x": 570, "y": 78,  "tipo": "arbol", "radio": 13},
    # Al lado de la subestación (Derecha)
    {"x": 805, "y": 95,  "tipo": "arbol", "radio": 14},
    {"x": 925, "y": 90,  "tipo": "arbol", "radio": 13},
    {"x": 950, "y": 105, "tipo": "arbusto", "radio": 7}
]

# =========================================================================
# --- CALIBRACIÓN DE LÍMITES PARA OPERADORES (ZONAS RESPETANDO ESTRUCTURAS) ---
# =========================================================================
Y_PISO_OPERADORES = 215  # Definimos la constante de altura para usarla de forma limpia
lista_operadores = [
    OperadorPlanta(x_inicio=360, y_piso=Y_PISO_OPERADORES, x_limite_izq=300, x_limite_der=440),  # Límite ajustado para no invadir la salmuera
    OperadorPlanta(x_inicio=560, y_piso=Y_PISO_OPERADORES, x_limite_izq=545, x_limite_der=650)   
]

# =========================================================================
# --- CONFIGURACIÓN DEL OPERADOR LIBRE EXTERIOR (WASD) ---
# =========================================================================
op_libre_x = 300
op_libre_y = 300  # Ajustado ligeramente hacia arriba para iniciar fuera de la zona bloqueada
op_libre_vel = 3
op_libre_dir = 1  

# Se agregaron los límites del entorno y la tubería de salmuera para el supervisor
obstaculos = [
    pygame.Rect(0, 0, 1000, 60),               
    pygame.Rect(0, 400, 1000, 150),            
    pygame.Rect(20, 60, 130, 340),             
    pygame.Rect(230, 140, 110, 60),            
    pygame.Rect(430, 140, 110, 60),            
    pygame.Rect(660, 100, 110, 180),           
    pygame.Rect(140, 165, 520, 20),            
    pygame.Rect(840, 78, 65, 47),              
    pygame.Rect(X_LLENADERO - 10, 280, 50, 95),
    pygame.Rect(230, Y_LLENADERO - 5, 750, 250), # <<-- BLOQUEO ABSOLUTO DE CARRETERA PARA EL SUPERVISOR
    
    # === NUEVO OBSTÁCULO: TUBERÍA DE SALMUERA DE DESCARGA COSTERA ===
    # Bloquea el paso horizontal desde x=60 hasta x=492 en la altura y=235
    pygame.Rect(60, 235, 432, 14)
]

X_VALVULA = 540
Y_VALVULA = 235

ejecutando = True
while ejecutando:
    teclas = pygame.key.get_pressed()

    # --- CONTROL DEL OPERADOR LIBRE CON WASD + DETECCIÓN DE COLISIONES ---
    dx, dy = 0, 0
    if teclas[pygame.K_a]: 
        dx = -op_libre_vel
        op_libre_dir = -1
    if teclas[pygame.K_d]: 
        dx = op_libre_vel
        op_libre_dir = 1
    if teclas[pygame.K_w]: dy = -op_libre_vel
    if teclas[pygame.K_s]: dy = op_libre_vel

    nuevo_rect_x = pygame.Rect(op_libre_x + dx - 8, op_libre_y - 25, 16, 30)
    colision_x = False
    for obs in obstaculos:
        if nuevo_rect_x.colliderect(obs):
            colision_x = True
            break
            
    if not colision_x:
        for camion in lista_camiones:
            rect_camion = pygame.Rect(camion.x, camion.y - 15, camion.ancho, camion.alto)
            if nuevo_rect_x.colliderect(rect_camion):
                colision_x = True
                break

    if not colision_x and (20 <= op_libre_x + dx <= 980):
        op_libre_x += dx

    nuevo_rect_y = pygame.Rect(op_libre_x - 8, op_libre_y + dy - 25, 16, 30)
    colision_y = False
    for obs in obstaculos:
        if nuevo_rect_y.colliderect(obs):
            colision_y = True
            break
            
    if not colision_y:
        for camion in lista_camiones:
            rect_camion = pygame.Rect(camion.x, camion.y - 15, camion.ancho, camion.alto)
            if nuevo_rect_y.colliderect(rect_camion):
                colision_y = True
                break

    if not colision_y and (60 <= op_libre_y + dy <= 400):
        op_libre_y += dy

    cerca_valvula_p1 = abs(lista_operadores[1].x - X_VALVULA) < 25
    cerca_valvula_libre = math.hypot(op_libre_x - X_VALVULA, op_libre_y - Y_VALVULA) < 30
    cerca_de_valvula = cerca_valvula_p1 or cerca_valvula_libre

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ejecutando = False
            
        if botones["apagon"].clickeado(event): estado_sistema = "FALLA_ELECTRICA"
        elif botones["captacion"].clickeado(event): estado_sistema = "FALLA_CAPTACION"
        elif botones["filtros"].clickeado(event): estado_sistema = "MANTENIMIENTO_FILTROS"
        elif botones["estable"].clickeado(event): estado_sistema = "OPERATIVO"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and cerca_de_valvula:
                if estado_sistema == "VALVULA_CERRADA":
                    estado_sistema = "OPERATIVO"
                else:
                    estado_sistema = "VALVULA_CERRADA"

    caudal_captado = mar_captacion.actualizar(estado_sistema)
    caudal_filtrado = bloque_filtrado.actualizar(caudal_captado, estado_sistema)
    caudal_purificado = bloque_osmosis.actualizar(caudal_filtrado, estado_sistema)
    
    caudal_hacia_tanque = 0 if estado_sistema == "VALVULA_CERRADA" else caudal_purificado
    tanque_reserva.actualizar(caudal_hacia_tanque, estado_sistema)
    
    # === CONTROL DE FLUJO ANIMADO EN TUBERÍAS SEGÚN ESTADO DEL SISTEMA ===
    if estado_sistema == "OPERATIVO":
        tubo_1.actualizar("OPERATIVO" if caudal_captado > 0 else "PARADO")
        tubo_2.actualizar("OPERATIVO" if caudal_filtrado > 0 else "PARADO")
        tubo_3.actualizar("OPERATIVO" if caudal_hacia_tanque > 0 else "PARADO")
        angulo_bomba_rotor += 0.25  # El rotor gira a velocidad nominal
    else:
        # Si el sistema está en cualquier estado de falla, se congela el flujo de inmediato
        tubo_1.actualizar("PARADO")
        tubo_2.actualizar("PARADO")
        tubo_3.actualizar("PARADO")
        
        # Opcional: Ralentizar o detener el rotor según la falla específica para hacer match visual
        if estado_sistema == "MANTENIMIENTO_FILTROS":
            angulo_bomba_rotor += 0.12
        elif estado_sistema == "FALLA_CAPTACION":
            angulo_bomba_rotor += 0.04
        else:
            # FALLA_ELECTRICA o VALVULA_CERRADA detienen el rotor por completo
            angulo_bomba_rotor += 0.0

    if estado_sistema == "OPERATIVO":
        angulo_bomba_rotor += 0.25
    elif estado_sistema == "MANTENIMIENTO_FILTROS":
        angulo_bomba_rotor += 0.12
    elif estado_sistema == "FALLA_CAPTACION":
        angulo_bomba_rotor += 0.04

    # Todos los operadores de pasarela actualizan su comportamiento automático
    for operador in lista_operadores:
        operador.actualizar(estado_sistema)

    if random.random() < TASA_LLEGADA_CAMION:
        # Límite máximo total de camiones permitidos en el sistema de forma simultánea
        CAPACIDAD_MAXIMA_LOGISTICA = 12
        
        # Solo se genera el camión si la cola total actual no supera el límite de contención
        if len(lista_camiones) < CAPACIDAD_MAXIMA_LOGISTICA:
            lista_camiones.append(Camion(x_inicio=1020, y_llenadero=Y_LLENADERO))

    if tanque_reserva.nivel_actual <= 0:
        tanque_en_recuperacion = True  
        
    if tanque_en_recuperacion and tanque_reserva.nivel_actual >= tanque_reserva.capacidad_maxima:
        tanque_en_recuperacion = False 

    camiones_en_espera = 0
    distancia_entre_camiones = 80

    for indice, camion in enumerate(lista_camiones):
        if camion.estado in ["SALIENDO", "DESVIANDO"]:
            camion.actualizar(0, False, tanque_reserva)
        else:
            # Determinamos la meta ideal en la fila
            x_meta_fila = X_LLENADERO + (camiones_en_espera * distancia_entre_camiones)
            es_el_primero_de_la_fila = (camiones_en_espera == 0) and not tanque_en_recuperacion
            estado_previo = camion.estado
            
            # --- DETECCIÓN DE COLISIÓN ENTRE CAMIONES (SISTEMA ANTICOLISIÓN ACTIVO) ---
            bloqueado_por_camion_delante = False
            if camiones_en_espera > 0:
                # El camión de adelante en la fila es el que se procesó justo antes en el índice anterior que no esté saliendo
                for idx_ant in range(indice - 1, -1, -1):
                    camion_delante = lista_camiones[idx_ant]
                    if camion_delante.estado not in ["SALIENDO", "DESVIANDO"]:
                        proximidad_actual = camion.x - camion_delante.x
                        if 0 < proximidad_actual < distancia_entre_camiones:
                            bloqueado_por_camion_delante = True
                        break

            if bloqueado_por_camion_delante:
                # Forzar su destino a su propia coordenada 'x' actual para detenerlo por completo y evitar que se encime
                camion.actualizar(camion.x, False, tanque_reserva)
            else:
                camion.actualizar(x_meta_fila, es_el_primero_de_la_fila, tanque_reserva)
            
            if estado_previo == "CARGANDO" and camion.estado == "SALIENDO":
                contador_camiones_atendidos += 1
                
            camiones_en_espera += 1

    lista_camiones = [c for c in lista_camiones if c.y < 550]

    # =========================================================================
    # --- CAPA 1: FONDO Y ESCENARIO BASE ---
    # =========================================================================
    pantalla.fill((30, 30, 32))  

    pygame.draw.rect(pantalla, (40, 43, 48), (20, 60, ANCHO - 40, 340), border_radius=10)
    pygame.draw.rect(pantalla, (80, 85, 90), (210, 60, ANCHO - 230, 340))
    pygame.draw.rect(pantalla, (235, 210, 165), (150, 60, 60, 340))

    x_tubo_h, y_tubo_h = 60, 235
    ancho_tubo_h, alto_tubo_h = 432, 12
    pygame.draw.rect(pantalla, (25, 27, 30), (x_tubo_h, y_tubo_h + alto_tubo_h, ancho_tubo_h, 3))
    pygame.draw.rect(pantalla, (40, 42, 45), (480 + 12, 200, 3, 45 + alto_tubo_h))  
    pygame.draw.rect(pantalla, (40, 42, 45), (480, 200, 12, 47))          
    pygame.draw.rect(pantalla, (65, 68, 72), (482, 200, 8, 47))          
    pygame.draw.rect(pantalla, (210, 215, 220), (485, 200, 2, 47))        
    pygame.draw.rect(pantalla, (40, 42, 45), (x_tubo_h, y_tubo_h, ancho_tubo_h, alto_tubo_h))      
    pygame.draw.rect(pantalla, (65, 68, 72), (x_tubo_h, y_tubo_h + 2, ancho_tubo_h, 8))       
    pygame.draw.rect(pantalla, (210, 215, 220), (x_tubo_h, y_tubo_h + 4, ancho_tubo_h, 2))    

    puntos_anillos = [90, 160, 220, 300, 380, 450]
    for px in puntos_anillos:
        pygame.draw.rect(pantalla, (30, 32, 35), (px, y_tubo_h - 2, 6, alto_tubo_h + 4), border_radius=1)
        pygame.draw.rect(pantalla, (120, 125, 130), (px + 2, y_tubo_h - 2, 2, alto_tubo_h + 4))

    pygame.draw.rect(pantalla, (40, 42, 45), (478, 233, 16, 16), border_radius=3)
    pygame.draw.rect(pantalla, (65, 68, 72), (480, 235, 12, 12), border_radius=2)
    pygame.draw.circle(pantalla, (100, 180, 240, 180), (60, 241), 12)
    pygame.draw.circle(pantalla, (180, 220, 255), (58, 241), 8)
    pygame.draw.circle(pantalla, (255, 255, 255), (54, 241), 5)

    lbl_pwr = fuente_interfaz.render("SUB-STATION", True, (180, 180, 185))
    pantalla.blit(lbl_pwr, (838, 62))
    pygame.draw.rect(pantalla, (60, 65, 70), (840, 78, 65, 47), border_radius=4)
    pygame.draw.rect(pantalla, (40, 45, 50), (846, 86, 12, 32))
    pygame.draw.rect(pantalla, (40, 45, 50), (863, 86, 12, 32))
    pygame.draw.polygon(pantalla, (240, 200, 40), [(892, 86), (885, 99), (892, 99), (887, 112), (898, 94), (891, 94)])

    # =========================================================================
    # --- CAPA 2: ASFALTO Y LÍNEAS DE CARRETERA ---
    # =========================================================================
    limite_cuadro_negro = pygame.Rect(20, 60, ANCHO - 40, 340)
    pantalla.set_clip(limite_cuadro_negro) 

    pygame.draw.rect(pantalla, (46, 48, 52), (230, Y_LLENADERO - 5, 750, 35))
    pygame.draw.rect(pantalla, (46, 48, 52), (230, Y_LLENADERO + 30, 35, 180))
    
    pygame.draw.line(pantalla, (200, 160, 40), (247, Y_LLENADERO + 12), (980, Y_LLENADERO + 12), width=1)
    pygame.draw.line(pantalla, (200, 160, 40), (247, Y_LLENADERO + 12), (247, 550), width=1)

    for veg in zonas_verdes:
        cx, cy, r = veg["x"], veg["y"], veg["radio"]
        if veg["tipo"] == "arbol":
            pygame.draw.ellipse(pantalla, (55, 60, 62), (cx - r, cy + 2, r * 2, 8))
            pygame.draw.rect(pantalla, (110, 70, 45), (cx - 3, cy, 6, 16))
            pygame.draw.circle(pantalla, (34, 112, 63), (cx, cy - 4), r)
            pygame.draw.circle(pantalla, (46, 139, 87), (cx - 2, cy - 6), int(r * 0.85))
            pygame.draw.circle(pantalla, (20, 45, 30), (cx, cy - 4), r, width=1)

    pantalla.set_clip(None) 

    # --- MANGUERA DE SALIDA ACOPLADA VERTICALMENTE AL TANQUE PULMÓN (Y: 233) ---
    pygame.draw.line(pantalla, (130, 135, 140), (X_LLENADERO + 15, 233), (X_LLENADERO + 15, Y_LLENADERO), width=4)
    pygame.draw.circle(pantalla, (255, 215, 0), (X_LLENADERO + 15, Y_LLENADERO), 5)

    # =========================================================================
    # --- CAPA 3: MÓDULOS DE LA PLANTA Y ELEMENTOS MÓVILES ---
    # =========================================================================
    tubo_1.dibujar(pantalla)
    tubo_2.dibujar(pantalla)
    tubo_3.dibujar(pantalla)
    
    mar_captacion.dibujar(pantalla, estado_sistema, fuente_interfaz)
    
    bomba_x, bomba_y = 105, 153
    bomba_w, bomba_h = 32, 34
    
    col_bomba_base = (70, 75, 82) if estado_sistema != "FALLA_ELECTRICA" else (48, 50, 54)
    col_bomba_borde = (30, 32, 35)
    
    pygame.draw.rect(pantalla, col_bomba_base, (bomba_x, bomba_y, bomba_w, bomba_h), border_radius=4)
    pygame.draw.rect(pantalla, col_bomba_borde, (bomba_x, bomba_y, bomba_w, bomba_h), width=2, border_radius=4)
    
    for rx in range(bomba_x + 4, bomba_x + bomba_w - 2, 5):
        pygame.draw.rect(pantalla, (25, 25, 28), (rx, bomba_y + bomba_h - 6, 3, 4))
        
    centro_rx, centro_ry = bomba_x + (bomba_w // 2), bomba_y + 13
    pygame.draw.circle(pantalla, (38, 40, 44), (centro_rx, centro_ry), 8)
    
    for i in range(4):
        f_aspa = angulo_bomba_rotor + (i * (math.pi / 2))
        ax = centro_rx + int(math.cos(f_aspa) * 6)
        ay = centro_ry + int(math.sin(f_aspa) * 6)
        col_aspa = (100, 210, 255) if estado_sistema == "OPERATIVO" else (220, 70, 70) if estado_sistema == "FALLA_CAPTACION" else (90, 95, 100)
        pygame.draw.line(pantalla, col_aspa, (centro_rx, centro_ry), (ax, ay), width=2)
        
    col_bomba_led = (40, 255, 90) if estado_sistema == "OPERATIVO" else (255, 150, 0) if estado_sistema == "MANTENIMIENTO_FILTROS" else (255, 30, 30)
    pygame.draw.circle(pantalla, col_bomba_led, (bomba_x + 6, bomba_y + 6), 3)

    bloque_filtrado.dibujar(pantalla, estado_sistema, fuente_interfaz)
    bloque_osmosis.dibujar(pantalla, estado_sistema, fuente_interfaz)
    tanque_reserva.dibujar(pantalla, fuente_interfaz)

    pygame.draw.circle(pantalla, (110, 115, 120), (148, 110), 9)
    pygame.draw.circle(pantalla, (90, 95, 100), (152, 120), 7)
    pygame.draw.circle(pantalla, (120, 125, 130), (146, 210), 11)
    pygame.draw.circle(pantalla, (100, 102, 105), (150, 222), 8)
    pygame.draw.circle(pantalla, (105, 108, 112), (147, 300), 10)
    pygame.draw.circle(pantalla, (85, 88, 90), (153, 312), 6)

    col_llave = (240, 50, 50) if estado_sistema == "VALVULA_CERRADA" else (50, 150, 240)
    pygame.draw.circle(pantalla, (30, 30, 30), (X_VALVULA, Y_VALVULA), 9)
    pygame.draw.circle(pantalla, col_llave, (X_VALVULA, Y_VALVULA), 7, width=2)

    # Renderizado de operadores de pasarela fijos
    for i, operador in enumerate(lista_operadores):
        operador.dibujar(pantalla)
        if i == 0:  
            txt_p1 = fuente_interfaz.render("OPERADOR 1 (AUTO)", True, (100, 200, 255))
            pantalla.blit(txt_p1, (operador.x - 30, Y_PISO_OPERADORES - 42))

    # =========================================================================
    # --- RENDERIZADO DEL SUPERVISOR LIBRE EXTERIOR (WASD) ---
    # =========================================================================
    pygame.draw.rect(pantalla, (110, 60, 160), (op_libre_x - 7, op_libre_y - 15, 14, 15), border_radius=2)
    pygame.draw.circle(pantalla, (245, 200, 160), (op_libre_x, op_libre_y - 21), 5)
    pygame.draw.arc(pantalla, (255, 255, 255), (op_libre_x - 6, op_libre_y - 27, 12, 10), 0, math.pi, width=4)
    pygame.draw.line(pantalla, (230, 230, 230), (op_libre_x - 7, op_libre_y - 22), (op_libre_x + 7, op_libre_y - 22), width=2)
    pygame.draw.rect(pantalla, (50, 52, 55), (op_libre_x - 6, op_libre_y, 5, 8))
    pygame.draw.rect(pantalla, (50, 52, 55), (op_libre_x + 1, op_libre_y, 5, 8))
    pygame.draw.rect(pantalla, (20, 20, 20), (op_libre_x - (7 if op_libre_dir == -1 else 6), op_libre_y + 8, 5, 3))
    pygame.draw.rect(pantalla, (20, 20, 20), (op_libre_x + (1 if op_libre_dir == -1 else 2), op_libre_y + 8, 5, 3))
    
    txt_libre = fuente_interfaz.render("SUPERVISOR (WASD)", True, (210, 150, 255))
    pantalla.blit(txt_libre, (op_libre_x - 45, op_libre_y - 40))

    if cerca_de_valvula:
        msg_val = "[E] ABRIR LLAVE" if estado_sistema == "VALVULA_CERRADA" else "[E] CERRAR LLAVE"
        lbl_val = fuente_interfaz.render(msg_val, True, (255, 255, 100))
        pygame.draw.rect(pantalla, (20, 20, 20), (X_VALVULA - 45, Y_VALVULA - 25, 95, 18), border_radius=3)
        pantalla.blit(lbl_val, (X_VALVULA - 41, Y_VALVULA - 23))

    pantalla.set_clip(limite_cuadro_negro)
    for camion in reversed(lista_camiones):
        camion.dibujar(pantalla, fuente_interfaz)
    pantalla.set_clip(None) 

    txt_cola = fuente_interfaz.render(f"Camiones en Fila (Demanda): {camiones_en_espera}", True, (200, 220, 240))
    pantalla.blit(txt_cola, (X_LLENADERO - 20, Y_LLENADERO + 45))

    # =========================================================================
    # --- CAPA 4: INTERFAZ DE USUARIO, PANEL DE BOTONES Y ALERTAS ---
    # =========================================================================
    pygame.draw.rect(pantalla, (20, 24, 30), (0, 0, ANCHO, 45))
    texto_titulo = fuente_titulo.render("AquaLogic: DESALINIZADORA PUNTO FIJO SIMULATION", True, (255, 255, 255))
    pantalla.blit(texto_titulo, (20, 10))

    pygame.draw.rect(pantalla, (22, 22, 24), (20, 440, ANCHO - 40, 85), border_radius=10)
    texto_panel = fuente_interfaz.render("PANEL DE CONTROL DE USUARIO (EVENTOS MANUALES)", True, (150, 150, 150))
    pantalla.blit(texto_panel, (35, 446))

    for brillo in botones.values():
        brillo.dibujar(pantalla, fuente_interfaz)

    if estado_sistema == "OPERATIVO":
        col_alarma, msg_alarma = (50, 220, 100), "SISTEMA ESTABLE - PRODUCCIÓN CONTINUA"
    elif estado_sistema == "FALLA_ELECTRICA":
        col_alarma, msg_alarma = (255, 50, 50), "¡FALLO CRÍTICO DE ENERGÍA! PLANTA PARADA"
        tiempo_falla_electrica += 1
    elif estado_sistema == "FALLA_CAPTACION":
        col_alarma, msg_alarma = (255, 120, 50), "ALERTA: BOMBAS DE CAPTACIÓN OBSTRUIDAS"
        tiempo_falla_captacion += 1
    elif estado_sistema == "MANTENIMIENTO_FILTROS":
        col_alarma, msg_alarma = (255, 200, 50), "MANTENIMIENTO: LAVADO DE LECHOS DE ARENA ACTIVO"
        tiempo_falla_filtros += 1
    elif estado_sistema == "VALVULA_CERRADA":
        col_alarma, msg_alarma = (255, 90, 90), "SABOTAJE / ADVERTENCIA: LLAVE GENERAL DE DISTRIBUCIÓN CERRADA"
        tiempo_valvula_cerrada += 1

    superficie_estado = fuente_estado.render(f"ESTADO GLOBAL: {msg_alarma}", True, col_alarma)
    pantalla.blit(superficie_estado, (35, 412))

    alerta_ingeniero.actualizar(
        tanque_reserva.nivel_actual, 
        estado_sistema, 
        filtros_saturados=(bloque_filtrado.saturacion >= 100 if hasattr(bloque_filtrado, 'saturacion') else False)
    )
    alerta_ingeniero.dibujar(pantalla)

    if estado_sistema != "OPERATIVO" and camiones_en_espera > 0:
        deficit_hidrico_litros += 0.9

    tiempo_simulado += 1
    if tiempo_simulado % 60 == 0:
        segundo = tiempo_simulado // 60
        historial_tiempo.append(segundo)
        historial_tanque.append(tanque_reserva.nivel_actual)
        historial_camiones_fila.append(camiones_en_espera)
        historial_deficit_acumulado.append(deficit_hidrico_litros)
        
        if estado_sistema == "OPERATIVO":
            agua_total_desalinizada += caudal_purificado

    pygame.display.flip()
    reloj.tick(60)

pygame.quit()

# --- GENERACIÓN DE REPORTES AVANZADOS AL CERRAR ---
import csv
import matplotlib.pyplot as plt

print("\n--- GENERANDO REPORTES DE OPERACIÓN AVANZADA ---")

archivo_csv = "reporte_desalinizadora_avanzado.csv"
try:
    with open(archivo_csv, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Tiempo (s)", "Nivel Tanque Reserva (L)", "Camiones en Fila", "Deficit Hidrico Acumulado (L)"])
        for i in range(len(historial_tiempo)):
            writer.writerow([historial_tiempo[i], round(historial_tanque[i], 2), historial_camiones_fila[i], round(historial_deficit_acumulado[i], 2)])
    print(f"✔️ Datos profesionales exportados a '{archivo_csv}'")
except Exception as e:
    print(f"❌ Error al guardar el CSV: {e}")

segundos_electricos = tiempo_falla_electrica / 60
segundos_captacion = tiempo_falla_captacion / 60
segundos_filtros = tiempo_falla_filtros / 60
segundos_valvula = tiempo_valvula_cerrada / 60
tiempo_total_fallas = segundos_electricos + segundos_captacion + segundos_filtros + segundos_valvula

print("\n================ INDICES DE RENDIMIENTO Y RESILIENCIA ================")
print(f" · DÉFICIT HÍDRICO TOTAL       : {round(deficit_hidrico_litros, 2)} Litros no distribuidos por fallas.")
print(f" · TIEMPO TOTAL DE INACTIVIDAD : {round(tiempo_total_fallas, 2)} segundos acumulados.")
print(f"   - Falla Eléctrica: {round(segundos_electricos, 1)}s | Filtros: {round(segundos_filtros, 1)}s | Captación: {round(segundos_captacion, 1)}s | Válvula: {round(segundos_valvula, 1)}s")
print(f" · AGUA TOTAL COMPLEMENTADA    : {round(agua_total_desalinizada, 2)} Litros inyectados al foso.")
print("======================================================================\n")

if historial_tiempo:
    fig, axs = plt.subplots(3, 1, figsize=(11, 9.5))
    fig.suptitle("Panel de Análisis de Infraestructura y Resiliencia Hídrica (Punto Fijo)", fontsize=13, fontweight='bold')

    axs[0].plot(historial_tiempo, historial_deficit_acumulado, color="crimson", linewidth=2.5, label="Litros Perdidos")
    axs[0].fill_between(historial_tiempo, historial_deficit_acumulado, color="crimson", alpha=0.15)
    axs[0].set_ylabel("Déficit Acumulado (Litros)")
    axs[0].set_title("1. Pérdida Crítica: Volumen de Agua que Dejó de Distribuirse por Inactividad")
    axs[0].grid(True, linestyle="--", alpha=0.5)
    axs[0].legend(loc="upper left")

    tiempo_inactividad_actual = tiempo_total_fallas
    tiempo_inactividad_mitigado = (segundos_electricos * 0.15) + (segundos_filtros * 0.10) + (segundos_captacion * 0.40) + (segundos_valvula * 0.0)
    
    categorias = ['Simulación Actual\n(Sin Soporte)', 'Con Planta Eléctrica &\nAutolavado de Filtros']
    tiempos_comparativos = [tiempo_inactividad_actual, tiempo_inactividad_mitigado]
    colores_barras = ['#e63946', '#2a9d8f']
    
    axs[1].barh(categorias, tiempos_comparativos, color=colores_barras, height=0.4, edgecolor='black', alpha=0.85)
    axs[1].set_xlabel("Tiempo Total Desconectado (Segundos)", labelpad=4)
    axs[1].set_title("2. Impacto de Reparación: Retorno de Inversión en Tecnologías de Mitigación")
    axs[1].grid(True, linestyle=":", alpha=0.6)
    
    for index, value in enumerate(tiempos_comparativos):
        axs[1].text(value + 0.5, index, f"{round(value, 1)}s", va='center', fontweight='bold')

    axs[2].plot(historial_tiempo, historial_tanque, color="dodgerblue", linewidth=2, label="Inventario del Buffer")
    axs[2].axhline(y=tanque_reserva.capacidad_maxima, color="darkblue", linestyle="--", label="Capacidad Límite (2000L)")
    axs[2].axhline(y=300.0, color="orange", linestyle=":", label="Zona Crítica de Agotamiento")
    axs[2].set_xlabel("Línea de Tiempo de Simulación (Segundos)")
    axs[2].set_ylabel("Volumen Disponible (L)")
    
    minimo_alcanzado = min(historial_tanque)
    if minimo_alcanzado <= 5.0:
        diagnostico = "DIAGNÓSTICO: FALLA DE RESILIENCIA (Buffer de 2000L INSUFICIENTE)"
        col_diag = "darkred"
    else:
        diagnostico = "DIAGNÓSTICO: SISTEMA ESTABLE (Buffer absorbió la falla)"
        col_diag = "darkgreen"
        
    axs[2].set_title("3. Resiliencia de Almacenamiento: Comportamiento del Buffer ante Colapsos", fontsize=10)
    axs[2].grid(True, linestyle="--", alpha=0.5)
    axs[2].plot([], [], ' ', label=diagnostico)
    
    leg = axs[2].legend(loc="upper right", fontsize=8)
    leg.get_texts()[-1].set_color(col_diag)
    leg.get_texts()[-1].set_weight('bold')

    plt.subplots_adjust(hspace=0.5, top=0.90, bottom=0.08)
    print("📊 Desplegando gráficos analíticos profesionales en pantalla...")
    plt.show()
else:
    print("⚠️ Datos insuficientes para organizar los gráficos (Simulación cerrada prematuramente).")

sys.exit()