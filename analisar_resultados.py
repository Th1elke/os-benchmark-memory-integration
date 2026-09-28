"""
Análise comparativa dos resultados do microbenchmark (Windows vs Linux).

Disciplina: Programação para Ciência de Dados
PBL: Windows ou Linux? Análise de Desempenho para Integração de Serviços
     Digitais em Cidades Inteligentes

Lê os dois arquivos CSV gerados por microbenchmark.py (um por sistema
operacional), calcula estatísticas descritivas por tamanho de bloco e por
operação (alocação, escrita, leitura, liberação), grava tabelas-resumo em
CSV e, se o matplotlib estiver disponível, gera gráficos comparativos.

Uso:
    python analisar_resultados.py resultados/resultados_windows_XXXX.csv \
                                   resultados/resultados_linux_XXXX.csv

Uso com pasta de saída customizada:
    python analisar_resultados.py windows.csv linux.csv --saida resultados/analise
"""

import argparse
import csv
import os
import statistics
from collections import defaultdict

OPERACOES = ["alloc_ms", "write_ms", "read_ms", "free_ms"]

NOMES_OPERACOES = {
    "alloc_ms": "Alocação",
    "write_ms": "Escrita",
    "read_ms": "Leitura",
    "free_ms": "Liberação",
}


def ler_resultados(caminho):
    """Lê um CSV de resultados do microbenchmark e retorna uma lista de dicts."""
    linhas = []
    with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            registro = {
                "bloco_MB": int(linha["bloco_MB"]),
                "teste": int(linha["teste"]),
            }
            for operacao in OPERACOES:
                registro[operacao] = float(linha[operacao])
            linhas.append(registro)
    return linhas


def ler_combinado(caminho):
    """
    Lê um CSV já combinado (com coluna 'sistema', gerado por combinar_csvs.py)
    e devolve duas listas de registros: (linhas_windows, linhas_linux).
    """
    linhas_windows, linhas_linux = [], []
    with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            registro = {
                "bloco_MB": int(linha["bloco_MB"]),
                "teste": int(linha["teste"]),
            }
            for operacao in OPERACOES:
                registro[operacao] = float(linha[operacao])

            sistema = linha["sistema"].strip().lower()
            if sistema == "windows":
                linhas_windows.append(registro)
            elif sistema == "linux":
                linhas_linux.append(registro)
    return linhas_windows, linhas_linux


def agrupar_por_bloco(linhas):
    """Agrupa os registros por tamanho de bloco (MB)."""
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[linha["bloco_MB"]].append(linha)
    return dict(sorted(grupos.items()))


def estatisticas(valores):
    return {
        "media": statistics.mean(valores),
        "mediana": statistics.median(valores),
        "desvio_padrao": statistics.stdev(valores) if len(valores) > 1 else 0.0,
        "minimo": min(valores),
        "maximo": max(valores),
    }


def resumir(linhas):
    """Gera um resumo estatístico por tamanho de bloco e por operação."""
    grupos = agrupar_por_bloco(linhas)
    resumo = {}
    for bloco_mb, registros in grupos.items():
        resumo[bloco_mb] = {}
        for operacao in OPERACOES:
            valores = [registro[operacao] for registro in registros]
            resumo[bloco_mb][operacao] = estatisticas(valores)
    return resumo


def salvar_resumo_csv(resumo, sistema, caminho):
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            ["sistema", "bloco_MB", "operacao", "media_ms", "mediana_ms",
             "desvio_padrao_ms", "minimo_ms", "maximo_ms"]
        )
        for bloco_mb, operacoes in resumo.items():
            for operacao, stats in operacoes.items():
                escritor.writerow(
                    [
                        sistema,
                        bloco_mb,
                        operacao,
                        f"{stats['media']:.6f}",
                        f"{stats['mediana']:.6f}",
                        f"{stats['desvio_padrao']:.6f}",
                        f"{stats['minimo']:.6f}",
                        f"{stats['maximo']:.6f}",
                    ]
                )


def comparar(resumo_windows, resumo_linux):
    """
    Compara média e desvio padrão de cada operação, bloco a bloco, entre os
    dois sistemas -- é a tabela "Windows e Linux para cada operação e
    tamanho" pedida no protocolo.
    """
    comparacao = []
    blocos_comuns = sorted(set(resumo_windows) & set(resumo_linux))
    for bloco_mb in blocos_comuns:
        for operacao in OPERACOES:
            stats_win = resumo_windows[bloco_mb][operacao]
            stats_lin = resumo_linux[bloco_mb][operacao]
            media_win = stats_win["media"]
            media_lin = stats_lin["media"]
            mais_rapido = "Windows" if media_win < media_lin else "Linux"
            maior = max(media_win, media_lin)
            diferenca_ms = abs(media_win - media_lin)
            diferenca_pct = diferenca_ms / maior * 100 if maior else 0.0
            comparacao.append(
                {
                    "bloco_MB": bloco_mb,
                    "operacao": operacao,
                    "media_windows_ms": media_win,
                    "desvio_padrao_windows_ms": stats_win["desvio_padrao"],
                    "media_linux_ms": media_lin,
                    "desvio_padrao_linux_ms": stats_lin["desvio_padrao"],
                    "diferenca_ms": diferenca_ms,
                    "diferenca_pct": diferenca_pct,
                    "mais_rapido": mais_rapido,
                }
            )
    return comparacao


def salvar_comparacao_csv(comparacao, caminho):
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            ["bloco_MB", "operacao",
             "media_windows_ms", "desvio_padrao_windows_ms",
             "media_linux_ms", "desvio_padrao_linux_ms",
             "diferenca_ms", "diferenca_pct", "mais_rapido"]
        )
        for linha in comparacao:
            escritor.writerow(
                [
                    linha["bloco_MB"],
                    linha["operacao"],
                    f"{linha['media_windows_ms']:.6f}",
                    f"{linha['desvio_padrao_windows_ms']:.6f}",
                    f"{linha['media_linux_ms']:.6f}",
                    f"{linha['desvio_padrao_linux_ms']:.6f}",
                    f"{linha['diferenca_ms']:.6f}",
                    f"{linha['diferenca_pct']:.2f}",
                    linha["mais_rapido"],
                ]
            )


def contar_vitorias(comparacao):
    """Conta, entre todas as combinações bloco x operação, quem venceu mais vezes."""
    vitorias = {"Windows": 0, "Linux": 0}
    for linha in comparacao:
        vitorias[linha["mais_rapido"]] += 1
    return vitorias


def gerar_graficos(resumo_windows, resumo_linux, pasta_saida):
    """Gera gráficos comparativos (requer matplotlib)."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # não exige ambiente gráfico
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib não está instalado — gráficos não foram gerados.")
        print("Instale com: pip install matplotlib")
        return

    os.makedirs(pasta_saida, exist_ok=True)
    blocos = sorted(set(resumo_windows) & set(resumo_linux))

    for operacao in OPERACOES:
        medias_win = [resumo_windows[bloco][operacao]["media"] for bloco in blocos]
        medias_lin = [resumo_linux[bloco][operacao]["media"] for bloco in blocos]

        plt.figure(figsize=(8, 5))
        plt.plot(blocos, medias_win, marker="o", label="Windows")
        plt.plot(blocos, medias_lin, marker="o", label="Linux")
        plt.xlabel("Tamanho do bloco (MB)")
        plt.ylabel("Tempo médio (ms)")
        plt.title(f"Tempo médio de {NOMES_OPERACOES[operacao]} por tamanho de bloco")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        caminho_figura = os.path.join(pasta_saida, f"grafico_{operacao}.png")
        plt.savefig(caminho_figura, dpi=150)
        plt.close()
        print(f"Gráfico salvo: {caminho_figura}")


def main():
    parser = argparse.ArgumentParser(
        description="Compara os resultados do microbenchmark entre Windows e Linux."
    )
    parser.add_argument(
        "csv_windows", nargs="?", default=None,
        help="Caminho do CSV de resultados do Windows (omitir se usar --combinado)"
    )
    parser.add_argument(
        "csv_linux", nargs="?", default=None,
        help="Caminho do CSV de resultados do Linux (omitir se usar --combinado)"
    )
    parser.add_argument(
        "--combinado", default=None,
        help="Em vez dos dois CSVs separados, usa um único CSV já combinado "
             "(gerado por combinar_csvs.py, com coluna 'sistema')."
    )
    parser.add_argument(
        "--saida", default="resultados/analise",
        help="Pasta onde os arquivos de análise serão salvos "
             "(padrão: resultados/analise)"
    )
    args = parser.parse_args()

    os.makedirs(args.saida, exist_ok=True)

    if args.combinado:
        linhas_windows, linhas_linux = ler_combinado(args.combinado)
    elif args.csv_windows and args.csv_linux:
        linhas_windows = ler_resultados(args.csv_windows)
        linhas_linux = ler_resultados(args.csv_linux)
    else:
        parser.error(
            "informe csv_windows e csv_linux, ou use --combinado <arquivo>."
        )

    resumo_windows = resumir(linhas_windows)
    resumo_linux = resumir(linhas_linux)

    salvar_resumo_csv(
        resumo_windows, "windows", os.path.join(args.saida, "resumo_windows.csv")
    )
    salvar_resumo_csv(
        resumo_linux, "linux", os.path.join(args.saida, "resumo_linux.csv")
    )

    comparacao = comparar(resumo_windows, resumo_linux)
    salvar_comparacao_csv(comparacao, os.path.join(args.saida, "comparacao.csv"))

    vitorias = contar_vitorias(comparacao)
    total_combinacoes = sum(vitorias.values())
    print(
        "\nResumo geral (combinações bloco x operação em que cada sistema "
        "foi mais rápido):"
    )
    for sistema, contagem in vitorias.items():
        pct = (contagem / total_combinacoes * 100) if total_combinacoes else 0.0
        print(f"  {sistema}: {contagem}/{total_combinacoes} ({pct:.1f}%)")

    gerar_graficos(resumo_windows, resumo_linux, args.saida)

    print(f"\nAnálise concluída. Arquivos salvos em: {args.saida}")
    print(
        "\nLembrete: os arquivos 'resumo_windows.csv', 'resumo_linux.csv' e "
        "'comparacao.csv' são a base quantitativa para responder à pergunta "
        "norteadora e para a recomendação final — a interpretação e a "
        "redação das conclusões ainda são do grupo."
    )


if __name__ == "__main__":
    main()
