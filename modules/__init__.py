from mouseMovement import mainFunction
import pyautogui

# Cria uma instância da classe mainFunction
main_func = mainFunction()

# Obtém as dimensões da tela
screen_width, screen_height = pyautogui.size()

# Calcula a posição central da tela
center_x = screen_width // 2
center_y = screen_height // 2

# Move o mouse para o centro da tela
main_func.move(center_x, center_y)

# Deativa a função (encerra a conexão)
main_func.deactivate()
