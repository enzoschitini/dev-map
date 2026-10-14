def gerar_relatorio_vendas(conn, inicio, fim):
    """CSV com os pedidos pagos ou enviados entre duas datas (texto ISO)."""
    rows = conn.execute(
        "SELECT id, cliente, total FROM pedidos WHERE status IN ('pago', 'enviado') AND id BETWEEN ? AND ?",
        (inicio, fim),
    ).fetchall()
    linhas = ["id;cliente;total"]
    for pedido_id, cliente, total in rows:
        linhas.append(f"{pedido_id};{cliente};{total:.2f}".replace(".", ","))
    return "\n".join(linhas)
