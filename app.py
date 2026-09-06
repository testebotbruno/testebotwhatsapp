import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuração da API do Gemini via REST
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# Dados da Evolution API
EVOLUTION_URL = "https://evolution-api-production-5008.up.railway.app"
INSTANCE_NAME = "restaurante atendimento"
EVOLUTION_API_KEY = "55FDF751A44E-43F4-9768-1D0C01FE4979"

# Prompt do Sistema Rico em Informações e Flexível
SYSTEM_PROMPT = """
Você é o assistente virtual inteligente e simpático de um delivery de comida. Seu objetivo é atender os clientes no WhatsApp com cordialidade, agilidade e clareza.

Aqui estão as informações do seu estabelecimento para você responder aos clientes:
- **Cardápio**: 
  1. X-Burguer Especial (Pão brioche, carne 180g, queijo cheddar, bacon e molho da casa) - R$ 32,90
  2. Pizza Margherita (Molho de tomate fresco, mussarela, manjericão e rodelas de tomate) - R$ 48,00 (Média) / R$ 62,00 (Grande)
  3. Batata Frita Crocante (Porção individual com cheddar e bacon) - R$ 24,90
  4. Refrigerante Lata (Coca-Cola, Guaraná Antarctica) - R$ 7,00
- **Horário de Funcionamento**: De terça a domingo, das 18h às 23h30.
- **Formas de Pagamento**: Pix, Cartão de Crédito/Débito na entrega e Dinheiro.
- **Taxa de Entrega**: Varia de R$ 6,00 a R$ 12,00 dependendo do bairro (consulte informando o endereço).

Regras de Atendimento:
1. Se o cliente mandar uma saudação simples (ex: "Olá", "Oi"), seja acolhedor e apresente brevemente as opções.
2. Se o cliente perguntar sobre cardápio, preços, pratos, horários ou pagamentos, use as informações acima para responder com detalhes.
3. Converse de forma natural e amigável.
"""

@app.route("/", methods=["GET"])
def home():
    return "TestBot WhatsApp (Delivery) Rodando com Sucesso! 🚀", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Dados recebidos da Evolution API:", data)
        
        # Filtra apenas eventos de mensagens novas
        if data.get("event") != "messages.upsert":
            return jsonify({"status": "ignored_event"}), 200

        raw_data = data.get("data", {})
        message_data = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
        if not isinstance(message_data, dict):
            return jsonify({"status": "ignored"}), 200

        # Ignora se for mensagem enviada pelo próprio bot
        if message_data.get("key", {}).get("fromMe", False):
            return jsonify({"status": "ignored"}), 200

        # Extrai o conteúdo do texto
        msg_content = message_data.get("message", {})
        if not isinstance(msg_content, dict):
            return jsonify({"status": "ignored"}), 200

        message_body = msg_content.get("conversation") or msg_content.get("extendedTextMessage", {}).get("text", "")
        
        if not message_body:
            return jsonify({"status": "ignored_no_text"}), 200

        sender_number = message_data.get("key", {}).get("remoteJid", "")
        print(f"Mensagem de texto recebida de {sender_number}: {message_body}")

        # Monta a requisição para o Gemini via REST API
        gemini_payload = {
            "contents": [{"parts": [{"text": message_body}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]}
        }
        
        gemini_response = requests.post(GEMINI_URL, json=gemini_payload)
        gemini_data = gemini_response.json()
        
        # Extrai a resposta gerada com segurança
        try:
            reply_text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as err:
            print("Erro detalhado do Gemini (possível limite de cota):", gemini_data)
            # Resposta genérica mais natural caso bata o limite de 20 msgs do plano gratuito
            reply_text = "Olá! Tudo bem? Nosso atendimento de delivery está a todo vapor! O que você gostaria de pedir hoje?"

        print(f"Resposta gerada pelo Gemini: {reply_text}")

        # Envia a resposta de volta para o cliente via Evolution API
        send_url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "number": sender_number.replace("@s.whatsapp.net", "").replace("@g.us", ""),
            "text": reply_text
        }
        
        requests.post(send_url, json=payload, headers=headers)

        return jsonify({"status": "success", "reply": reply_text}), 200

    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
