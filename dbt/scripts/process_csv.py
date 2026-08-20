#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# process_csv.py — filtro de coluna + reparo/quarentena de linha (spec 019)
#
# Uso: process_csv.py <seed_file> <downloaded_file> <output_file>
#
#   seed_file       seeds/contratos.csv ATUAL — define as colunas conhecidas
#                   (header) e a ordem de saída.
#   downloaded_file CSV baixado do portal nesta execução (TMP_FILE).
#   output_file     CSV filtrado/reparado resultante — NÃO é o seed_file
#                   (ingest.sh decide se/quando promover pra lá).
#
# Variável de ambiente:
#   QUARANTINE_FILE  caminho do arquivo de quarentena cumulativo (default:
#                    /var/log/compras-publicas/contratos_quarentena.csv)
#
# Código de saída: 0 mesmo com quarentena não-vazia (reportada, não é falha).
# Código de saída 1 só se o processamento em si falhar (arquivo ilegível,
# coluna do seed ausente no arquivo baixado, etc.) — nesse caso nada é escrito
# em output_file nem em QUARANTINE_FILE.
# ─────────────────────────────────────────────────────────────────────────────
import csv
import io
import os
import sys

DELIMITER = ";"


class ProcessamentoError(Exception):
    pass


def ler_header(caminho):
    with open(caminho, encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=DELIMITER)
        try:
            return next(reader)
        except StopIteration:
            raise ProcessamentoError(f"{caminho}: arquivo vazio, sem header")


def mapear_colunas(header_seed, header_baixado):
    indice_baixado = {nome.strip().lower(): i for i, nome in enumerate(header_baixado)}
    indices = []
    faltando = []
    for nome in header_seed:
        i = indice_baixado.get(nome.strip().lower())
        if i is None:
            faltando.append(nome)
        else:
            indices.append(i)
    return indices, faltando


def reparar_texto(texto_bruto):
    return texto_bruto.replace('\\"', '""')


def processar(seed_file, downloaded_file):
    header_seed = ler_header(seed_file)
    header_baixado = ler_header(downloaded_file)
    n_esperado = len(header_baixado)

    indices, faltando = mapear_colunas(header_seed, header_baixado)
    if faltando:
        raise ProcessamentoError(
            "colunas do seed atual ausentes no arquivo baixado (deveria ter sido "
            f"barrado pela validação de header antes desta etapa): {faltando}"
        )

    with open(downloaded_file, encoding="utf-8", errors="replace", newline="") as f:
        linhas_fisicas = f.readlines()

    if not linhas_fisicas:
        raise ProcessamentoError(f"{downloaded_file}: arquivo vazio")

    linhas_ok = []
    quarentena = []
    total = ok = reparadas = 0

    with open(downloaded_file, encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=DELIMITER)
        next(reader)  # header, já lido acima
        prev = reader.line_num

        for row in reader:
            atual = reader.line_num
            numero_linha = prev + 1  # 1-based, header = linha 1
            total += 1

            if len(row) == n_esperado:
                linhas_ok.append([row[idx] for idx in indices])
                ok += 1
            else:
                texto_bruto = "".join(linhas_fisicas[prev:atual])
                texto_reparado = reparar_texto(texto_bruto)
                tentativa = list(csv.reader(io.StringIO(texto_reparado), delimiter=DELIMITER))
                if len(tentativa) == 1 and len(tentativa[0]) == n_esperado:
                    campos = tentativa[0]
                    linhas_ok.append([campos[idx] for idx in indices])
                    reparadas += 1
                else:
                    motivo = f"contagem de campos: esperado {n_esperado}, obtido {len(row)}"
                    quarentena.append((numero_linha, motivo, texto_bruto))

            prev = atual

    return header_seed, linhas_ok, quarentena, (total, ok, reparadas, len(quarentena))


def escrever_saida(caminho, header, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=DELIMITER, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(linhas)


def escrever_quarentena(caminho, registros):
    if not registros:
        return
    arquivo_existe = os.path.isfile(caminho) and os.path.getsize(caminho) > 0
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=DELIMITER, lineterminator="\n")
        if not arquivo_existe:
            writer.writerow(["numero_linha", "motivo", "linha_bruta"])
        for numero_linha, motivo, texto_bruto in registros:
            writer.writerow([numero_linha, motivo, texto_bruto])


def main():
    if len(sys.argv) != 4:
        print(
            "uso: process_csv.py <seed_file> <downloaded_file> <output_file>",
            file=sys.stderr,
        )
        return 1

    seed_file, downloaded_file, output_file = sys.argv[1:4]
    quarantine_file = os.environ.get(
        "QUARANTINE_FILE", "/var/log/compras-publicas/contratos_quarentena.csv"
    )

    try:
        header, linhas_ok, quarentena, (total, ok, reparadas, n_quarentena) = processar(
            seed_file, downloaded_file
        )
        escrever_saida(output_file, header, linhas_ok)
        escrever_quarentena(quarantine_file, quarentena)
    except ProcessamentoError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    print(
        f"process_csv: {total} linhas lidas | {ok} ok | {reparadas} reparadas | "
        f"{n_quarentena} em quarentena ({quarantine_file})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
