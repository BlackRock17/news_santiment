from flask import Flask, render_template, request, jsonify
from crypto_analyzer import CryptoAnalyzer
import time

app = Flask(__name__)

# Инициализираме analyzer веднъж при стартиране (за по-бърза работа)
print("Стартиране на Flask app и зареждане на модели...")
crypto_analyzer = CryptoAnalyzer()
print("Flask app готов!")


@app.route('/')
def index():
    """Главна страница"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_text():
    """API endpoint за анализ на текст с интегриран summarizer"""
    try:
        # Вземаме текста от POST заявката
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'error': 'Няма предоставен текст'}), 400

        # Правим пълен анализ с интегрирания summarizer
        start_time = time.time()
        result = crypto_analyzer.analyze_crypto_text(text)
        analysis_time = round(time.time() - start_time, 2)

        # ПОПРАВКА: Конвертираме всички float32 в обикновени float
        def convert_floats(obj):
            """Конвертира numpy float32 в Python float за JSON"""
            if isinstance(obj, dict):
                return {key: convert_floats(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy float32/float64
                return float(obj.item())
            elif isinstance(obj, (float, int)):
                return float(obj)
            else:
                return obj

        # Почистваме резултата
        clean_result = convert_floats(result)
        clean_result['total_analysis_time'] = analysis_time

        return jsonify(clean_result)

    except Exception as e:
        print(f"ГРЕШКА в analyze_text: {str(e)}")  # За debugging
        return jsonify({'error': f'Грешка при анализа: {str(e)}'}), 500


@app.route('/health')
def health_check():
    """Проверка дали приложението работи"""
    return jsonify({
        'status': 'OK',
        'message': 'Crypto Analyzer е готов!',
        'summarization_threshold': crypto_analyzer.text_summarizer.min_words_for_summary
    })


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("CRYPTO SENTIMENT ANALYZER WITH SUMMARIZATION")
    print("Отвори браузър на: http://127.0.0.1:5000")
    print(f"Summarization лимит: {crypto_analyzer.text_summarizer.min_words_for_summary}+ думи")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)
