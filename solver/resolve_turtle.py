"""
================================================================
 resolve_turtle.py
================================================================

Script principal: reconstrói a flag do desafio Turtle e valida a
solução rodando o programa original (headless) de ponta a ponta.

COMO RODAR:
    cd solver/
    pip install -r requirements.txt
    python3 resolve_turtle.py

O QUE ESSE SCRIPT FAZ, EM 4 PASSOS:

  Passo 1 — Carrega a memória (m.png) com uma flag "placeholder"
            de 35 caracteres, só para poder navegar pela memória
            com as funções originais do jogo (readM/readC).
            (Os primeiros 35 endereços viram a flag placeholder;
            isso não atrapalha, porque os dois arrays que
            precisamos estão em endereços mais altos, a partir do
            35 — ver docs/redescoberta-opcodes.md para o raciocínio
            completo.)

  Passo 2 — Extrai dois arrays gravados na memória (a partir do
            endereço 35): o array de REORDENAÇÃO (uma permutação
            de 30 posições) e o array de RESULTADOS DA BUSCA
            BINÁRIA (que indica, para cada caractere ASCII
            possível, se ele faz parte da flag ou não).

  Passo 3 — Reconstrói a flag combinando os dois arrays: primeiro
            descobre QUAIS caracteres pertencem à flag (mas ainda
            fora de ordem), depois usa o array de reordenação para
            colocá-los na posição certa.

  Passo 4 — VALIDAÇÃO FINAL: roda o programa original completo
            (a VM inteira, instrução por instrução, headless) com
            a flag reconstruída como entrada, e confirma que ele
            responde "correct" — prova de ponta a ponta, não só
            uma extração estática de arrays.
"""

import shutil
import time
from pathlib import Path

import headless_turtle
import turt_headless as jogo


# -----------------------------------------------------------------
# ADAPTAÇÃO DE CONVENIÊNCIA (não muda lógica nenhuma): o código
# original (turt_headless.py, copiado fielmente de turt.py) sempre
# abre os arquivos "c.png" e "m.png" a partir do DIRETÓRIO ATUAL
# (é assim que o desafio original também funciona). Para não exigir
# que quem for apresentar precise copiar esses arquivos manualmente
# toda vez, copiamos automaticamente daqui de challenge/ antes de
# rodar, se ainda não estiverem presentes.
# -----------------------------------------------------------------
_PASTA_DESAFIO = Path(__file__).parent.parent / "challenge"
for _nome in ("c.png", "m.png"):
    if not Path(_nome).exists():
        shutil.copy(_PASTA_DESAFIO / _nome, _nome)


# -----------------------------------------------------------------
# Constantes descobertas durante a análise (ver
# docs/redescoberta-opcodes.md para o processo completo de como
# esses números foram encontrados)
# -----------------------------------------------------------------

TAMANHO_DA_FLAG = 35                 # exigido por turt.py (`if len(flag) != 35`)
ENDERECO_ARRAY_ORDEM = 65            # início do array de reordenação
TAMANHO_ARRAY_ORDEM = 30             # 30 posições (flag interna, sem "CTF{" e "}")
ENDERECO_ARRAY_BUSCA = 95            # início do array de resultados da busca binária
TAMANHO_ARRAY_BUSCA = 424            # 424 entradas brutas (múltiplas por caractere testado)
PRIMEIRO_ASCII_TESTADO = 43          # '+' — primeiro caractere candidato
ULTIMO_ASCII_TESTADO = 122           # 'z' — último caractere candidato (inclusive)


def extrai_array_ordem():
    """Lê o array de reordenação da memória (endereços 65 a 94).

    Esse array é uma PERMUTAÇÃO dos números de 0 a 29 — ou seja,
    diz "o caractere na posição i da lista de achados vai para a
    posição ordem[i] da flag final"."""
    return [jogo.readC(jogo.readM(a))
            for a in range(ENDERECO_ARRAY_ORDEM, ENDERECO_ARRAY_ORDEM + TAMANHO_ARRAY_ORDEM)]


def extrai_array_busca():
    """Lê o array bruto de resultados da busca binária (endereços
    95 a 518 — 424 entradas).

    Esse array tem MUITO mais entradas do que caracteres testados,
    porque a busca binária recursiva grava um resultado a CADA
    comparação intermediária (valores 1 e 2), não só o resultado
    final. Só os valores 3 e 4 marcam o resultado FINAL de cada
    caractere testado (3 = achou, 4 = não achou) — por isso
    filtramos só esses dois valores, na seção seguinte."""
    return [jogo.readC(jogo.readM(a))
            for a in range(ENDERECO_ARRAY_BUSCA, ENDERECO_ARRAY_BUSCA + TAMANHO_ARRAY_BUSCA)]


def reconstroi_flag(array_ordem, array_busca):
    """Combina os dois arrays extraídos para reconstruir a flag."""

    # Mantém só os resultados FINAIS (3=achou, 4=não achou),
    # descartando os resultados intermediários (1 e 2) da recursão
    resultados_finais = [v for v in array_busca if v in (3, 4)]

    candidatos_ascii = list(range(PRIMEIRO_ASCII_TESTADO, ULTIMO_ASCII_TESTADO + 1))
    assert len(candidatos_ascii) == len(resultados_finais), (
        "Número de resultados finais não bate com o número de "
        "caracteres candidatos testados — a memória pode ter uma "
        "estrutura diferente do esperado."
    )

    # Os caracteres "achados" (valor == 3), na ordem em que foram
    # testados (ainda NÃO é a ordem final da flag)
    achados = [chr(c) for c, v in zip(candidatos_ascii, resultados_finais) if v == 3]

    assert len(achados) == len(array_ordem), (
        f"Array de reordenação tem {len(array_ordem)} posições, mas "
        f"foram achados {len(achados)} caracteres — algo não bate."
    )

    # A posição k da flag final é achados[ordem[k]] — ou seja, o
    # array de reordenação diz, para cada posição final, QUAL
    # caractere achado (por índice) deve ir ali.
    flag_interna = "".join(achados[posicao] for posicao in array_ordem)

    return "CTF{" + flag_interna + "}"


if __name__ == "__main__":
    print("=" * 70)
    print("PASSO 1 — Carregando a memória (m.png) com um placeholder")
    print("=" * 70)
    headless_turtle.resetar_canvas()
    jogo.loadM("A" * TAMANHO_DA_FLAG)  # placeholder — só p/ poder navegar a memória
    print(f"Memória carregada. Placeholder de {TAMANHO_DA_FLAG} caracteres em uso.\n")

    print("=" * 70)
    print("PASSO 2 — Extraindo os dois arrays gravados na memória")
    print("=" * 70)
    array_ordem = extrai_array_ordem()
    array_busca = extrai_array_busca()

    print(f"Array de reordenação ({len(array_ordem)} posições):")
    print(f"  {array_ordem}")
    print(f"  É permutação válida de 0..{TAMANHO_ARRAY_ORDEM - 1}? "
          f"{sorted(array_ordem) == list(range(TAMANHO_ARRAY_ORDEM))}")
    print(f"Array de resultados da busca ({len(array_busca)} entradas brutas).\n")

    print("=" * 70)
    print("PASSO 3 — Reconstruindo a flag")
    print("=" * 70)
    flag_reconstruida = reconstroi_flag(array_ordem, array_busca)
    print(f"Flag reconstruída: {flag_reconstruida}")
    print(f"Tamanho: {len(flag_reconstruida)} (esperado: {TAMANHO_DA_FLAG})\n")

    print("=" * 70)
    print("PASSO 4 — Validação final: rodando a VM completa, do zero")
    print("=" * 70)
    inicio = time.time()
    resultado = jogo.roda_com_flag(flag_reconstruida)
    tempo_total = time.time() - inicio

    print(f"Resultado da execução completa: {resultado}")
    print(f"Tempo: {tempo_total:.2f}s")

    if resultado == "correct":
        print("\n[SUCESSO] A flag reconstruída foi ACEITA pelo programa original,")
        print("rodando de ponta a ponta.")
    else:
        print("\n[FALHA] A flag reconstruída NÃO foi aceita — revisar a extração.")
