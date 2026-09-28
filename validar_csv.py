"""
Validação dos arquivos CSV do microbenchmark — Checkpoints 1 e 2.

Disciplina: Programação para Ciência de Dados
PBL: Windows ou Linux? Análise de Desempenho para Integração de Serviços
     Digitais em Cidades Inteligentes

Checkpoint 1 (validação individual, "Coleta e Validação do SO"):
    - cabeçalho com as seis colunas previstas;
    - 1.000 registros;
    - 10 tamanhos de bloco, 100 testes por tamanho;
    - identificadores (bloco_MB, teste) sem ausências ou duplicatas;
    - tempos numéricos, finitos e não negativos.

    Só depois de um CSV aprovado no Checkpoint 1 é que o protocolo libera a
    execução no segundo ambiente.

Checkpoint 2 (validação conjunta, "Validação Conjunta"):
    - os dois CSVs (Windows e Linux) aprovados individualmente;
    - mesmo cabeçalho / mesma unidade (comparáveis entre si).

Uso (Checkpoint 1 — validar um único CSV):
    python validar_csv.py resultados/resultados_windows.csv

Uso (Checkpoint 2 — validar os dois juntos, antes de seguir para a análise):
    python validar_csv.py resultados/resultados_windows.csv resultados/resultados_linux.csv

Código de saída: 0 se aprovado, 1 se reprovado (útil para encadear comandos).
"""

import argparse
import csv
import math
import os
import sys

CABECALHO_ESPERADO = ["bloco_MB", "teste", "alloc_ms", "write_ms", "read_ms", "free_ms"]
BLOCOS_ESPERADOS = list(range(100, 1001, 100))  # 100, 200, ..., 1000
REPETICOES_ESPERADAS = 100
TOTAL_ESPERADO = len(BLOCOS_ESPERADOS) * REPETICOES_ESPERADAS  # 1000


def ler_csv_bruto(caminho):
    """Lê o CSV como texto (sem conversão), para checar o cabeçalho exato."""
    with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        return list(leitor)


def arquivo_existe(caminho):
    return os.path.isfile(caminho)


def validar_csv_unico(caminho, verboso=True):
    """
    Executa as verificações do Checkpoint 1 para um único CSV.
    Retorna um dicionário {verificacao: bool}.
    """
    resultado = {
        "cabecalho": False,
        "quantidade": False,
        "cobertura": False,
        "identificadores": False,
        "tempos_validos": False,
    }

    if not arquivo_existe(caminho):
        if verboso:
            print(f"[ERRO] Arquivo não encontrado: {caminho}")
        return resultado

    linhas = ler_csv_bruto(caminho)
    if not linhas:
        if verboso:
            print(f"[ERRO] Arquivo vazio: {caminho}")
        return resultado

    cabecalho, registros_brutos = linhas[0], linhas[1:]
    resultado["cabecalho"] = cabecalho == CABECALHO_ESPERADO
    resultado["quantidade"] = len(registros_brutos) == TOTAL_ESPERADO

    registros = []
    linhas_invalidas = 0
    for linha in registros_brutos:
        if len(linha) != len(CABECALHO_ESPERADO):
            linhas_invalidas += 1
            continue
        try:
            bloco_mb = int(linha[0])
            teste = int(linha[1])
            tempos = [float(valor) for valor in linha[2:]]
        except ValueError:
            linhas_invalidas += 1
            continue
        registros.append((bloco_mb, teste, tempos))

    # Cobertura e identificadores: para cada tamanho esperado, os "teste"
    # observados devem ser exatamente {1, ..., 100}, sem faltar nem repetir.
    testes_por_bloco = {}
    for bloco_mb, teste, _tempos in registros:
        testes_por_bloco.setdefault(bloco_mb, []).append(teste)

    cobertura_ok = True
    identificadores_ok = True
    for bloco_esperado in BLOCOS_ESPERADOS:
        testes_vistos = testes_por_bloco.get(bloco_esperado, [])
        if len(testes_vistos) != REPETICOES_ESPERADAS:
            cobertura_ok = False
        if set(testes_vistos) != set(range(1, REPETICOES_ESPERADAS + 1)):
            identificadores_ok = False

    resultado["cobertura"] = cobertura_ok and linhas_invalidas == 0
    resultado["identificadores"] = identificadores_ok and linhas_invalidas == 0

    # Tempos numéricos, finitos e não negativos
    tempos_ok = linhas_invalidas == 0
    for _bloco_mb, _teste, tempos in registros:
        for tempo in tempos:
            if math.isnan(tempo) or math.isinf(tempo) or tempo < 0:
                tempos_ok = False
    resultado["tempos_validos"] = tempos_ok

    if verboso:
        print(f"\nValidação de: {caminho}")
        print(f"  Registros lidos: {len(registros_brutos)} "
              f"(linhas com erro de formato: {linhas_invalidas})")
        _imprimir_checklist(resultado)

    return resultado


def _imprimir_checklist(resultado):
    rotulos = {
        "cabecalho": "Cabeçalho (seis colunas previstas)",
        "quantidade": f"Quantidade ({TOTAL_ESPERADO} registros)",
        "cobertura": "Cobertura (10 tamanhos e 100 testes por tamanho)",
        "identificadores": "Identificadores (sem ausências ou duplicatas)",
        "tempos_validos": "Tempos numéricos, finitos e não negativos",
    }
    for chave, rotulo in rotulos.items():
        marca = "[x]" if resultado[chave] else "[ ]"
        print(f"  {marca} {rotulo}")

    aprovado = all(resultado.values())
    print(f"  -> Checkpoint 1: {'APROVADO' if aprovado else 'REPROVADO'}")


def validar_conjunto(caminho_win, caminho_lin):
    """
    Executa o Checkpoint 2: valida os dois CSVs individualmente e verifica
    se são comparáveis entre si (mesmo cabeçalho / mesma unidade de tempo).
    Retorna True se aprovado, False caso contrário.
    """
    print("=" * 62)
    print("VALIDAÇÃO INDIVIDUAL (Checkpoint 1, para cada arquivo)")
    print("=" * 62)
    resultado_win = validar_csv_unico(caminho_win)
    resultado_lin = validar_csv_unico(caminho_lin)

    cabecalho_win = ler_csv_bruto(caminho_win)[0] if arquivo_existe(caminho_win) else None
    cabecalho_lin = ler_csv_bruto(caminho_lin)[0] if arquivo_existe(caminho_lin) else None
    mesmo_esquema = (
        cabecalho_win is not None
        and cabecalho_win == cabecalho_lin == CABECALHO_ESPERADO
    )

    print("\n" + "=" * 62)
    print("VALIDAÇÃO CONJUNTA (Checkpoint 2)")
    print("=" * 62)

    criterios = {
        "Cabeçalho correto": (resultado_win["cabecalho"], resultado_lin["cabecalho"]),
        "1.000 registros": (resultado_win["quantidade"], resultado_lin["quantidade"]),
        "10 tamanhos e 100 testes": (resultado_win["cobertura"], resultado_lin["cobertura"]),
        "Tempos válidos": (resultado_win["tempos_validos"], resultado_lin["tempos_validos"]),
    }

    print(f"  {'Critério':<28}{'Windows':>10}{'Linux':>10}{'Comparável':>14}")
    tudo_ok = mesmo_esquema
    for criterio, (ok_win, ok_lin) in criterios.items():
        comparavel = ok_win and ok_lin
        tudo_ok = tudo_ok and comparavel
        print(
            f"  {criterio:<28}"
            f"{'[x]' if ok_win else '[ ]':>10}"
            f"{'[x]' if ok_lin else '[ ]':>10}"
            f"{'[x]' if comparavel else '[ ]':>14}"
        )
    print(
        f"  {'Mesmo esquema e unidade':<28}{'':>10}{'':>10}"
        f"{'[x]' if mesmo_esquema else '[ ]':>14}"
    )

    print(f"\n  -> Checkpoint 2: {'APROVADO' if tudo_ok else 'REPROVADO'}")
    return tudo_ok


def main():
    parser = argparse.ArgumentParser(
        description="Valida o(s) CSV(s) do microbenchmark (Checkpoints 1 e 2)."
    )
    parser.add_argument("csv_a", help="CSV a validar (ex: resultados de um dos sistemas)")
    parser.add_argument(
        "csv_b", nargs="?", default=None,
        help="CSV do segundo sistema (opcional). Se informado, roda a "
             "validação conjunta (Checkpoint 2)."
    )
    args = parser.parse_args()

    if args.csv_b is None:
        resultado = validar_csv_unico(args.csv_a)
        sys.exit(0 if all(resultado.values()) else 1)
    else:
        aprovado = validar_conjunto(args.csv_a, args.csv_b)
        sys.exit(0 if aprovado else 1)


if __name__ == "__main__":
    main()
