# Google CTF 2023 — Turtle (Reverse Engineering)

Write-up e reprodução do desafio **Turtle**, categoria Reverse
Engineering do Google CTF 2023, desenvolvido como avaliação (E3) da
disciplina **Segurança Cibernética (CCO-04.2.01)** — PPGCC, UFSCar.

## Membros do grupo

- Thayná Marostica Machado da Silva
- Bruno Camargo Ribeiro
- Bruno Hiroki Nagao Anhaia
- Gabriel Alves Moreira
- Jonathan Choy Rivera
- Cilene Renata Real
- Emerson Hermann Lira dos Santos
- Stephanie Maria Braga

---

## 1. Identificação do desafio e objetivo

**Turtle** entrega três arquivos:

- `turt.py` — um script Python que usa a biblioteca **Turtle
  Graphics** (normalmente usada para desenhar formas simples) de um
  jeito não convencional: a "tartaruga" se comporta como uma **CPU**.
- `c.png` — uma imagem de **9×83 pixels** que codifica o *código* do
  programa: cada trinca de pixels numa linha é uma instrução.
- `m.png` — uma imagem de **25×21 pixels** que codifica a *memória*
  inicial do programa.

**A ideia central:** `turt.py` não é o "programa" em si — é o
**hardware** (a CPU). O programa de verdade (a lógica que decide se
uma flag está certa) está **codificado como cores de pixels** dentro
de `c.png`. A tartaruga percorre esses pixels, interpreta cada trinca
como uma instrução (opcode + 2 operandos), e executa.

**Objetivo:** descobrir qual sequência de 35 caracteres faz o
programa imprimir `"correct flag!"` em vez de `"wrong flag :C"`.

---

## 2. A arquitetura (ISA) — visão geral

### 2.1 — As 4 "tartarugas" (a arquitetura da máquina)

| Tartaruga | Papel |
|---|---|
| **C** (`cTurt`) | Percorre `c.png`; é o ponteiro de instrução (like um "PC" de CPU) |
| **M** (`mTurt`) | Memória principal, carregada de `m.png`; a flag testada é sobrescrita nos primeiros 35 endereços |
| **S** (`sTurt`) | Pilha, **separada** da memória principal |
| **R** (`rTurt`) | 9 registradores de uso geral, numa grade 3×3 |

### 2.2 — Como uma instrução é codificada

Cada instrução ocupa **3 pixels em sequência, na mesma linha** de
`c.png`. O primeiro pixel, **mascarado** (`&0xfc` em cada canal),
identifica o opcode; os 2 bits menos significativos de cada canal
são *flags* que dizem como interpretar os outros 2 pixels
(registrador? memória/pilha? constante?).

### 2.3 — A tabela de opcodes: processo de redescoberta

`turt.py` não tem nenhum comentário dizendo "esta cor significa
`mov`" ou "aquela cor significa `add`". A única forma de saber o que
cada cor faz é **ler a função `run()`** e observar, para cada
`elif cmpcolor == (...)`, **o que o código faz de fato** quando
aquela cor aparece — e daí dar um nome (mov, add, cmp, etc.) por
analogia com instruções de assembly que já conhecemos. Esta seção
documenta esse processo, para deixar claro que a tabela abaixo
**não foi copiada de nenhuma fonte externa** — foi redescoberta
lendo o próprio código-fonte do desafio, e só depois comparada com
um write-up público como conferência (Seção 11).

**Passo 1 — isolar a estrutura de decisão.** A função `run()` tem
este formato:

```python
color0 = getColor(cTurt)
cmpcolor = (color0[0]&0xfc, color0[1]&0xfc, color0[2]&0xfc)
...
if cmpcolor == (0,252,0):
    ...
elif cmpcolor == (252,0,0):
    ...
```

A **cor mascarada** (`cmpcolor`) do primeiro pixel de cada instrução
é o "opcode"; o resto é um `if/elif` comparando essa cor contra
valores fixos. A máscara `& 0xfc` zera os 2 bits menos significativos
de cada canal — separando a cor em "opcode" (bits altos) e "flags de
operando" (os 2 bits baixos de cada canal, usados no Passo 3).

**Passo 2 — nomear cada operação pelo comportamento.** Para cada
bloco `elif`, lemos o que o código **faz**, e escolhemos um nome:

| Cor mascarada | O que o código faz (evidência) | Nome escolhido |
|---|---|---|
| `(0, 252, 0)` | `return "correct"` (adaptado; original: `print("correct flag!"); exit(0)`) | **success** |
| `(252, 0, 0)` | `return "wrong"` (original: `print("wrong flag :C"); exit(0)`) | **fail** |
| `(204, 204, 252)` | `sTurt.forward(readC(color1)*5)` — move o ponteiro da pilha | **sp_adjust** |
| `(220, 252, 0)` | escreve `val2` direto no destino, sem operação matemática | **mov** |
| `(252, 188, 0)` | escreve o **endereço calculado** (`readPA`), não o valor lido | **lea** |
| `(64, 224, 208)` | `write(color1, val1 + val2, ...)` | **add** |
| `(156, 224, 188)` | `write(color1, val1 - val2, ...)` | **sub** |
| `(100, 148, 236)` | `write(color1, val1 >> val2, ...)` | **shr** |
| `(252, 124, 80)` | grava 3 resultados de comparação (igual/menor/maior) em registradores | **cmp** |
| `(220, 48, 96)` | move o ponteiro de código condicionalmente, conforme flags/registradores | **jcc** (salto condicional) |
| `(252, 0, 252)` | guarda posição na pilha + salta para outra posição do código | **call** |
| `(128, 0, 128)` | recupera posição da pilha + volta o ponteiro de código | **ret** |

Cada linha tem uma evidência concreta no código-fonte — não é
suposição. Por exemplo, sabemos que `(252, 188, 0)` é `lea` e não
`mov` porque, olhando a diferença:

```python
if cmpcolor == (252, 188, 0):
    val2 = readPA(color2, isC2)      # <- calcula um ENDEREÇO
else:
    val2 = read(color2, isR2, isP2, isC2)   # <- lê um VALOR
```

Isso é exatamente a diferença entre `mov` e `lea` em assembly real:
`mov` lê o *conteúdo* de um endereço; `lea` usa o *próprio endereço*
como valor.

**Passo 3 — decodificar as flags dos operandos.** Os 2 bits menos
significativos de cada canal de `color0` (descartados do opcode pela
máscara) reaparecem assim:

```python
isR1 = color0[0]&1 != 0
isP1 = color0[1]&1 != 0
isC1 = color0[2]&1 != 0
isR2 = color0[0]&2 != 0
isP2 = color0[1]&2 != 0
isC2 = color0[2]&2 != 0
```

Bit 0 de cada canal descreve o **primeiro operando** (registrador?
memória/pilha? constante?); bit 1 descreve o **segundo operando**.
Isso foi descoberto seguindo onde essas 6 variáveis são usadas mais
adiante.

**Passo 4 — o caso mais sutil: o salto condicional.** A cor
`(220, 48, 96)` reaproveita os mesmos 4 bits (canais R e G de
`color0`) para codificar **quais condições** disparam o salto:

```python
e = readRVal(6)   # "igual" (resultado do último cmp)
l = readRVal(7)   # "menor"
g = readRVal(8)   # "maior"
if (color0[0]&1 != 0 and e) or (color0[1]&1 != 0 and not e) or (color0[0]&2 != 0 and l) or (color0[1]&2 != 0 and g):
    ...salta...
```

R&1 liga "salta se igual", G&1 liga "salta se diferente", R&2 liga
"salta se menor", G&2 liga "salta se maior". Se **todos os 4 bits**
estiverem ligados ao mesmo tempo, alguma condição é sempre
verdadeira — vira um salto **incondicional** (`jmp`). Isso não está
escrito em lugar nenhum como "jmp" — é uma consequência lógica de
combinar as 4 condições, percebida simulando alguns casos na mão.

**A tabela final** (usada em `solver/turt_headless.py`):

| Cor mascarada | Operação |
|---|---|
| `(0, 252, 0)` | success (flag correta) |
| `(252, 0, 0)` | fail (flag errada) |
| `(204, 204, 252)` | ajuste do ponteiro de pilha |
| `(220, 252, 0)` | mov |
| `(252, 188, 0)` | lea |
| `(64, 224, 208)` | add |
| `(156, 224, 188)` | sub |
| `(100, 148, 236)` | shr |
| `(252, 124, 80)` | cmp |
| `(220, 48, 96)` | salto condicional (jcc) |
| `(252, 0, 252)` | call |
| `(128, 0, 128)` | ret |

### 2.4 — A lógica de negócio (o crackme em si)

Confirmado ao rodar o programa (Seção 6): a flag precisa ter
**exatamente 35 caracteres**. A lógica embutida em `c.png` verifica,
nessa ordem:

1. Um cabeçalho fixo (`CTF{` no início, `}` no fim).
2. Que os 30 caracteres internos são todos **únicos**.
3. Para cada caractere possível do intervalo ASCII `'+'` (43) até
   `'z'` (122), roda uma **busca binária recursiva** contra os
   caracteres da flag, comparando o resultado de cada passo (menor,
   maior, igual) com um valor **fixo, gravado em `m.png`**.
4. Reordena os caracteres encontrados usando um array de permutação,
   também gravado em `m.png`.

---

## 3. Teoria necessária

- **Codificação de instruções em pixels** — a ideia de usar bits de
  uma cor para multiplexar informação (opcode + flags de operando)
  é uma técnica clássica de compressão de formato de instrução,
  parecida com como processadores reais codificam registradores e
  modos de endereçamento nos bits de uma instrução.
- **Busca binária** — algoritmo clássico; aqui, invertido: em vez de
  buscar um valor num array ordenado, usamos os **resultados
  gravados** de buscas binárias (para candidatos de 43 a 122) como
  "testemunhas" de quais caracteres pertencem à flag.
- **Permutações** — o array de reordenação é uma bijeção de 30
  posições; a mesma ideia matemática de uma "chave de reordenação",
  sem qualquer criptografia envolvida.

---

## 4. Ambiente, dependências e a decisão de reprodutibilidade mais importante

**Não usamos Tkinter, nem Xvfb, nem qualquer ambiente gráfico.**

A execução original de `turt.py` depende da biblioteca `turtle`
(construída sobre Tkinter), que por sua vez precisa de um display
gráfico — em servidores sem tela, isso normalmente exige o `Xvfb`
(*X Virtual Framebuffer*, um "monitor falso"). Isso é uma fonte real
de atrito na reprodução (a planilha do desafio já avisa: "o tempo de
execução não foi medido").

**Nossa solução:** como `c.png` e `m.png` já contêm toda a
informação (código e memória), escrevemos um **shim headless** —
`solver/headless_turtle.py` — que substitui só a camada gráfica por
um dicionário Python simples, guardando "que cor foi pintada em cada
posição". Rodamos o `turt.py` **original, sem alterar nenhuma linha
de lógica de negócio**, só trocando essa camada.

**Dependências:**
- Python 3
- `Pillow` (`pip install -r solver/requirements.txt`) — única
  dependência externa, usada só para ler os pixels de `c.png`/`m.png`.

---

## 5. Estrutura do repositório

```
turtle-writeup/
├── README.md
├── .gitignore
├── challenge/                    # arquivos ORIGINAIS do desafio (nao alterados)
│   ├── turt.py
│   ├── c.png
│   └── m.png
└── solver/                       # nosso codigo
    ├── headless_turtle.py        # shim headless (substitui so o Tkinter)
    ├── turt_headless.py          # copia fiel de turt.py, rodando sem GUI
    ├── resolve_turtle.py         # script principal: extrai, reconstroi e valida
    └── requirements.txt          # Pillow
```

---

## 6. Origem dos artefatos e adaptações do grupo

- **`turt.py`, `c.png`, `m.png`**: baixados do repositório oficial
  do desafio (ver Seção 8, Referências) — **não foram alterados em
  nenhum byte**.
- **`headless_turtle.py`**: escrito do zero pelo grupo — nenhuma
  linha vem de nenhuma fonte externa.
- **`turt_headless.py`**: **cópia fiel** de `turt.py`, com exatamente
  3 adaptações documentadas no topo do próprio arquivo — troca do
  import gráfico, reescrita da função `getColor()`, e o bloco final
  transformado em função reutilizável. Todo o resto (cada linha de
  `loadM`, `readM`, `writeM`, `loadS`, `readS`, `writeS`, `loadR`,
  `readR`, `writeR`, `loadC`, `drawImg`, `read`, `write`, `readC`,
  `cToColor`, `run`, etc.) é idêntico ao original.
- **`resolve_turtle.py`**: escrito do zero — a lógica de extração e
  reconstrução da flag foi desenvolvida de forma independente pelo
  grupo (ver Seção 7 sobre a conferência com o write-up público).

---

## 7. Como rodar (instruções de ponta a ponta)

### Linux / macOS

```bash
cd solver
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 resolve_turtle.py
```

### Windows (PowerShell)

```powershell
cd solver
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python resolve_turtle.py
```

> `resolve_turtle.py` copia `c.png` e `m.png` de `../challenge/`
> automaticamente na primeira execução (ver comentário no topo do
> arquivo) — não é necessário copiar nada manualmente.

### Saída esperada

```
======================================================================
PASSO 1 — Carregando a memória (m.png) com um placeholder
======================================================================
Memória carregada. Placeholder de 35 caracteres em uso.

======================================================================
PASSO 2 — Extraindo os dois arrays gravados na memória
======================================================================
Array de reordenação (30 posições):
  [23, 14, 7, 18, 12, 1, 28, 15, 26, 0, 5, 21, 27, 3, 11, 24, 13, 2, 8, 22, 6, 10, 29, 19, 17, 9, 20, 4, 16, 25]
  É permutação válida de 0..29? True
Array de resultados da busca (424 entradas brutas).

======================================================================
PASSO 3 — Reconstruindo a flag
======================================================================
Flag reconstruída: CTF{iT5_E-tUr+1es/AlL.7h3;waY:d0Wn}
Tamanho: 35 (esperado: 35)

======================================================================
PASSO 4 — Validação final: rodando a VM completa, do zero
======================================================================
Resultado da execução completa: correct
Tempo: 0.15s

[SUCESSO] A flag reconstruída foi ACEITA pelo programa original,
rodando de ponta a ponta.
```

---

## 8. Explicação das etapas do código

### `headless_turtle.py`

Reimplementa só o subconjunto da API de `turtle.Turtle()` que o
desafio usa (`forward`, `back`, `left`, `right`, `penup`, `pendown`,
`pencolor`, `pos`, `speed`, `pensize`). Internamente, guarda um
dicionário `CANVAS` mapeando posições `(x, y)` para cores — a
"tela" inteira vira uma estrutura de dados comum, sem nenhuma
dependência gráfica. Comentários extensos em cada método explicam a
tradução exata de "andar/girar" em aritmética de coordenadas.

### `turt_headless.py`

Cópia do desafio original, com as 3 adaptações documentadas no topo
do próprio arquivo. A função `run()` — o "loop principal da CPU" —
tem comentários explicando cada opcode, remetendo à tabela
documentada em `docs/redescoberta-opcodes.md`.

### `resolve_turtle.py`

Script principal, dividido em 4 passos (ver comentário no topo do
arquivo e Seção 7 acima): carrega a memória com uma flag placeholder,
extrai os dois arrays relevantes (reordenação + resultados de busca),
reconstrói a flag combinando os dois, e **valida rodando a VM
completa** com a flag reconstruída — não se contenta em só extrair
constantes estaticamente.

---

## 9. Evidência de reprodução

Executado com sucesso, do zero, conforme a saída completa mostrada
na Seção 7. Os pontos-chave de evidência:

- **O array de reordenação é uma permutação válida** de 0 a 29
  (conferido programaticamente: `sorted(array) == list(range(30))`).
- **A flag reconstruída tem exatamente 35 caracteres**, como exigido
  pelo programa original.
- **A validação final roda a VM inteira, instrução por instrução**,
  e confirma `"correct"` — não é uma inferência estática apenas; é
  a prova de que o programa original, rodando de ponta a ponta,
  aceita essa flag.

---

## 10. Contribuições próprias do grupo

- **Emulador headless completo**, mantendo a lógica original
  **100% intacta** — uma alternativa mais rigorosa a só descrever a
  tabela de opcodes: provamos que o programa reconstruído se
  comporta identicamente ao original, porque **é o mesmo código**,
  rodando sem GUI.
- **Redescoberta documentada da tabela de opcodes** (Seção 2.3) —
  processo registrado com evidência linha a linha do código-fonte
  para cada entrada da tabela, não apenas o resultado final.
- **Validação de ponta a ponta via execução completa da VM** — em
  vez de só extrair arrays estaticamente (o suficiente para
  "adivinhar" a flag), rodamos o programa original inteiro com a
  flag reconstruída, obtendo a confirmação `"correct"` do próprio
  programa.
- **Zero dependência de ambiente gráfico** — eliminando por completo
  a necessidade de Tkinter/Xvfb mencionada como fonte de incerteza
  nos materiais do desafio.
- **Código extensamente comentado**, pensado para que qualquer
  pessoa do grupo consiga apresentar a solução mesmo sem ter escrito
  o código originalmente.

---

## 11. Referências

- Código-fonte e descrição oficial do desafio: repositório
  [`google/google-ctf`](https://github.com/google/google-ctf),
  `2023/quals/rev-turtle` (commit
  `1655538e8c8b41451d39f670ef15a5af22979ca9`).
- Página do desafio no CTFtime:
  [ctftime.org/task/25686](https://ctftime.org/task/25686).
- Write-up consultado para conferência independente (não usado como
  fonte da nossa implementação): Bo-Shiun Yen (bronson113),
  *"GoogleCTF 2023 Writeup"* — seção Turtle, incluindo o
  desassemblador de referência (`translate.py`) e o solver original
  (`solve.py`). Disponível também via
  [CTFtime](https://ctftime.org/writeup/37339).
- Resultados/soluções do evento: `taskSolutions/rev-turtle.json`,
  Firebase público do Google CTF 2023.
