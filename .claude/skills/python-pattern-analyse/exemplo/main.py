from loja.pedidos import GerenciadorDePedidos

if __name__ == "__main__":
    g = GerenciadorDePedidos()
    print(g.processar({
        "cliente": "Ana", "email": "ana@ex.com", "uf": "SP", "tipo_cliente": "vip",
        "gateway": "pagfacil", "cartao": "tok_123",
        "itens": [{"sku": "A1", "preco": 100.0, "qtd": 2}],
    }))
