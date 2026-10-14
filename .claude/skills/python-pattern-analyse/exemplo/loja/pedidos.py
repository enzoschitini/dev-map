import datetime
import json
import os
import smtplib
import sqlite3
import urllib.request
from email.message import EmailMessage

DB_PATH = os.environ.get("LOJA_DB", "loja.db")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.loja.com")
PAGFACIL_KEY = os.environ.get("PAGFACIL_KEY", "")
PAYMUNDI_KEY = os.environ.get("PAYMUNDI_KEY", "")


class GerenciadorDePedidos:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS pedidos ("
            "id INTEGER PRIMARY KEY, cliente TEXT, email TEXT, total REAL, "
            "status TEXT, gateway TEXT, transacao TEXT)"
        )

    def processar(self, dados):
        # validação
        if not dados.get("itens"):
            raise ValueError("pedido sem itens")
        if "@" not in dados.get("email", ""):
            raise ValueError("email inválido")
        for item in dados["itens"]:
            if item["qtd"] <= 0:
                raise ValueError(f"quantidade inválida para {item['sku']}")

        # total com desconto
        subtotal = sum(i["preco"] * i["qtd"] for i in dados["itens"])
        tipo = dados.get("tipo_cliente", "comum")
        if tipo == "comum":
            desconto = 0
        elif tipo == "vip":
            desconto = subtotal * 0.10
        elif tipo == "funcionario":
            desconto = subtotal * 0.30
        elif tipo == "atacado":
            desconto = subtotal * 0.15 if subtotal > 1000 else subtotal * 0.05
        else:
            desconto = 0
        if datetime.date.today().month == 11 and tipo != "funcionario":  # black friday
            desconto += subtotal * 0.05
        total = round(subtotal - desconto, 2)

        # frete
        if dados.get("uf") in ("SP", "RJ", "MG"):
            frete = 15.0
        else:
            frete = 30.0
        if total > 300:
            frete = 0
        total += frete

        # pagamento
        gateway = dados.get("gateway", "pagfacil")
        if gateway == "pagfacil":
            body = json.dumps({"valor_centavos": int(total * 100), "cartao": dados["cartao"]}).encode()
            req = urllib.request.Request(
                "https://api.pagfacil.com/v1/cobrancas",
                data=body,
                headers={"Authorization": "Bearer " + PAGFACIL_KEY, "Content-Type": "application/json"},
            )
            resp = json.loads(urllib.request.urlopen(req).read())
            if resp["situacao"] != "APROVADA":
                raise Exception("pagamento recusado: " + resp.get("motivo", ""))
            transacao = resp["id_cobranca"]
        elif gateway == "paymundi":
            body = json.dumps({"amount": total, "currency": "BRL", "card_token": dados["cartao"]}).encode()
            req = urllib.request.Request(
                "https://paymundi.io/v2/charges",
                data=body,
                headers={"X-Api-Key": PAYMUNDI_KEY, "Content-Type": "application/json"},
            )
            resp = json.loads(urllib.request.urlopen(req).read())
            if resp["status"] != "succeeded":
                raise Exception("pagamento recusado: " + resp["error"]["message"])
            transacao = resp["charge_id"]
        else:
            raise Exception("gateway desconhecido: " + gateway)

        # salvar
        cur = self.conn.execute(
            "INSERT INTO pedidos (cliente, email, total, status, gateway, transacao) VALUES (?, ?, ?, ?, ?, ?)",
            (dados["cliente"], dados["email"], total, "pago", gateway, transacao),
        )
        self.conn.commit()
        pedido_id = cur.lastrowid

        # email
        msg = EmailMessage()
        msg["Subject"] = f"Pedido {pedido_id} confirmado"
        msg["From"] = "loja@loja.com"
        msg["To"] = dados["email"]
        msg.set_content(
            f"Olá {dados['cliente']}, seu pedido de R$ {total:.2f} foi confirmado. Transação: {transacao}"
        )
        with smtplib.SMTP(SMTP_HOST) as s:
            s.send_message(msg)

        print(f"[{datetime.datetime.now()}] pedido {pedido_id} processado")
        return {"id": pedido_id, "total": total, "transacao": transacao}

    def marcar_enviado(self, pedido_id, codigo_rastreio):
        row = self.conn.execute("SELECT status, email, cliente FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if row is None:
            raise Exception("pedido não existe")
        status, email, cliente = row
        if status == "pago":
            self.conn.execute("UPDATE pedidos SET status = 'enviado' WHERE id = ?", (pedido_id,))
            self.conn.commit()
            msg = EmailMessage()
            msg["Subject"] = f"Pedido {pedido_id} enviado"
            msg["From"] = "loja@loja.com"
            msg["To"] = email
            msg.set_content(f"Olá {cliente}, seu pedido foi enviado. Rastreio: {codigo_rastreio}")
            with smtplib.SMTP(SMTP_HOST) as s:
                s.send_message(msg)
        elif status == "enviado":
            raise Exception("pedido já enviado")
        elif status == "cancelado":
            raise Exception("pedido cancelado não pode ser enviado")

    def cancelar(self, pedido_id):
        row = self.conn.execute("SELECT status, email, cliente FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if row is None:
            raise Exception("pedido não existe")
        status, email, cliente = row
        if status == "pago":
            self.conn.execute("UPDATE pedidos SET status = 'cancelado' WHERE id = ?", (pedido_id,))
            self.conn.commit()
            msg = EmailMessage()
            msg["Subject"] = f"Pedido {pedido_id} cancelado"
            msg["From"] = "loja@loja.com"
            msg["To"] = email
            msg.set_content(f"Olá {cliente}, seu pedido foi cancelado.")
            with smtplib.SMTP(SMTP_HOST) as s:
                s.send_message(msg)
        elif status == "enviado":
            raise Exception("pedido já enviado, abra uma devolução")
        elif status == "cancelado":
            raise Exception("pedido já cancelado")
