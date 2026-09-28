"""
Coleta de informações de identificação do ambiente de execução.

Disciplina: Programação para Ciência de Dados
PBL: Windows ou Linux? Análise de Desempenho para Integração de Serviços
     Digitais em Cidades Inteligentes

Este script preenche automaticamente os campos da tabela "Identificação dos
ambientes" do protocolo experimental:

    - Versão do sistema
    - Arquitetura
    - Versão do Python
    - Memória disponível (equivale à RAM atribuída, quando roda em VM)
    - Quantidade de vCPUs (se VM)
    - Versão do VirtualBox Guest Additions (se VM)

Uso:
    python ambiente_info.py
"""

import json
import os
import platform
import subprocess


def _memoria_windows_bytes():
    """Lê a memória física total do host no Windows via API do Windows."""
    import ctypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    mem_status = MEMORYSTATUSEX()
    mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
    return mem_status.ullTotalPhys


def _memoria_linux_bytes():
    """Lê a memória física total do host no Linux via /proc/meminfo."""
    with open("/proc/meminfo", "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            if linha.startswith("MemTotal:"):
                partes = linha.split()
                kb = int(partes[1])
                return kb * 1024
    return None


def memoria_total_gb():
    """Retorna a memória RAM total visível pelo sistema, em GB (aprox.)."""
    sistema = platform.system()
    try:
        if sistema == "Windows":
            total_bytes = _memoria_windows_bytes()
        elif sistema == "Linux":
            total_bytes = _memoria_linux_bytes()
        else:
            return None
        if total_bytes is None:
            return None
        return round(total_bytes / (1024 ** 3), 2)
    except Exception:
        # Qualquer falha na leitura não deve interromper a coleta dos
        # demais dados do ambiente.
        return None


def versao_virtualbox():
    """
    Tenta identificar a versão do VirtualBox Guest Additions instalada.
    Se encontrada, é um forte indício de que o sistema está rodando em VM.
    Retorna None quando não for possível identificar (ex: execução bare metal).
    """
    try:
        if platform.system() == "Windows":
            saida = subprocess.run(
                [
                    "reg", "query",
                    r"HKLM\SOFTWARE\Oracle\VirtualBox Guest Additions",
                    "/v", "Version",
                ],
                capture_output=True, text=True, timeout=5,
            )
            if saida.returncode == 0:
                for linha in saida.stdout.splitlines():
                    if "Version" in linha:
                        return linha.strip().split()[-1]
        else:
            saida = subprocess.run(
                ["VBoxControl", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if saida.returncode == 0:
                return saida.stdout.strip()
    except Exception:
        pass
    return None


def coletar_informacoes():
    """Monta um dicionário com os campos da tabela 'Identificação dos ambientes'."""
    info = {
        "versao_do_sistema": f"{platform.system()} {platform.release()} "
                              f"({platform.version()})",
        "arquitetura": platform.machine(),
        "versao_do_python": platform.python_version(),
        "memoria_disponivel_gb": memoria_total_gb(),
        "quantidade_de_vcpus": os.cpu_count(),
        "versao_do_virtualbox_guest_additions": versao_virtualbox(),
        "hostname": platform.node(),
    }
    return info


def salvar_informacoes(caminho="resultados/ambiente_info.json"):
    """Coleta e grava as informações do ambiente em um arquivo JSON."""
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    info = coletar_informacoes()
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(info, arquivo, indent=2, ensure_ascii=False)
    return info, caminho


if __name__ == "__main__":
    info, caminho = salvar_informacoes()

    print("Informações do ambiente coletadas:\n")
    for chave, valor in info.items():
        print(f"  {chave}: {valor}")

    print(f"\nSalvo em: {caminho}")
    print(
        "\nObservação: 'memoria_disponivel_gb' e 'quantidade_de_vcpus' "
        "correspondem ao que o SO enxerga. Se estiver em VM, esses valores "
        "equivalem ao que foi atribuído na configuração da máquina virtual."
    )
