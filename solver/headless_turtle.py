"""
================================================================
 headless_turtle.py
================================================================

O QUE ESTE ARQUIVO FAZ, EM UMA FRASE:
    Substitui a biblioteca "turtle" do Python (que precisa de uma
    janela grafica de verdade, via Tkinter) por uma versao que
    guarda tudo num dicionario na memoria -- sem nunca abrir
    nenhuma janela.

POR QUE ISSO E NECESSARIO:
    O desafio original (turt.py) usa a biblioteca "turtle" -- a
    mesma que professores usam pra ensinar programacao desenhando
    quadrados e triangulos na tela. Só que aqui ela e usada de um
    jeito criativo: em vez de desenhar, ela "le" pixels de uma
    imagem carregada no canvas e usa a cor de cada pixel como se
    fosse uma instrucao de CPU.

    O problema pratico: a biblioteca "turtle" e construida em cima
    do Tkinter, que por sua vez PRECISA de um ambiente grafico
    (uma tela, ou pelo menos um "simulador de tela" chamado Xvfb)
    pra funcionar. Isso deixa a reproducao do desafio mais
    complicada -- precisa instalar Xvfb, configurar variaveis de
    ambiente, etc.

    A SOLUCAO: como tudo que a tartaruga faz e, no fundo, "andar
    e colorir posicoes", a gente pode simular exatamente esse
    comportamento com um dicionario Python simples: cada posicao
    (x, y) vira uma chave, e a cor que foi "pintada" ali vira o
    valor. Perguntar "qual a cor desse pixel?" vira so um
    ".get()" no dicionario, sem precisar de nenhuma janela.

    IMPORTANTE: este arquivo NAO muda nenhuma regra do desafio.
    Ele so troca "como a tartaruga se move e le cores" por baixo
    dos panos -- o comportamento observavel e identico.
================================================================
"""

# Este dicionario e o "canvas" -- o quadro onde as cores sao
# guardadas. A chave e uma posicao (x, y), sempre numeros inteiros
# (porque toda movimentacao no desafio original acontece em passos
# de 5 unidades, e todo giro e sempre de 90 graus -- entao a
# tartaruga nunca para "no meio" de um pixel).
#
# TODAS as tartarugas do desafio (a que le o codigo, a que le a
# memoria, a que le os registradores, a que le a pilha) compartilham
# ESTE MESMO dicionario -- exatamente como, no jogo original, todas
# elas desenham na MESMA janela/canvas. Isso importa porque uma
# tartaruga pode "ler" uma cor que outra tartaruga "escreveu" antes.
CANVAS = {}


def resetar_canvas():
    """Limpa o canvas inteiro. Usado sempre que queremos testar um
    novo palpite de flag do zero, sem misturar com a execucao
    anterior (senao cores antigas "vazariam" pra tentativa nova)."""
    CANVAS.clear()


class Turtle:
    """
    Substituto do turtle.Turtle() original.

    So implementa os metodos que o desafio realmente usa:
    speed, pensize (ambos ignorados -- so afetam a ANIMACAO visual,
    nunca o resultado), penup, pendown, pencolor, forward, back,
    left, right, pos.

    COMO FUNCIONA POR DENTRO:
    Cada tartaruga guarda sua propria posicao (x, y) e para qual
    direcao esta "olhando" (heading, em graus). Como o desafio
    original SO gira em multiplos de 90 graus, a gente nao precisa
    de nenhuma trigonometria complicada -- so 4 casos possiveis:
    olhando pra direita (0), pra cima (90), pra esquerda (180) ou
    pra baixo (270).
    """

    def __init__(self):
        self.x = 0
        self.y = 0
        self.heading = 0  # 0=direita, 90=cima, 180=esquerda, 270=baixo
        self.pen_down = False  # comeca com a "caneta" levantada
        self.color = (0, 0, 0)  # cor atual da caneta (preto por padrao)

    def speed(self, v):
        # Controla a VELOCIDADE DA ANIMACAO na versao grafica.
        # Sem janela, nao existe animacao -- entao isso nao faz
        # nada aqui, e tudo bem, porque nunca afeta o RESULTADO.
        pass

    def pensize(self, v):
        # Controla a ESPESSURA do traco desenhado. Tambem so
        # importa visualmente, nunca muda o resultado da logica.
        pass

    def penup(self):
        """"Levanta a caneta": a partir de agora, mover a tartaruga
        NAO pinta nada por onde ela passar (so anda)."""
        self.pen_down = False

    def pendown(self):
        """"Abaixa a caneta": a partir de agora, mover a tartaruga
        PINTA cada posicao por onde ela passa, com a cor atual."""
        self.pen_down = True

    def pencolor(self, cor):
        """Define a cor que sera usada na proxima vez que a
        tartaruga se mover com a caneta abaixada."""
        self.color = tuple(int(c) for c in cor)

    def _delta(self, distancia):
        """Traduz 'andar X unidades para frente' em um deslocamento
        (dx, dy), de acordo com a direcao atual (heading). So existem
        4 direcoes possiveis porque so giramos em multiplos de 90."""
        h = round(self.heading) % 360
        if h == 0:
            return distancia, 0
        elif h == 90:
            return 0, distancia
        elif h == 180:
            return -distancia, 0
        elif h == 270:
            return 0, -distancia
        raise ValueError(f"direcao inesperada (nao e multiplo de 90): {self.heading}")

    def forward(self, distancia):
        """Anda 'distancia' unidades na direcao atual.

        DETALHE IMPORTANTE: se a caneta estiver abaixada, a gente
        registra a cor atual na posicao de PARTIDA (antes de andar)
        -- isso reproduz exatamente o comportamento do desenho
        original: 'pencolor(X); forward(5)' pinta o trecho que a
        tartaruga estava prestes a percorrer com a cor X."""
        if self.pen_down:
            CANVAS[(self.x, self.y)] = self.color
        dx, dy = self._delta(distancia)
        self.x += dx
        self.y += dy

    def back(self, distancia):
        """Andar para tras e equivalente a andar para frente com
        distancia negativa (e o que o proprio Python turtle faz)."""
        self.forward(-distancia)

    def left(self, angulo):
        """Gira a tartaruga no sentido anti-horario (esquerda)."""
        self.heading = (self.heading + angulo) % 360

    def right(self, angulo):
        """Gira a tartaruga no sentido horario (direita)."""
        self.heading = (self.heading - angulo) % 360

    def pos(self):
        """Devolve a posicao atual (x, y) -- usado pelo desafio
        original dentro da funcao getColor()."""
        return (self.x, self.y)


class _ScreenFake:
    """Substituto minimo de turtle.Screen(). O desafio original só
    chama .colormode(255) nela, pra dizer 'cores vao de 0 a 255'
    -- algo que ja e verdade por padrao aqui, entao so ignoramos."""

    def colormode(self, v):
        pass


def Screen():
    """Substitui turtle.Screen() -- devolve nosso Screen falso."""
    return _ScreenFake()


def getcanvas():
    """Mantido só por compatibilidade com o nome original
    (turtle.getcanvas()). Na pratica, nunca e chamado de verdade,
    porque a funcao getColor() do desafio e substituida por inteiro
    em turt_headless.py, usando CANVAS diretamente."""
    return None
