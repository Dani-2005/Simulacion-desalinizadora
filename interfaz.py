import pygame

class Boton:
    def __init__(self, x, y, ancho, alto, texto, color_base, color_hover, color_texto=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color_base = color_base
        self.color_hover = color_hover
        self.color_actual = color_base
        self.color_texto = color_texto

    def dibujar(self, pantalla, fuente):
        # Efecto Hover (cambia de color si el mouse está encima)
        lista_mouse = pygame.mouse.get_pos()
        if self.rect.collidepoint(lista_mouse):
            self.color_actual = self.color_hover
        else:
            self.color_actual = self.color_base

        # Dibujar el rectángulo del botón
        pygame.draw.rect(pantalla, self.color_actual, self.rect, border_radius=8)
        # Dibujar un borde sutil
        pygame.draw.rect(pantalla, (200, 200, 200), self.rect, width=1, border_radius=8)

        # Renderizar el texto centrado
        superficie_texto = fuente.render(self.texto, True, self.color_texto)
        rect_texto = superficie_texto.get_rect(center=self.rect.center)
        pantalla.blit(superficie_texto, rect_texto)

    def clickeado(self, evento):
        # Verifica si el evento es un clic izquierdo del mouse dentro del botón
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect.collidepoint(evento.pos):
                return True
        return False