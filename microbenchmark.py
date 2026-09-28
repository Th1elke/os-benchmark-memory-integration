"""
Microbenchmark de operações de memória (alocação, escrita, leitura, liberação)

Disciplina: Programação para Ciência de Dados
PBL: Windows ou Linux? Análise de Desempenho para Integração de Serviços
     Digitais em Cidades Inteligentes

Reproduz, em Python puro (biblioteca padrão), as quatro operações de memória
realizadas por um processo de integração:

    1) Alocação  -> bloco = bytearray(bloco_bytes)
    2) Escrita   -> bloco[:] = padrao
    3) Leitura   -> soma = sum(bloco)
    4) Liberação -> bloco.clear(); del bloco

Protocolo experimental (definido em aula, "Restrições do Experimento"):
    - blocos de 100 a 1.000 MB, em intervalos de 100 MB;
    - 100 repetições por tamanho de bloco;
    - tempos medidos em milissegundos com time.perf_counter_ns();
    - resultados persistidos em CSV com o cabeçalho:
          bloco_MB,teste,alloc_ms,write_ms,read_ms,free_ms

Uso (execução completa, conforme o protocolo):
    python microbenchmark.py

Uso (execução rápida, só para validar que o script funciona):
    python microbenchmark.py --teste-rapido

Uso (parâmetros customizados, ex: só o bloco de 100 MB, 5 repetições):
    python microbenchmark.py --min 100 --max 100 --passo 100 --repeticoes 5
"""

import argparse
import csv
import os
import time
from datetime import datetime

try:
    import ambiente_info
except ImportError:
    ambiente_info = None


# ----------------------------------------------------------------------
# Parâmetros padrão do protocolo experimental (fixados previamente pelo
# enunciado da aula). Podem ser sobrescritos via linha de comando apenas
# para testes rápidos -- a coleta final deve usar os valores do protocolo.
# ----------------------------------------------------------------------
BLOCO_MIN_MB_PADRAO = 100
BLOCO_MAX_MB_PADRAO = 1000
BLOCO_PASSO_MB_PADRAO = 100
REPETICOES_PADRAO = 100

PADRAO_BYTE = 0xAA  # valor usado para "escrever" no bloco
PASTA_SAIDA_PADRAO = "resultados"


def identificar_sistema():
    """Retorna um rótulo curto do sistema operacional (windows/linux/outro)."""
    import platform

    sistema = platform.system().lower()
    if sistema.startswith("win"):
        return "windows"
    if sistema.startswith("linux"):
        return "linux"
    return sistema or "desconhecido"


def medir_bloco(bloco_bytes, padrao):
    """
    Executa as quatro operações de memória para um bloco de 'bloco_bytes'
    bytes e retorna os tempos decorridos em milissegundos.

    'padrao' já deve estar pronto (preparado fora da medição), com o mesmo
    tamanho de 'bloco_bytes'.
    """
    # 1) Alocação
    t0 = time.perf_counter_ns()
    bloco = bytearray(bloco_bytes)
    t1 = time.perf_counter_ns()
    alloc_ms = (t1 - t0) / 1_000_000

    # 2) Escrita
    t2 = time.perf_counter_ns()
    bloco[:] = padrao
    t3 = time.perf_counter_ns()
    write_ms = (t3 - t2) / 1_000_000

    # 3) Leitura
    t4 = time.perf_counter_ns()
    soma = sum(bloco)
    t5 = time.perf_counter_ns()
    read_ms = (t5 - t4) / 1_000_000

    # 4) Liberação
    t6 = time.perf_counter_ns()
    bloco.clear()
    del bloco
    t7 = time.perf_counter_ns()
    free_ms = (t7 - t6) / 1_000_000

    # 'soma' só existe para que a leitura percorra o bloco de verdade;
    # não faz parte do resultado.
    del soma

    return alloc_ms, write_ms, read_ms, free_ms


def executar_experimento(bloco_min_mb, bloco_max_mb, bloco_passo_mb,
                          repeticoes, pasta_saida):
    sistema = identificar_sistema()
    os.makedirs(pasta_saida, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_csv = os.path.join(
        pasta_saida, f"resultados_{sistema}_{timestamp}.csv"
    )

    tamanhos_mb = list(range(bloco_min_mb, bloco_max_mb + 1, bloco_passo_mb))
    total_execucoes = len(tamanhos_mb) * repeticoes
    contagem = 0

    print(f"Sistema identificado : {sistema}")
    print(f"Tamanhos de bloco (MB): {tamanhos_mb}")
    print(f"Repetições por bloco  : {repeticoes}")
    print(f"Total de execuções    : {total_execucoes}")
    print(f"Arquivo de saída      : {caminho_csv}\n")

    # Registra também as informações do ambiente, se o módulo estiver
    # disponível na mesma pasta (ambiente_info.py).
    if ambiente_info is not None:
        caminho_info = os.path.join(
            pasta_saida, f"ambiente_{sistema}_{timestamp}.json"
        )
        info, _ = ambiente_info.salvar_informacoes(caminho_info)
        print("Ambiente registrado:")
        for chave, valor in info.items():
            print(f"  {chave}: {valor}")
        print()

    inicio_geral = time.perf_counter()

    with open(caminho_csv, "w", encoding="utf-8", newline="") as arquivo_saida:
        escritor = csv.writer(arquivo_saida)
        escritor.writerow(
            ["bloco_MB", "teste", "alloc_ms", "write_ms", "read_ms", "free_ms"]
        )

        for mb in tamanhos_mb:
            bloco_bytes = mb * 1024 * 1024

            # O padrão de escrita é preparado uma única vez por tamanho de
            # bloco, fora da medição -- só o efeito de escrevê-lo no bloco
            # (bloco[:] = padrao) é cronometrado.
            padrao = bytes([PADRAO_BYTE]) * bloco_bytes

            for teste in range(1, repeticoes + 1):
                alloc_ms, write_ms, read_ms, free_ms = medir_bloco(
                    bloco_bytes, padrao
                )

                escritor.writerow(
                    [
                        mb,
                        teste,
                        f"{alloc_ms:.6f}",
                        f"{write_ms:.6f}",
                        f"{read_ms:.6f}",
                        f"{free_ms:.6f}",
                    ]
                )

                contagem += 1
                if teste % 20 == 0 or teste == repeticoes:
                    print(
                        f"  bloco {mb:4d} MB | repetição {teste:3d}/{repeticoes} "
                        f"| progresso geral: {contagem}/{total_execucoes}"
                    )

            del padrao

    duracao_total_s = time.perf_counter() - inicio_geral
    print(f"\nExperimento concluído em {duracao_total_s:.1f} s.")
    print(f"Resultados salvos em: {caminho_csv}")
    return caminho_csv


def main():
    parser = argparse.ArgumentParser(
        description="Microbenchmark de operações de memória (alocação, "
                     "escrita, leitura, liberação)."
    )
    parser.add_argument(
        "--min", type=int, default=BLOCO_MIN_MB_PADRAO,
        help=f"Tamanho mínimo de bloco em MB (padrão: {BLOCO_MIN_MB_PADRAO})"
    )
    parser.add_argument(
        "--max", type=int, default=BLOCO_MAX_MB_PADRAO,
        help=f"Tamanho máximo de bloco em MB (padrão: {BLOCO_MAX_MB_PADRAO})"
    )
    parser.add_argument(
        "--passo", type=int, default=BLOCO_PASSO_MB_PADRAO,
        help=f"Intervalo entre tamanhos de bloco, em MB "
             f"(padrão: {BLOCO_PASSO_MB_PADRAO})"
    )
    parser.add_argument(
        "--repeticoes", type=int, default=REPETICOES_PADRAO,
        help=f"Número de repetições por tamanho de bloco "
             f"(padrão: {REPETICOES_PADRAO})"
    )
    parser.add_argument(
        "--saida", default=PASTA_SAIDA_PADRAO,
        help=f"Pasta onde o CSV de resultados será salvo "
             f"(padrão: {PASTA_SAIDA_PADRAO})"
    )
    parser.add_argument(
        "--teste-rapido", action="store_true",
        help="Executa uma versão reduzida (bloco único de 100 MB, 5 "
             "repetições) apenas para validar que o script funciona. "
             "NÃO deve ser usado para a coleta final."
    )
    args = parser.parse_args()

    if args.teste_rapido:
        print("*** MODO TESTE RÁPIDO — não usar estes resultados na entrega final ***\n")
        bloco_min, bloco_max, passo, repeticoes = 100, 100, 100, 5
    else:
        bloco_min, bloco_max, passo, repeticoes = (
            args.min, args.max, args.passo, args.repeticoes
        )

    executar_experimento(bloco_min, bloco_max, passo, repeticoes, args.saida)


if __name__ == "__main__":
    main()
