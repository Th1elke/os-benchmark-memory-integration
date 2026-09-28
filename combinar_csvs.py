"""
Processamento dos CSVs — combina Windows e Linux em uma base comparável.

Disciplina: Programação para Ciência de Dados
PBL: Windows ou Linux? Análise de Desempenho para Integração de Serviços
     Digitais em Cidades Inteligentes

Reproduz os passos do slide "Processamento dos CSVs":
    1) preservar os dois CSVs originais (este script nunca os sobrescreve);
    2) ler os arquivos e converter os tipos;
    3) validar (Checkpoint 1) e combinar os registros em uma base única,
       com uma coluna extra "sistema" (windows/linux);
    4) salvar o resultado em um novo CSV processado.

Uso:
    python combinar_csvs.py resultados/resultados_windows.csv resultados/resultados_linux.csv

Uso com caminho de saída customizado:
    python combinar_csvs.py windows.csv linux.csv --saida resultados/dados_combinados.csv

Por padrão, o script só combina se os dois CSVs passarem no Checkpoint 1
(validar_csv.py). Use --forcar para pular essa checagem (não recomendado).
"""

import argparse
import csv
import os
import sys

from validar_csv import CABECALHO_ESPERADO, validar_csv_unico

CABECALHO_SAIDA = ["sistema"] + CABECALHO_ESPERADO


def ler_e_converter(caminho, sistema):
    """Lê um CSV bruto e retorna uma lista de registros tipados, rotulados com o sistema."""
    registros = []
    with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            registros.append(
                {
                    "sistema": sistema,
                    "bloco_MB": int(linha["bloco_MB"]),
                    "teste": int(linha["teste"]),
                    "alloc_ms": float(linha["alloc_ms"]),
                    "write_ms": float(linha["write_ms"]),
                    "read_ms": float(linha["read_ms"]),
                    "free_ms": float(linha["free_ms"]),
                }
            )
    return registros


def combinar(caminho_win, caminho_lin, caminho_saida, exigir_aprovacao=True):
    if exigir_aprovacao:
        print("Validando os arquivos originais antes de combinar (Checkpoint 1)...\n")
        aprovado_win = all(validar_csv_unico(caminho_win).values())
        aprovado_lin = all(validar_csv_unico(caminho_lin).values())
        if not (aprovado_win and aprovado_lin):
            print(
                "\n[ABORTADO] Um ou ambos os CSVs não passaram no Checkpoint 1. "
                "Corrija a coleta antes de combinar.\n"
                "(Use --forcar para combinar mesmo assim — não recomendado.)"
            )
            return None

    registros_win = ler_e_converter(caminho_win, "windows")
    registros_lin = ler_e_converter(caminho_lin, "linux")
    registros = registros_win + registros_lin

    pasta = os.path.dirname(caminho_saida)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CABECALHO_SAIDA)
        escritor.writeheader()
        for registro in registros:
            escritor.writerow(registro)

    print(
        f"\nBase combinada salva em: {caminho_saida}\n"
        f"  {len(registros_win)} registros do Windows + "
        f"{len(registros_lin)} registros do Linux = {len(registros)} no total"
    )
    print("Os arquivos originais não foram alterados — continuam como evidência bruta da coleta.")
    return caminho_saida


def main():
    parser = argparse.ArgumentParser(
        description="Combina os CSVs originais de Windows e Linux em uma "
                     "única base comparável, após validação (Checkpoint 1)."
    )
    parser.add_argument("csv_windows", help="CSV original de resultados do Windows")
    parser.add_argument("csv_linux", help="CSV original de resultados do Linux")
    parser.add_argument(
        "--saida", default="resultados/dados_combinados.csv",
        help="Caminho do CSV processado de saída "
             "(padrão: resultados/dados_combinados.csv)"
    )
    parser.add_argument(
        "--forcar", action="store_true",
        help="Combina mesmo que a validação (Checkpoint 1) falhe."
    )
    args = parser.parse_args()

    resultado = combinar(
        args.csv_windows, args.csv_linux, args.saida,
        exigir_aprovacao=not args.forcar,
    )
    sys.exit(0 if resultado else 1)


if __name__ == "__main__":
    main()
