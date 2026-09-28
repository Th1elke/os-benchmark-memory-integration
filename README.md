# Windows ou Linux? Microbenchmark de Operações de Memória

Scripts do experimento para a disciplina **Programação para Ciência de
Dados** — PBL *"Windows ou Linux? Análise de Desempenho para Integração de
Serviços Digitais em Cidades Inteligentes"*.

## Arquivos

O fluxo segue as três etapas do Encontro 2 (Executar e Coletar → Processar →
Comparar e Decidir):

| Arquivo | Etapa | O que faz |
|---|---|---|
| `microbenchmark.py` | 1. Executar e Coletar | Mede alocação, escrita, leitura e liberação de memória para blocos de 100 a 1.000 MB, 100 repetições cada, e grava os tempos em um CSV. |
| `ambiente_info.py` | 1. Executar e Coletar | Coleta automaticamente os dados da tabela "Identificação dos ambientes" (versão do sistema, arquitetura, versão do Python, memória, vCPUs, VirtualBox) e salva em JSON. É chamado automaticamente pelo `microbenchmark.py`. |
| `validar_csv.py` | 1. Coleta e Validação | Confere um CSV contra os critérios do **Checkpoint 1** (cabeçalho, 1.000 registros, cobertura, identificadores, tempos válidos), ou dois CSVs contra o **Checkpoint 2** (comparáveis entre si). |
| `combinar_csvs.py` | 2. Processamento dos CSVs | Valida (Checkpoint 1) e combina os dois CSVs originais em uma única base com coluna `sistema`, sem alterar os arquivos originais. |
| `analisar_resultados.py` | 3. Comparar e Decidir | Calcula média e desvio padrão por tamanho de bloco e operação, gera a tabela comparativa Windows x Linux e um gráfico por operação. Aceita os dois CSVs separados ou a base já combinada. |
| `requirements.txt` | — | Única dependência opcional: `matplotlib`, para os gráficos. |

## Como rodar

### 1. Rodar o microbenchmark em cada sistema

Em **cada** ambiente (Windows e Linux), na pasta onde estão os scripts:

```bash
python microbenchmark.py
```

Isso executa o protocolo completo (100 a 1.000 MB, passo de 100 MB, 100
repetições por bloco — 1.000 medições no total) e salva:

- `resultados/resultados_<sistema>_<timestamp>.csv` — os tempos medidos;
- `resultados/ambiente_<sistema>_<timestamp>.json` — os dados do ambiente.

**Atenção:** a execução completa pode demorar, especialmente nos blocos
maiores (perto de 1.000 MB), porque a operação de leitura (`sum(bloco)`)
percorre byte a byte. É normal levar de alguns minutos a algumas dezenas
de minutos, dependendo do hardware.

### 2. Testar rapidamente antes da coleta oficial

Para conferir que o script roda sem erros no seu ambiente, sem esperar o
protocolo inteiro:

```bash
python microbenchmark.py --teste-rapido
```

Isso roda só o bloco de 100 MB, com 5 repetições. **Não use esse resultado
na entrega** — é só para validar o ambiente.

Também dá para customizar os parâmetros manualmente, se for útil para
depuração:

```bash
python microbenchmark.py --min 100 --max 200 --passo 100 --repeticoes 10
```

### 3. Validar cada CSV (Checkpoint 1)

Assim que terminar de rodar em **um** dos sistemas, valide o CSV antes de
liberar a execução no outro ambiente (é exatamente o que o protocolo pede
no "Checkpoint 1"):

```bash
python validar_csv.py resultados/resultados_windows_<timestamp>.csv
```

Se aparecer `APROVADO`, pode rodar no segundo sistema. Depois de ter os
dois CSVs, junte-os em uma única pasta (renomeando se quiser deixar mais
claro), e valide os dois juntos (Checkpoint 2):

```
resultados/resultados_windows.csv
resultados/resultados_linux.csv
```

```bash
python validar_csv.py resultados/resultados_windows.csv resultados/resultados_linux.csv
```

### 4. Combinar os CSVs em uma base processada

```bash
python combinar_csvs.py resultados/resultados_windows.csv resultados/resultados_linux.csv
```

Isso valida os dois arquivos de novo e gera
`resultados/dados_combinados.csv` — os dois CSVs originais em uma única
tabela, com uma coluna `sistema` (windows/linux). Os arquivos originais
não são alterados; continuam como evidência bruta da coleta.

### 5. Rodar a análise comparativa

```bash
pip install -r requirements.txt   # só se quiser os gráficos

# opção A: a partir dos dois CSVs originais
python analisar_resultados.py resultados/resultados_windows.csv resultados/resultados_linux.csv

# opção B: a partir da base já combinada
python analisar_resultados.py --combinado resultados/dados_combinados.csv
```

Isso gera, em `resultados/analise/`:

- `resumo_windows.csv` e `resumo_linux.csv` — estatísticas (média, mediana, desvio padrão, mínimo, máximo) por bloco e operação, em cada sistema;
- `comparacao.csv` — média e desvio padrão dos dois sistemas lado a lado, diferença absoluta e percentual, e quem foi mais rápido em cada combinação bloco × operação;
- `grafico_alloc_ms.png`, `grafico_write_ms.png`, `grafico_read_ms.png`, `grafico_free_ms.png` — tempo médio por tamanho de bloco, Windows x Linux.

E imprime no terminal um resumo de quantas combinações (bloco × operação)
cada sistema venceu.

## Reprodutibilidade

Antes de cada execução oficial, confira que:

- é o mesmo código (mesmo commit do repositório) nos dois sistemas;
- a mesma versão do Python está instalada nos dois ambientes;
- não há aplicações desnecessárias rodando em segundo plano;
- apenas um ambiente (Windows ou Linux) está ativo por vez, conforme a
  modalidade experimental escolhida no protocolo.
