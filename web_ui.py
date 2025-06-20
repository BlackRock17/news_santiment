"""
AI Analysis Web UI - Flask приложение за управление на crypto sentiment analysis
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
import time
from datetime import datetime
from threading import Thread
import logging

# Import на нашите модули
from postgres_reader import PostgreSQLReader
from analysis_workflow import AnalysisWorkflow

# Настройка на logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Промени това в production

# Глобални променливи за статус
analysis_in_progress = False
current_analysis_stats = {}


def background_analysis(limit, save_results):
    """Стартира анализ в background thread"""
    global analysis_in_progress, current_analysis_stats

    try:
        analysis_in_progress = True
        logger.info(f"Starting background analysis with limit={limit}")

        # Създаваме workflow
        workflow = AnalysisWorkflow()

        # Стартираме анализа
        results = workflow.process_unanalyzed_articles(limit=limit, save_results=save_results)

        # Запазваме статистиките
        current_analysis_stats = {
            'completed': True,
            'total_articles': results['total_articles'],
            'successful': results['successful_analyses'],
            'failed': results['failed_analyses'],
            'processing_time': results['processing_time'],
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"Background analysis completed: {results}")

    except Exception as e:
        logger.error(f"Error in background analysis: {e}")
        current_analysis_stats = {
            'completed': True,
            'error': str(e),
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    finally:
        analysis_in_progress = False


@app.route('/')
def dashboard():
    """Главна страница - Dashboard"""
    try:
        # Вземаме статистики от базата данни
        db_reader = PostgreSQLReader()
        stats = db_reader.get_database_stats()

        # Ако има грешка в статистиките
        if not stats:
            stats = {
                'total_articles': 0,
                'analyzed_articles': 0,
                'unanalyzed_articles': 0,
                'latest_article': None
            }

        # Добавяме статус информация
        stats['analysis_in_progress'] = analysis_in_progress
        stats['last_analysis'] = current_analysis_stats.get('completed_at', 'Never')

        # Показваме първите неанализирани статии
        unanalyzed_preview = []
        if stats['unanalyzed_articles'] > 0:
            unanalyzed_preview = db_reader.get_unanalyzed_articles(limit=5)

        return render_template('dashboard.html',
                               stats=stats,
                               unanalyzed_preview=unanalyzed_preview)

    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        flash(f"Грешка при зареждане на dashboard: {str(e)}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/analysis')
def analysis_page():
    """Страница за управление на анализа"""
    try:
        db_reader = PostgreSQLReader()
        stats = db_reader.get_database_stats()

        # Вземаме списък с неанализирани статии
        unanalyzed_articles = []
        if stats and stats['unanalyzed_articles'] > 0:
            unanalyzed_articles = db_reader.get_unanalyzed_articles(limit=20)

        return render_template('analysis.html',
                               stats=stats,
                               unanalyzed_articles=unanalyzed_articles,
                               analysis_in_progress=analysis_in_progress)

    except Exception as e:
        logger.error(f"Error in analysis page: {e}")
        flash(f"Грешка при зареждане на анализ страницата: {str(e)}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Стартира анализ на статии"""
    global analysis_in_progress

    if analysis_in_progress:
        flash('Анализ вече е в ход. Моля изчакайте да завърши.', 'warning')
        return redirect(url_for('analysis_page'))

    try:
        # Вземаме параметрите от формата
        limit = int(request.form.get('limit', 5))
        save_results = request.form.get('save_results') == 'on'

        # Валидация
        if limit < 1 or limit > 50:
            flash('Лимитът трябва да е между 1 и 50 статии.', 'error')
            return redirect(url_for('analysis_page'))

        # Стартираме анализа в background thread
        thread = Thread(target=background_analysis, args=(limit, save_results))
        thread.daemon = True
        thread.start()

        flash(f'Анализ стартиран за {limit} статии. Ще отнеме няколко минути...', 'info')
        return redirect(url_for('analysis_status'))

    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        flash(f'Грешка при стартиране на анализ: {str(e)}', 'error')
        return redirect(url_for('analysis_page'))


@app.route('/analysis_status')
def analysis_status():
    """Страница за статус на анализа (real-time updates)"""
    try:
        db_reader = PostgreSQLReader()
        current_stats = db_reader.get_database_stats()

        return render_template('analysis_status.html',
                               analysis_in_progress=analysis_in_progress,
                               current_stats=current_stats,
                               analysis_results=current_analysis_stats)

    except Exception as e:
        logger.error(f"Error in analysis status: {e}")
        flash(f"Грешка при показване на статус: {str(e)}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/api/analysis_status')
def api_analysis_status():
    """API endpoint за real-time статус на анализа"""
    try:
        db_reader = PostgreSQLReader()
        current_stats = db_reader.get_database_stats()

        return jsonify({
            'analysis_in_progress': analysis_in_progress,
            'database_stats': current_stats,
            'analysis_results': current_analysis_stats
        })

    except Exception as e:
        logger.error(f"Error in API analysis status: {e}")
        return jsonify({'error': str(e)}), 500


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
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    result_files.append({
                        'filename': filename,
                        'size_kb': file_size,
                        'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'article_count': len(data) if isinstance(data, list) else 0,
                        'preview': data[:2] if isinstance(data, list) and len(data) > 0 else []
                    })

                except Exception as e:
                    logger.warning(f"Could not read file {filename}: {e}")
                    continue

        # Сортираме по дата (най-новите първо)
        result_files.sort(key=lambda x: x['modified'], reverse=True)

        return render_template('results.html', result_files=result_files)

    except Exception as e:
        logger.error(f"Error in results page: {e}")
        flash(f"Грешка при зареждане на резултати: {str(e)}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/view_result/<filename>')
def view_result(filename):
    """Показва детайли за конкретен резултат файл"""
    try:
        # Валидация на filename за сигурност
        if not filename.startswith('analysis_results_') or not filename.endswith('.json'):
            flash('Невалиден файл.', 'error')
            return redirect(url_for('results_page'))

        if not os.path.exists(filename):
            flash('Файлът не съществува.', 'error')
            return redirect(url_for('results_page'))

        # Четем данните
        with open(filename, 'r', encoding='utf-8') as f:
            results_data = json.load(f)

        # Статистики
        total_results = len(results_data) if isinstance(results_data, list) else 0

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

        return render_template('view_result.html',
                               filename=filename,
                               results_data=results_data,
                               total_results=total_results,
                               sentiment_stats=sentiment_stats,
                               entity_stats=entity_stats)

    except Exception as e:
        logger.error(f"Error viewing result {filename}: {e}")
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
        logger.error(f"Error in settings page: {e}")
        flash(f"Грешка при зареждане на настройки: {str(e)}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Тестваме връзката с базата данни
        db_reader = PostgreSQLReader()
        stats = db_reader.get_database_stats()

        return jsonify({
            'status': 'OK',
            'database_connection': 'OK' if stats else 'ERROR',
            'analysis_in_progress': analysis_in_progress,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    print("🚀 AI Analysis Web UI стартиране...")
    print("📊 Dashboard: http://localhost:5002")
    print("🤖 Analysis Control: http://localhost:5002/analysis")
    print("📈 Results: http://localhost:5002/results")
    print("=" * 50)

    # Стартираме Flask приложението
    app.run(debug=True, host='0.0.0.0', port=5002)
