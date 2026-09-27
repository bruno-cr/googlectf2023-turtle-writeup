"""
================================================================
 turt_headless.py
================================================================

O QUE ESTE ARQUIVO E:
    Uma copia do arquivo original do desafio, `challenge/turt.py`,
    adaptada para rodar SEM Tkinter/Xvfb (sem janela grafica).

O QUE FOI MUDADO EM RELACAO AO ORIGINAL (e SO ISSO):
    1. `import turtle`  vira  `import headless_turtle as turtle`
       (troca a biblioteca grafica pelo nosso shim -- ver
       headless_turtle.py).
    2. A funcao `getColor()` foi reescrita -- no original, ela
       perguntava pro Tkinter "que cor tem nesse pixel da tela?".
       Aqui, ela pergunta pro dicionario `headless_turtle.CANVAS`.
    3. O bloco final do script original (as ultimas ~12 linhas,
       que liam a flag digitada e rodavam o programa uma unica
       vez) foi transformado na funcao `roda_com_flag(flag)`,
       reutilizavel -- assim da pra testar varias flags sem
       reiniciar o programa inteiro a cada vez.
    4. A funcao `run()` ganhou um limite de passos (`max_passos`)
       e retorna uma STRING ("correct"/"wrong"/"timeout") em vez de
       imprimir na tela e encerrar o programa com `exit(0)` -- pra
       podermos capturar o resultado programaticamente.

TODO O RESTO -- cada linha de loadM, readM, writeM, loadS, readS,
writeS, loadR, readR, writeR, loadC, drawImg, getRNum, read, write,
readRVal, writeRVal, writePVal, readPVal, readPA, readC,
readOneByteC, cToColor, e a logica interna de run() -- e uma copia
EXATA do arquivo original, sem nenhuma mudanca de comportamento.
Isso e proposital: queremos ter certeza de que estamos rodando o
MESMO programa, so sem depender de uma janela grafica.
================================================================
"""

import headless_turtle
import headless_turtle as turtle
from PIL import Image


def hexToRgb(hx):
    """Converte uma cor no formato hexadecimal ('#rrggbb') para uma
    tupla (r, g, b). Mantida do original por completude, mas nao e
    mais usada de fato (so fazia sentido quando liamos cores reais
    do Tkinter, que vinham nesse formato de texto)."""
    return (int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16))


def getColor(turt):
    """
    ADAPTADO (era a unica funcao que dependia do Tkinter de verdade).

    ORIGINAL: perguntava pro canvas real do Tkinter "que cor tem
    bem em cima da posicao onde a tartaruga X esta agora?".

    AQUI: a mesma pergunta, respondida consultando nosso dicionario
    headless_turtle.CANVAS. Se nada foi pintado ali ainda, devolve
    branco (255,255,255) -- exatamente o comportamento do original
    (fundo branco = "nada desenhado aqui").
    """
    return headless_turtle.CANVAS.get((turt.x, turt.y), (255, 255, 255))


def drawImg(path, turt):
    """
    Varre uma imagem (c.png ou m.png) pixel por pixel e faz a
    tartaruga 'desenhar' cada pixel na posicao correspondente do
    canvas -- ou seja, isso e o que transforma um arquivo PNG comum
    numa regiao de memoria/codigo que o resto do programa consegue
    ler depois.

    Percorre linha por linha (yy), e dentro de cada linha, coluna
    por coluna (xx): pinta a cor daquele pixel, anda 5 unidades
    para a direita. No fim de cada linha, volta pro inicio (x=0
    daquela linha) e desce para a proxima.

    Cada "unidade de imagem" (1 pixel) corresponde a exatamente 5
    unidades no canvas -- e por isso todo o resto do codigo sempre
    multiplica posicoes por 5 (ex: `mTurt.forward(a*5)`).
    """
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    turt.pendown()
    for yy in range(h):
        for xx in range(w):
            turt.pencolor(px[xx, yy])
            turt.forward(5)
        turt.penup()
        turt.back(w * 5)
        turt.right(90)
        turt.forward(5)
        turt.left(90)
        turt.pendown()
    turt.penup()
    turt.left(90)
    turt.forward(h * 5)
    turt.right(90)


# =================================================================
# MEMORIA (M) -- carregada a partir de m.png
# =================================================================
# A "memoria" do programa e uma grade de 25 colunas de largura
# (por isso os calculos `a % 25` para achar a coluna e `a // 25`
# para achar a linha, em varias funcoes abaixo).

mTurt = None  # a tartaruga responsavel por ler/escrever a memoria


def loadM(flag):
    """
    Prepara a memoria: desenha m.png no canvas, e DEPOIS sobrescreve
    as primeiras 35 posicoes (enderecos 0 a 34) com os codigos ASCII
    da flag que estamos testando.

    Ou seja: o conteudo de m.png so define a memoria a partir do
    endereco 35 em diante -- os primeiros 35 enderecos SEMPRE viram
    a flag testada, nao importa o que estivesse desenhado ali na
    imagem original. E por isso, mais abaixo no solver, que os
    arrays importantes (a ordem de reconstrucao da flag, e os
    resultados da busca binaria) estao guardados a partir do
    endereco 35 -- justamente pra nao serem sobrescritos.
    """
    global mTurt
    mTurt = turtle.Turtle()
    mTurt.speed(0)
    mTurt.pensize(5)
    mTurt.penup()
    mTurt.forward(12 * 5)
    drawImg("m.png", mTurt)
    mTurt.pendown()
    for i in range(len(flag)):
        mTurt.pencolor((ord(flag[i]), 0, 0))
        mTurt.forward(5)
        if i == 24:
            # a flag tem ate 35 caracteres, mas a memoria so tem 25
            # colunas -- entao, ao chegar na posicao 25, precisa
            # "quebrar linha" e continuar na linha de baixo.
            mTurt.penup()
            mTurt.back(25 * 5)
            mTurt.right(90)
            mTurt.forward(5)
            mTurt.left(90)
            mTurt.pendown()
    mTurt.penup()
    mTurt.back(10 * 5)
    mTurt.left(90)
    mTurt.forward(5)
    mTurt.right(90)


def readM(a):
    """Le o conteudo (cor) do endereco de memoria `a`. Navega ate a
    coluna (a%25) e linha (a//25) corretas, le a cor, e volta pro
    lugar de onde partiu (importante: NAO deixa efeito colateral na
    posicao da tartaruga)."""
    mTurt.forward((a % 25) * 5)
    mTurt.right(90)
    mTurt.forward((a // 25) * 5)
    c = getColor(mTurt)
    mTurt.right(90)
    mTurt.forward((a % 25) * 5)
    mTurt.right(90)
    mTurt.forward((a // 25) * 5)
    mTurt.right(90)
    return c


def writeM(a, c):
    """Escreve a cor `c` no endereco de memoria `a`. Mesma ideia de
    navegacao de readM, so que no final pinta em vez de so ler."""
    mTurt.right(90)
    mTurt.forward((a // 25) * 5)
    mTurt.left(90)
    mTurt.forward((a % 25) * 5)
    mTurt.pencolor(c)
    mTurt.pendown()
    mTurt.forward(0)
    mTurt.penup()
    mTurt.left(90)
    mTurt.forward((a // 25) * 5)
    mTurt.left(90)
    mTurt.forward((a % 25) * 5)
    mTurt.left(180)


# =================================================================
# PILHA (S / "Stack") -- separada da memoria principal
# =================================================================

sTurt = None  # a tartaruga responsavel pela pilha


def loadS():
    """Prepara a pilha: uma faixa de 120 posicoes, toda inicializada
    com a cor (255, 128, 128) -- um valor "neutro" que nao coincide
    com nenhum opcode real (evita confusao acidental de leitura)."""
    global sTurt
    sTurt = turtle.Turtle()
    sTurt.speed(0)
    sTurt.pensize(5)
    sTurt.penup()
    sTurt.left(90)
    sTurt.forward(50 * 5)
    sTurt.left(90)
    sTurt.forward(4 * 5)
    sTurt.left(90)
    sTurt.pencolor((255, 128, 128))
    sTurt.pendown()
    sTurt.forward(120 * 5)
    sTurt.penup()


def readS(a):
    """Le a posicao `a` da pilha (relativa ao topo atual)."""
    sTurt.forward(a * 5)
    c = getColor(sTurt)
    sTurt.back(a * 5)
    return c


def writeS(a, c):
    """Escreve a cor `c` na posicao `a` da pilha."""
    sTurt.forward(a * 5)
    sTurt.pencolor(c)
    sTurt.pendown()
    sTurt.forward(0)
    sTurt.penup()
    sTurt.back(a * 5)


# =================================================================
# REGISTRADORES (R) -- 9 "variaveis" de uso geral (numeradas 0-8),
# dispostas numa grade 3x3
# =================================================================

rTurt = None  # a tartaruga responsavel pelos registradores


def loadR():
    """Prepara os 9 registradores (grade 3x3), todos comecando
    pretos (0,0,0) -- equivalente a "zerados"."""
    global rTurt
    rTurt = turtle.Turtle()
    rTurt.speed(0)
    rTurt.pensize(5)
    rTurt.penup()
    rTurt.forward(20 * 5)
    rTurt.left(90)
    rTurt.forward(40 * 5)
    rTurt.right(90)
    sTurt.pencolor((0, 0, 0))
    for i in range(3):
        for j in range(3):
            rTurt.pendown()
            rTurt.forward(0)
            rTurt.penup()
            rTurt.forward(2 * 5)
        rTurt.back(6 * 5)
        rTurt.right(90)
        rTurt.forward(2 * 5)
        rTurt.left(90)
    rTurt.left(90)
    rTurt.forward(6 * 5)
    rTurt.right(90)


def readR(n):
    """Le o valor do registrador numero `n` (0 a 8)."""
    rTurt.forward((n % 3) * 10)
    rTurt.right(90)
    rTurt.forward((n // 3) * 10)
    c = getColor(rTurt)
    rTurt.right(90)
    rTurt.forward((n % 3) * 10)
    rTurt.right(90)
    rTurt.forward((n // 3) * 10)
    rTurt.right(90)
    return c


def writeR(n, c):
    """Escreve a cor `c` no registrador numero `n`."""
    rTurt.forward((n % 3) * 10)
    rTurt.right(90)
    rTurt.forward((n // 3) * 10)
    rTurt.pencolor(c)
    rTurt.pendown()
    rTurt.forward(0)
    rTurt.penup()
    rTurt.right(90)
    rTurt.forward((n % 3) * 10)
    rTurt.right(90)
    rTurt.forward((n // 3) * 10)
    rTurt.right(90)


# =================================================================
# CODIGO (C) -- carregado a partir de c.png; e o "programa" em si
# =================================================================

cTurt = None  # a tartaruga responsavel por ler o codigo (o "ip"/ponteiro de instrucao)


def loadC():
    """Prepara o codigo: desenha c.png no canvas. Repare que cTurt
    NUNCA usa pendown() depois disso -- ela so LE o codigo, nunca
    escreve nele (o codigo e fixo durante toda a execucao)."""
    global cTurt
    cTurt = turtle.Turtle()
    cTurt.speed(0)
    cTurt.pensize(5)
    cTurt.penup()
    cTurt.left(90)
    cTurt.forward(50 * 5)
    cTurt.right(90)
    drawImg("c.png", cTurt)


# =================================================================
# Decodificacao de operandos
# =================================================================

def getRNum(colorOrInt):
    """Converte um valor de cor (ou so o componente vermelho dela)
    no NUMERO do registrador correspondente. A formula `(v-20)//40`
    e a maneira como o desafio codifica "qual registrador" dentro
    do valor de um pixel."""
    if type(colorOrInt) == tuple:
        colorOrInt = colorOrInt[0]
    return (colorOrInt - 20) // 40


def read(op, isR, isP, isC):
    """Le um "operando" -- que pode ser um registrador (isR), um
    endereco de memoria/pilha (isP), ou uma constante literal (isC),
    dependendo de quais flags vieram ligadas no opcode."""
    if isP:
        return readPVal(op, isR, isC)
    elif isR:
        return readRVal(getRNum(op))
    elif isC:
        return readC(op)
    raise BaseException("invalid insn")


def readRVal(rNum):
    """Le o valor NUMERICO (ja decodificado) do registrador `rNum`."""
    return readC(readR(rNum))


def write(op, val, isR, isP, isC):
    """Escreve um valor num operando -- mesma logica de `read`, so
    que na direcao contraria."""
    if isP:
        writePVal(op, val, isR, isC)
    elif isR:
        writeRVal(getRNum(op), val)
    else:
        raise BaseException("invalid insn")


def writeRVal(rNum, val):
    """Escreve um valor NUMERICO no registrador `rNum` (convertendo
    pra cor antes de gravar)."""
    writeR(rNum, cToColor(val))


def writePVal(op, val, isS, isC):
    """Escreve um valor numa posicao de memoria ou pilha, calculada
    a partir do operando `op` (que pode envolver registradores)."""
    a = readPA(op, isC)
    if isS:
        writeS(a, cToColor(val))
    else:
        writeM(a, cToColor(val))


def readPVal(op, isS, isC):
    """Le um valor de uma posicao de memoria ou pilha, calculada a
    partir do operando `op`."""
    a = readPA(op, isC)
    if isS:
        return readC(readS(a))
    else:
        return readC(readM(a))


def readPA(op, isC):
    """Calcula um ENDERECO a partir de um operando -- pode ser um
    endereco fixo (isC) ou uma soma de ate 2 registradores com um
    deslocamento fixo (como "endereco = R[2] + R[5] + 3", parecido
    com o modo de enderecamento de assembly de verdade)."""
    if isC:
        return readC(op)
    a = 0
    if op[0] != 0:
        a = readRVal(getRNum(op[0]))
    if op[1] != 0:
        a += readRVal(getRNum(op[1]))
    a += readOneByteC(op[2])
    return a


def readC(op):
    """Decodifica os 3 bytes de uma cor (R, G, B) como um numero
    inteiro de 24 bits, COM SINAL (ou seja, valores "grandes" viram
    negativos -- e a mesma ideia de complemento de dois usada em
    processadores de verdade)."""
    c = op[0] + (op[1] << 8) + (op[2] << 16)
    if c >= (256 ** 3) // 2:
        c = -((256 ** 3) - c)
    return c


def readOneByteC(val):
    """Igual a readC, mas para um unico byte (8 bits com sinal, de
    -128 a 127) -- usado nos deslocamentos de endereco."""
    if val > 256 // 2:
        return -(256 - val)
    return val


def cToColor(val):
    """Caminho inverso de readC: transforma um numero inteiro de
    volta numa cor (lista [R, G, B]), pronta pra ser "pintada"."""
    if val < 0:
        val = 256 ** 3 + val
    return [val % 256, (val >> 8) % 256, (val >> 16) % 256]


# =================================================================
# O "CPU": executa uma instrucao por vez, lendo o opcode a partir
# da cor mascarada (ignorando os 2 bits menos significativos de
# cada canal, que carregam as FLAGS dos operandos)
# =================================================================

def run(max_passos=2_000_000):
    """
    Este e o "loop principal da CPU". A cada volta:
      1. Le a cor no ponteiro de instrucao atual (color0) -- essa
         cor, MASCARADA (ignorando os 2 bits menos significativos
         de cada canal), identifica QUAL operacao executar.
      2. Le mais duas cores (color1, color2) -- os operandos.
      3. Executa a operacao correspondente.
      4. Avanca o ponteiro de instrucao (exceto quando um salto ja
         mudou ele explicitamente).

    A TABELA DE CORES -> OPERACOES abaixo (os varios `cmpcolor ==
    (...)`) e exatamente a tabela de opcodes que documentamos, com
    o processo de redescoberta detalhado, em
    docs/redescoberta-opcodes.md.

    ADAPTACAO (nao existia no original): em vez de `print(...)` +
    `exit(0)`, devolvemos uma STRING com o resultado -- assim
    conseguimos testar varias flags programaticamente. Tambem
    adicionamos um limite de passos (`max_passos`) por seguranca,
    caso algum palpite de flag entre num loop infinito.
    """
    passos = 0
    while True:
        passos += 1
        if passos > max_passos:
            return "timeout"

        # --- Busca (fetch): le opcode + 2 operandos ---
        color0 = getColor(cTurt)
        cmpcolor = (color0[0] & 0xFC, color0[1] & 0xFC, color0[2] & 0xFC)
        cTurt.forward(5)
        color1 = getColor(cTurt)
        cTurt.forward(5)
        color2 = getColor(cTurt)
        cTurt.back(2 * 5)  # volta pro inicio da instrucao (mantem o "ip" consistente)

        # Os 2 bits menos significativos de cada canal de color0 sao
        # as FLAGS que dizem como interpretar color1/color2 (registrador?
        # endereco de memoria/pilha? constante literal?):
        isR1 = color0[0] & 1 != 0
        isP1 = color0[1] & 1 != 0
        isC1 = color0[2] & 1 != 0
        isR2 = color0[0] & 2 != 0
        isP2 = color0[1] & 2 != 0
        isC2 = color0[2] & 2 != 0

        # --- Execucao (decode + execute) ---
        if cmpcolor == (0, 252, 0):
            # "success": a flag testada passou em TODAS as verificacoes
            return "correct"
        elif cmpcolor == (252, 0, 0):
            # "fail": alguma verificacao falhou
            return "wrong"
        elif cmpcolor == (204, 204, 252):
            # ajusta o ponteiro da PILHA (equivalente a "sp += valor")
            sTurt.forward(readC(color1) * 5)
        elif cmpcolor == (220, 252, 0) or cmpcolor == (252, 188, 0) or cmpcolor == (64, 224, 208) or cmpcolor == (156, 224, 188) or cmpcolor == (100, 148, 236) or cmpcolor == (252, 124, 80):
            # Grupo de instrucoes "duas entradas, uma saida":
            # mov, lea, add, sub, shr, cmp
            if cmpcolor == (252, 188, 0):
                # "lea" (load effective address): o segundo operando
                # NAO e lido como valor -- e o proprio ENDERECO
                # calculado que interessa (por isso chama readPA
                # direto, em vez de "read").
                val2 = readPA(color2, isC2)
            else:
                val2 = read(color2, isR2, isP2, isC2)

            if cmpcolor == (220, 252, 0) or cmpcolor == (252, 188, 0):
                # mov / lea: so escreve val2 no destino
                write(color1, val2, isR1, isP1, isC1)
            elif cmpcolor == (64, 224, 208):
                # add: destino = destino + val2
                val1 = read(color1, isR1, isP1, isC1)
                write(color1, val1 + val2, isR1, isP1, isC1)
            elif cmpcolor == (156, 224, 188):
                # sub: destino = destino - val2
                val1 = read(color1, isR1, isP1, isC1)
                write(color1, val1 - val2, isR1, isP1, isC1)
            elif cmpcolor == (100, 148, 236):
                # shr: destino = destino >> val2 (deslocamento de bits)
                val1 = read(color1, isR1, isP1, isC1)
                write(color1, val1 >> val2, isR1, isP1, isC1)
            elif cmpcolor == (252, 124, 80):
                # cmp: compara val1 com val2 e grava o resultado em
                # 3 registradores "de bandeira" (parecido com as
                # flags ZF/CF de um processador real): R6=igual,
                # R7=menor, R8=maior. O valor magico 16581630 e so
                # uma cor "true" arbitraria (equivale a "nao-zero").
                val1 = read(color1, isR1, isP1, isC1)
                writeRVal(6, 16581630 if (val1 == val2) else 0)
                writeRVal(7, 16581630 if (val1 < val2) else 0)
                writeRVal(8, 16581630 if (val1 > val2) else 0)
        elif cmpcolor == (220, 48, 96):
            # Salto condicional (jcc). As flags de color0 dizem QUAIS
            # bandeiras (igual/menor/maior, lidas dos registradores
            # 6/7/8) fazem o salto acontecer -- se TODAS as 4 flags
            # estiverem ligadas ao mesmo tempo, o salto sempre
            # acontece (e o "jmp incondicional").
            e = readRVal(6)
            l = readRVal(7)
            g = readRVal(8)
            if (color0[0] & 1 != 0 and e) or (color0[1] & 1 != 0 and not e) or (color0[0] & 2 != 0 and l) or (color0[1] & 2 != 0 and g):
                cTurt.right(90)
                cTurt.forward((readC(color1) - 1) * 5)
                cTurt.left(90)
        elif cmpcolor == (252, 0, 252):
            # call: guarda o "endereco de retorno" na pilha (a
            # posicao atual do codigo) e pula para uma nova posicao
            # (uma nova COLUNA e LINHA no canvas -- e assim que o
            # programa "chama" uma das 3 funcoes/colunas do c.png).
            sTurt.back(5)
            writeS(0, (color1[0], color1[1], 127))
            cTurt.forward(color1[0] * 5)
            cTurt.left(90)
            cTurt.forward((color1[1] + 1) * 5)
            cTurt.right(90)
        elif cmpcolor == (128, 0, 128):
            # ret: volta pro endereco de retorno guardado na pilha
            cTurt.left(90)
            cTurt.forward(readC(color1) * 5)
            cTurt.left(90)
            cTurt.forward(readS(0)[0] * 5)
            cTurt.left(90)
            cTurt.forward(readS(0)[1] * 5)
            cTurt.left(90)
            sTurt.forward(5)
        else:
            raise BaseException("unknown: %s" % str(cmpcolor))

        # Avanca o ponteiro de instrucao pra proxima linha (a menos
        # que um salto/call/ret ja tenha mudado a posicao acima)
        cTurt.right(90)
        cTurt.forward(5)
        cTurt.left(90)


# =================================================================
# ADAPTACAO: bloco final reutilizavel (nao existia como funcao no
# original -- la, era so codigo solto no fim do arquivo, rodando
# uma unica vez por execucao do programa)
# =================================================================

def roda_com_flag(flag, max_passos=2_000_000):
    """
    Equivalente a rodar `python3 turt.py` do zero e digitar `flag`
    quando ele perguntar -- só que como uma funcao Python comum,
    que podemos chamar varias vezes seguidas.

    Devolve uma destas strings:
      "tamanho_errado" -- a flag nao tem 35 caracteres
      "correct"        -- a flag foi ACEITA pelo programa
      "wrong"          -- a flag foi REJEITADA pelo programa
      "timeout"        -- passou de max_passos sem terminar (nunca
                           deveria acontecer com uma flag valida
                           de verdade; existe so como seguranca)
    """
    headless_turtle.resetar_canvas()  # começa do zero, sem "lixo" da rodada anterior

    if len(flag) != 35:
        return "tamanho_errado"

    loadM(flag)
    loadS()
    loadR()
    loadC()
    return run(max_passos=max_passos)
