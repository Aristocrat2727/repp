from flask import Flask, request, jsonify, render_template_string
import httpx
import os

app = Flask(__name__)

# Создаем HTTP клиент вручную (обходим баг с proxies)
http_client = httpx.Client(
    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.ecomagent.in/"),
    headers={
        "x-api-key": os.environ.get("ANTHROPIC_AUTH_TOKEN", ""),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    },
    timeout=60.0
)

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude AI Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 800px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: #2d2d2d;
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 20px; font-weight: 600; }
        .status {
            font-size: 12px;
            color: #4ade80;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status::before {
            content: '';
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { justify-content: flex-end; }
        .message.assistant { justify-content: flex-start; }
        .bubble {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.5;
        }
        .message.user .bubble {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .bubble {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        .input-area {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-area input:focus { border-color: #667eea; }
        .input-area button {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, background 0.3s;
        }
        .input-area button:hover {
            background: #5a6fd6;
            transform: scale(1.02);
        }
        .input-area button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .footer {
            text-align: center;
            padding: 8px;
            font-size: 11px;
            color: #999;
            background: #f8f9fa;
        }
        .clear-btn {
            background: #e74c3c;
            padding: 8px 16px;
            border: none;
            border-radius: 15px;
            color: white;
            cursor: pointer;
            font-size: 12px;
        }
        .clear-btn:hover {
            background: #c0392b;
        }
        .model-badge {
            font-size: 10px;
            background: #4ade80;
            color: #1a1a1a;
            padding: 2px 10px;
            border-radius: 12px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Claude AI</h1>
            <div style="display: flex; align-items: center; gap: 15px;">
                <span class="model-badge">Opus 4.8</span>
                <button class="clear-btn" onclick="clearChat()">Очистить</button>
                <div class="status">Online</div>
            </div>
        </div>

        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="bubble">Привет! Я Claude Opus 4.8 через ecomagent.in. Задайте мне вопрос!</div>
            </div>
        </div>

        <div class="input-area">
            <input type="text" id="userInput" placeholder="Введите сообщение..." />
            <button id="sendBtn">Отправить</button>
        </div>
        <div class="footer">Работает на ecomagent.in прокси • Модель: Claude Opus 4.8</div>
    </div>

    <script>
        const messagesContainer = document.getElementById('messages');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.className = `message ${sender}`;
            div.innerHTML = `<div class="bubble">${text}</div>`;
            messagesContainer.appendChild(div);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'message assistant';
            div.id = 'typing';
            div.innerHTML = `<div class="bubble">✍️ Печатает...</div>`;
            messagesContainer.appendChild(div);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function removeTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }

        function clearChat() {
            messagesContainer.innerHTML = '';
            addMessage('Чат очищен! Задайте новый вопрос.', 'assistant');
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            userInput.value = '';
            sendBtn.disabled = true;
            showTyping();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                const data = await response.json();
                removeTyping();

                if (data.success) {
                    addMessage(data.response, 'assistant');
                } else {
                    addMessage(`❌ Ошибка: ${data.error}`, 'assistant');
                }
            } catch (error) {
                removeTyping();
                addMessage(`❌ Ошибка соединения: ${error.message}`, 'assistant');
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        userInput.focus();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Сообщение пустое'})
        
        # Отправляем запрос напрямую через httpx
        response = http_client.post(
            "/v1/messages",
            json={
                "model": "claude-opus-4-8",  # Используем доступную модель
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": user_message}]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            # Извлекаем текст ответа
            if 'content' in result and len(result['content']) > 0:
                reply = result['content'][0].get('text', 'Нет текста в ответе')
                return jsonify({'success': True, 'response': reply})
            else:
                return jsonify({'success': False, 'error': 'Неожиданный формат ответа'})
        else:
            return jsonify({
                'success': False, 
                'error': f'API ошибка {response.status_code}: {response.text}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
