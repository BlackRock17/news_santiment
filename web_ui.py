"""
Simplified AI Analysis Web UI - Само за персонално използване
Без threading, без real-time updates, само прости sync операции
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import os
from datetime import datetime

# Import на AI модулите
from postgres_reader import PostgreSQLReader
from analysis_workflow import AnalysisWorkflow

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Една global database connection (reuse за всички заявки)
db_reader = PostgreSQLReader()


@app.route('/')
def dashboard():
    """Главна страница - Dashboard"""
    try:
        # Вземаме статистики от базата данни
        stats = db_reader.get_database_stats()

        # Показваме първите неанализирани статии
        unanalyzed_preview = []
        if stats and stats['unanalyzed_articles'] > 0:
            unanalyzed_preview = db_reader.get_unanalyzed_articles(limit=5)

        return render_template('dashboard.html',
                               stats=stats,
                               unanalyzed_preview=unanalyzed_preview)

    except Exception as e:
        flash(f"Грешка при зареждане на dashboard: {str(e)}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/analysis')
def analysis_page():
    """Страница за управление на анализа"""
    try:
        stats = db_reader.get_database_stats()

        # Вземаме списък с неанализирани статии
        unanalyzed_articles = []
        if stats and stats['unanalyzed_articles'] > 0:
            unanalyzed_articles = db_reader.get_unanalyzed_articles(limit=20)

        return render_template('analysis.html',
                               stats=stats,
                               unanalyzed_articles=unanalyzed_articles)

    except Exception as e:
        flash(f"Грешка при зареждане на анализ страницата: {str(e)}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Стартира loading страница и после анализ"""
    try:
        # Вземаме параметрите от формата
        limit = int(request.form.get('limit', 5))
        save_results = request.form.get('save_results') == 'on'

        # Валидация
        if limit < 1 or limit > 50:
            flash('Лимитът трябва да е между 1 и 50 статии.', 'error')
            return redirect(url_for('analysis_page'))

        # Показваме loading страница
        return render_template('analysis_loading.html',
                               limit=limit,
                               save_results=save_results)

    except Exception as e:
        flash(f'Грешка при стартиране на анализ: {str(e)}', 'error')
        return redirect(url_for('analysis_page'))


@app.route('/run_analysis/<int:limit>/<save_results>')
def run_analysis(limit, save_results):
    """Прави SYNC анализ и пренасочва към резултатите"""
    try:
        print(f"🚀 Стартиране на SYNC анализ за {limit} статии...")

        # Създаваме workflow и правим анализ (SYNC - без threading)
        workflow = AnalysisWorkflow()
        results = workflow.process_unanalyzed_articles(
            limit=limit,
            save_results=(save_results == 'true')
        )

        # След завършване показваме резултата
        success_msg = f'Анализ завърши успешно! {results["successful_analyses"]} статии анализирани за {results["processing_time"]:.1f} секунди.'
        flash(success_msg, 'success')

        return redirect(url_for('results_page'))

    except Exception as e:
        flash(f'Грешка по време на анализа: {str(e)}', 'error')
        return redirect(url_for('analysis_page'))


@app.route('/results')
def results_page():
    """Страница за преглед на резултати от анализи"""
    try:
        # Търсим JSON файлове с резултати
        result_files = []
        for filename in os.listdir('.'):
            if filename.startswith('analysis_results_') and filename.endswith('.json'):
                try:
                    # Вземаме информация за файла
                    file_stats = os.stat(filename)
                    file_size = round(file_stats.st_size / 1024, 1)  # KB
                    modified_time = datetime.fromtimestamp(file_stats.st_mtime)

                    # Четем първите няколко резултата за preview
                    import json
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    result_files.append({
                        'filename': filename,
                        'size_kb': file_size,
                        'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'article_count': len(data) if isinstance(data, list) else 0,
                        'preview': data[:2] if isinstance(data, list) and len(data) > 0 else []
                    })

                except Exception:
                    continue

        # Сортираме по дата (най-новите първо)
        result_files.sort(key=lambda x: x['modified'], reverse=True)

        return render_template('results.html', result_files=result_files)

    except Exception as e:
        flash(f"Грешка при зареждане на резултати: {str(e)}", 'error')
        return render_template('results.html', result_files=[])


@app.route('/view_result/<filename>')
def view_result(filename):
    """Показва детайли за конкретен резултат файл"""
    try:
        print(f"🔍 Trying to view result file: {filename}")
        print(f"📂 Current directory files: {os.listdir('.')}")

        # Валидация на filename за сигурност
        if not filename.startswith('analysis_results_') or not filename.endswith('.json'):
            print(f"❌ Invalid filename format: {filename}")
            flash('Невалиден файл.', 'error')
            return redirect(url_for('results_page'))

        if not os.path.exists(filename):
            print(f"❌ File does not exist: {filename}")
            flash('Файлът не съществува.', 'error')
            return redirect(url_for('results_page'))

        print(f"✅ File exists, reading: {filename}")

        # Четем данните
        import json
        with open(filename, 'r', encoding='utf-8') as f:
            results_data = json.load(f)

        print(f"✅ JSON loaded successfully, data type: {type(results_data)}")

        # Статистики
        total_results = len(results_data) if isinstance(results_data, list) else 0
        print(f"📊 Total results: {total_results}")

        sentiment_stats = {}
        entity_stats = {}

        if isinstance(results_data, list):
            for result in results_data:
                # Sentiment статистики
                sentiment = result.get('sentiment', {}).get('label', 'unknown')
                sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1

                # Entity статистики
                entities = result.get('entities', {})
                for category, entity_list in entities.items():
                    if entity_list:
                        entity_stats[category] = entity_stats.get(category, 0) + len(entity_list)

        print(f"📈 Sentiment stats: {sentiment_stats}")
        print(f"🏷️ Entity stats: {entity_stats}")
        print(f"✅ Rendering view_result.html template")

        return render_template('view_result.html',
                               filename=filename,
                               results_data=results_data,
                               total_results=total_results,
                               sentiment_stats=sentiment_stats,
                               entity_stats=entity_stats)

    except Exception as e:
        print(f"❌ Error in view_result: {str(e)}")
        print(f"❌ Exception type: {type(e)}")
        flash(f"Грешка при четене на файл: {str(e)}", 'error')
        return redirect(url_for('results_page'))


@app.route('/settings')
def settings_page():
    """Страница за настройки"""
    try:
        # Показваме текущите настройки на анализатора
        workflow = AnalysisWorkflow()

        settings_info = {
            'summarization_threshold': workflow.crypto_analyzer.text_summarizer.min_words_for_summary,
            'max_input_words': workflow.crypto_analyzer.text_summarizer.max_input_words,
            'target_summary_words': workflow.crypto_analyzer.text_summarizer.target_summary_words
        }

        return render_template('settings.html', settings=settings_info)

    except Exception as e:
        flash(f"Грешка при зареждане на настройки: {str(e)}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Тестваме връзката с базата данни
        stats = db_reader.get_database_stats()

        return {
            'status': 'OK',
            'database_connection': 'OK' if stats else 'ERROR',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500


if __name__ == '__main__':
    print("🚀 Simplified AI Analysis Web UI стартиране...")
    print("📊 Dashboard: http://localhost:5002")
    print("🤖 Analysis Control: http://localhost:5002/analysis")
    print("📈 Results: http://localhost:5002/results")
    print("💡 Optimized for personal use - no threading, no real-time updates")
    print("=" * 50)

    # Стартираме Flask приложението
    app.run(debug=True, host='0.0.0.0', port=5002)
