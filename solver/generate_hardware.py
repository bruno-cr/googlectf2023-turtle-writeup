#!/usr/bin/env python3
"""
======================================================================
 generate_hardware.py
======================================================================
 Script para renderizar e gerar a imagem representativa do hardware
 visual da CPU Turtle (hardware.png), mapeando fielmente os elementos
 gráficos do canvas do Tkinter com as 4 tartarugas e os módulos.

 COMO RODAR:
     python3 solver/generate_hardware.py
======================================================================
"""

import math
import os
import sys
from pathlib import Path
import turtle
from PIL import Image, ImageDraw, ImageFont

# Localizar a raiz do projeto e a pasta challenge
ROOT_DIR = Path(__file__).resolve().parent.parent
CHALLENGE_DIR = ROOT_DIR / "challenge"

if not (CHALLENGE_DIR / "c.png").exists():
    CHALLENGE_DIR = Path("challenge")
    ROOT_DIR = Path(".")

os.chdir(CHALLENGE_DIR)
turtle.tracer(0, 0)

# Carregar o interpretador original com a flag correta
with open("turt.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace('flag = input("Flag: ")', 'flag = "CTF{iT5_E-tUr+1es/AlL.7h3;waY:d0Wn}"')
code = "\n".join([line for line in code.splitlines() if line.strip() != "run()"])
exec(code)

cv = turtle.getcanvas()
items = cv.find_all()

lines_data = []
for it in items:
    if cv.type(it) == "line":
        coords = cv.coords(it)
        fill = cv.itemcget(it, "fill")
        w = float(cv.itemcget(it, "width") or 1.0)
        lines_data.append((coords, fill, w))

IMG_W, IMG_H = 1420, 870
img = Image.new("RGB", (IMG_W, IMG_H), (248, 250, 252))
draw = ImageDraw.Draw(img)

# Carregar fontes do sistema
font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
font_sec_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
font_sec_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
font_mono_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
font_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)

# Barra de título da janela
draw.rectangle([(0, 0), (IMG_W, 44)], fill=(15, 23, 42))
draw.ellipse([(18, 16), (28, 26)], fill=(239, 68, 68))
draw.ellipse([(36, 16), (46, 26)], fill=(245, 158, 11))
draw.ellipse([(54, 16), (64, 26)], fill=(16, 185, 129))
draw.text((78, 13), "Turtle Graphics (Tkinter) - Anatomia Visual da CPU e Hardware em Execução", font=font_title, fill=(241, 245, 249))

# Painel do Canvas
CANVAS_X0, CANVAS_Y0 = 30, 65
CANVAS_W, CANVAS_H = 680, 780
draw.rectangle([(CANVAS_X0, CANVAS_Y0), (CANVAS_X0 + CANVAS_W, CANVAS_Y0 + CANVAS_H)], fill=(255, 255, 255), outline=(203, 213, 225), width=2)

for gx in range(CANVAS_X0, CANVAS_X0 + CANVAS_W, 35):
    draw.line([(gx, CANVAS_Y0), (gx, CANVAS_Y0 + CANVAS_H)], fill=(248, 250, 252), width=1)
for gy in range(CANVAS_Y0, CANVAS_Y0 + CANVAS_H, 35):
    draw.line([(CANVAS_X0, gy), (CANVAS_X0 + CANVAS_W, gy)], fill=(248, 250, 252), width=1)

SCALE = 1.15
OFFSET_X = CANVAS_X0 + 130
OFFSET_Y = CANVAS_Y0 + 340

def to_img_coords(x, y):
    return OFFSET_X + x * SCALE, OFFSET_Y + y * SCALE

# 1. Desenhar pixels e linhas originais do canvas
for coords, fill, w in lines_data:
    if not fill or fill == "":
        continue
    c_rgb = (int(fill[1:3], 16), int(fill[3:5], 16), int(fill[5:7], 16)) if fill.startswith("#") else (0, 0, 0)
    for k in range(0, len(coords) - 2, 2):
        x1, y1 = to_img_coords(coords[k], coords[k+1])
        x2, y2 = to_img_coords(coords[k+2], coords[k+3])
        draw_w = max(int(w * SCALE), 1)
        if x1 == x2 and y1 == y2:
            r = draw_w // 2 + 1
            draw.rectangle([(x1 - r, y1 - r), (x1 + r, y1 + r)], fill=c_rgb)
        else:
            draw.line([(x1, y1), (x2, y2)], fill=c_rgb, width=draw_w)

# Bounding boxes dos módulos
def draw_component_box(x1, y1, x2, y2, color):
    ix1, iy1 = to_img_coords(x1, y1)
    ix2, iy2 = to_img_coords(x2, y2)
    rx1, rx2 = min(ix1, ix2) - 8, max(ix1, ix2) + 8
    ry1, ry2 = min(iy1, iy2) - 8, max(iy1, iy2) + 8
    draw.rounded_rectangle([(rx1, ry1), (rx2, ry2)], radius=6, outline=color, width=2)
    return (rx1, ry1, rx2, ry2)

box_stack = draw_component_box(-20, -250, -20, 350, (220, 38, 38))
box_code  = draw_component_box(0, -250, 45, 165, (37, 99, 235))
box_regs  = draw_component_box(100, -200, 120, -180, (124, 58, 237))
box_mem   = draw_component_box(60, 0, 185, 105, (5, 150, 105))

# Desenhar cursores das 4 tartarugas
def draw_turtle(x, y, heading_deg, fill_color):
    ix, iy = to_img_coords(x, y)
    rad = math.radians(-heading_deg)
    size = 14
    p_nose = (ix + size * math.cos(rad), iy + size * math.sin(rad))
    p_left = (ix + size * 0.75 * math.cos(rad + 2.4), iy + size * 0.75 * math.sin(rad + 2.4))
    p_back = (ix + size * 0.35 * math.cos(rad + math.pi), iy + size * 0.35 * math.sin(rad + math.pi))
    p_right = (ix + size * 0.75 * math.cos(rad - 2.4), iy + size * 0.75 * math.sin(rad - 2.4))
    
    draw.polygon([p_nose, p_left, p_back, p_right], fill=fill_color, outline=(15, 23, 42), width=1)
    draw.ellipse([(ix-2, iy-2), (ix+2, iy+2)], fill=(255, 255, 255))
    return ix, iy

pos_c = draw_turtle(0, -250, cTurt.heading(), (37, 99, 235))
pos_s = draw_turtle(-20, 350, sTurt.heading(), (220, 38, 38))
pos_r = draw_turtle(100, -200, rTurt.heading(), (124, 58, 237))
pos_m = draw_turtle(60, 0, mTurt.heading(), (5, 150, 105))

# Nomes curtos isolados em espaço em branco (sem sobreposição com os desenhos)
def draw_isolated_badge(bx, by, text, color, pointer_target=None):
    bbox = font_mono_bold.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    if pointer_target:
        px, py = pointer_target
        cx = bx + tw // 2
        cy = by + th // 2
        draw.line([(cx, cy), (px, py)], fill=color, width=1)
        draw.ellipse([(px-2, py-2), (px+2, py+2)], fill=color)

    draw.rounded_rectangle([(bx - 6, by - 4), (bx + tw + 6, by + th + 4)], radius=4, fill=(255, 255, 255), outline=color, width=2)
    draw.text((bx, by - 1), text, font=font_mono_bold, fill=color)

draw_isolated_badge(pos_c[0] + 4, pos_c[1] - 32, "(cTurt)", (37, 99, 235), pointer_target=(pos_c[0] + 6, pos_c[1] - 4))
draw_isolated_badge(box_regs[2] + 16, pos_r[1] - 8, "(rTurt)", (124, 58, 237), pointer_target=(pos_r[0] + 12, pos_r[1]))
draw_isolated_badge(pos_m[0] + 8, box_mem[1] - 32, "(mTurt)", (5, 150, 105), pointer_target=(pos_m[0] + 8, pos_m[1] - 4))
draw_isolated_badge(pos_s[0] - 78, pos_s[1] - 8, "(sTurt)", (220, 38, 38), pointer_target=(pos_s[0] - 6, pos_s[1]))

# Painel Lateral Direito
SIDE_X = 740
SIDE_W = 650

def draw_card(y_top, h, border_color, badge_text, title, desc_lines, connect_target=None):
    if connect_target:
        tx, ty = connect_target
        sy = y_top + h // 2
        draw.line([(tx, ty), (SIDE_X - 10, sy)], fill=(203, 213, 225), width=2)
        draw.ellipse([(tx - 4, ty - 4), (tx + 4, ty + 4)], fill=border_color)
        draw.ellipse([(SIDE_X - 13, sy - 3), (SIDE_X - 7, sy + 3)], fill=border_color)

    draw.rounded_rectangle([(SIDE_X, y_top), (SIDE_X + SIDE_W, y_top + h)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240), width=1)
    draw.rounded_rectangle([(SIDE_X, y_top), (SIDE_X + 6, y_top + h)], radius=3, fill=border_color)
    
    badge_w = len(badge_text) * 8 + 16
    draw.rounded_rectangle([(SIDE_X + 16, y_top + 12), (SIDE_X + 16 + badge_w, y_top + 30)], radius=4, fill=border_color)
    draw.text((SIDE_X + 24, y_top + 14), badge_text, font=font_badge, fill=(255, 255, 255))
    
    draw.text((SIDE_X + 26 + badge_w, y_top + 12), title, font=font_sec_title, fill=(30, 41, 59))
    
    cur_y = y_top + 40
    for line, is_code in desc_lines:
        if is_code:
            draw.text((SIDE_X + 20, cur_y), line, font=font_mono, fill=(51, 65, 85))
        else:
            draw.text((SIDE_X + 20, cur_y), line, font=font_sec_text, fill=(71, 85, 105))
        cur_y += 18

draw_card(
    65, 180,
    (37, 99, 235), "(cTurt)",
    "Ponteiro de Instrução (PC) e 3 Colunas de Bytecode (c.png)",
    [
        ("• Dimensões: 9 colunas de pixels x 83 linhas de instruções.", False),
        ("• Cada instrução usa 3 pixels (9 px total = 3 funções paralelas):", False),
        ("    Coluna 0 (Main): envelope CTF{...}, charset (43..122) e unicidade.", True),
        ("    Coluna 1 (Sort): permuta 30 caracteres centrais via MEM[65..94].", True),
        ("    Coluna 2 (BinSearch): busca binária recursiva validada no oráculo.", True),
        ("• O Program Counter (PC) é a posição física vertical de cTurt na coluna.", False),
        ("• Chamadas de função (CALL) fazem a tartaruga saltar para colunas vizinhas.", False)
    ],
    connect_target=(box_code[2], box_code[1] + 40)
)

draw_card(
    260, 155,
    (124, 58, 237), "(rTurt)",
    "Banco de 9 Registradores em Grade 3x3",
    [
        ("• Grade bidimensional de 3 x 3 pontos com espaçamento de 10 unidades.", False),
        ("• reg_0 a reg_5: registradores de uso geral para cálculo e endereçamento.", False),
        ("• reg_6, reg_7 e reg_8: guardam as flags de condição da instrução CMP:", False),
        ("    reg_6 = igual (==),  reg_7 = menor (<),  reg_8 = maior (>)", True),
        ("• A tartaruga rTurt se move para ler ou atualizar a cor de cada célula.", False)
    ],
    connect_target=(box_regs[2], (box_regs[1] + box_regs[3]) // 2)
)

draw_card(
    430, 175,
    (5, 150, 105), "(mTurt)",
    "Grade Principal de Dados (m.png - 25x21 células)",
    [
        ("• Dimensões: 25 colunas x 21 linhas = 525 células (passo de 5 pixels).", False),
        ("• Endereços 0 a 34: 35 caracteres da flag sobrescrevem os primeiros pixels.", False),
        ("• Endereços 65 a 94: tabela de permutação da Função 1 (30 bytes).", False),
        ("• Endereços 95 a 518: oráculo determinístico com 424 respostas da busca.", False),
        ("• Mecanismo de escrita: mTurt avança e carimba cor por cima (ids[::-1]).", False),
        ("  Fórmula de coordenadas: x = (addr % 25) * 5, y = (addr // 25) * 5", True)
    ],
    connect_target=(box_mem[2], (box_mem[1] + box_mem[3]) // 2)
)

draw_card(
    620, 155,
    (220, 38, 38), "(sTurt)",
    "Segmento Linear LIFO e Ponteiro de Pilha (SP)",
    [
        ("• Linha reta de 120 posições verticais (segmento rosa de 120x5 unidades).", False),
        ("• O Stack Pointer (SP) é a posição física da tartaruga sTurt na reta.", False),
        ("• Guarda endereços de retorno de chamadas de função (CALL e RET).", False),
        ("• STACK[3..82]: vetor de contagem para validação de unicidade da flag.", False),
        ("• Empilhar avança sTurt; desempilhar (DROP/RET) recua o cursor para trás.", False)
    ],
    connect_target=(box_stack[2] + 4, box_stack[3] - 40)
)

FOOTER_Y = 795
draw.rectangle([(SIDE_X, FOOTER_Y), (SIDE_X + SIDE_W, FOOTER_Y + 50)], fill=(241, 245, 249), outline=(226, 232, 240), width=1)
draw.text((SIDE_X + 16, FOOTER_Y + 10), "Ciclo de Instrução Visual da Máquina:", font=font_sec_title, fill=(30, 41, 59))
draw.text((SIDE_X + 16, FOOTER_Y + 28), "A CPU lê instruções e dados diretamente da tela via find_overlapping(x, y, x, y).", font=font_sec_text, fill=(71, 85, 105))

OUT_PATH = ROOT_DIR / "hardware.png"
img.save(OUT_PATH, "PNG", optimize=True)
print(f"hardware.png gerado com sucesso em: {OUT_PATH}")
