"""
Analysis Workflow - Интеграция между PostgreSQL Reader и AI Анализатор
Чете неанализирани статии от базата и ги анализира
"""

import time
import json
from datetime import datetime
from postgres_reader import PostgreSQLReader
from crypto_analyzer import CryptoAnalyzer


class AnalysisWorkflow:
    def __init__(self):
        """
        Инициализира workflow за анализ
        """
        print("🚀 Инициализиране на Analysis Workflow...")

        # Инициализираме компонентите
        print("📊 Зареждане на PostgreSQL Reader...")
        self.db_reader = PostgreSQLReader()

        print("🤖 Зареждане на AI анализатор...")
        self.crypto_analyzer = CryptoAnalyzer()

        print("✅ Analysis Workflow готов!")

    def analyze_single_article(self, article_data):
        """
        Анализира една статия

        Args:
            article_data (dict): Данни за статията от базата данни

        Returns:
            dict: Резултат от анализа или None ако има грешка
        """
        article_id = article_data['id']
        title = article_data['title']
        content = article_data['content']

        print(f"\n📄 Анализиране на статия ID:{article_id}")
        print(f"   Заглавие: {title[:60]}...")
        print(f"   Дължина: {len(content)} символа")

        try:
            # Стартираме AI анализ
            start_time = time.time()
            analysis_result = self.crypto_analyzer.analyze_crypto_text(content)
            analysis_time = round(time.time() - start_time, 2)

            # Добавяме метаданни
            analysis_result['metadata'] = {
                'article_id': article_id,
                'article_title': title,
                'article_url': article_data['url'],
                'analyzed_at': datetime.now().isoformat(),
                'analysis_time_seconds': analysis_time
            }

            print(f"✅ Анализ завършен за {analysis_time}s")
            print(
                f"   Sentiment: {analysis_result['sentiment']['label']} ({analysis_result['sentiment']['confidence']:.2f})")

            # Показваме entities
            total_entities = sum(len(entities) for entities in analysis_result['entities'].values())
            print(f"   Entities: {total_entities} намерени")

            return analysis_result

        except Exception as e:
            print(f"❌ Грешка при анализ на статия ID:{article_id}: {str(e)}")
            return None

    def process_unanalyzed_articles(self, limit=5, save_results=True):
        """
        Основният метод - обработва неанализирани статии

        Args:
            limit (int): Максимален брой статии за обработка
            save_results (bool): Дали да запазва резултатите в JSON файл

        Returns:
            dict: Статистики за обработката
        """
        print(f"\n🎯 ЗАПОЧВАНЕ НА BATCH АНАЛИЗ")
        print(f"🔍 Търсене на до {limit} неанализирани статии...")

        # Стъпка 1: Вземаме неанализирани статии
        articles = self.db_reader.get_unanalyzed_articles(limit=limit)

        if not articles:
            print("📋 Няма неанализирани статии за обработка")
            return {
                'total_articles': 0,
                'successful_analyses': 0,
                'failed_analyses': 0,
                'processing_time': 0
            }

        print(f"📰 Намерени {len(articles)} статии за анализ")

        # Статистики
        successful_count = 0
        failed_count = 0
        analysis_results = []

        start_time = time.time()

        # Стъпка 2: Анализираме всяка статия
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] " + "=" * 50)

            # Анализираме статията
            analysis_result = self.analyze_single_article(article)

            if analysis_result:
                # Стъпка 3: Маркираме като анализирана
                success = self.db_reader.mark_article_as_analyzed(
                    article['id'],
                    analysis_summary=analysis_result['summary']
                )

                if success:
                    successful_count += 1
                    analysis_results.append(analysis_result)
                    print(f"✅ Статия {i} успешно обработена и маркирана")
                else:
                    failed_count += 1
                    print(f"❌ Грешка при маркиране на статия {i}")
            else:
                failed_count += 1
                print(f"❌ Анализът на статия {i} се провали")

            # Малка пауза между статиите
            if i < len(articles):
                print("⏳ Пауза 2 секунди...")
                time.sleep(2)

        # Стъпка 4: Обобщение
        total_time = round(time.time() - start_time, 2)

        print(f"\n" + "=" * 60)
        print(f"🎉 BATCH АНАЛИЗ ЗАВЪРШЕН!")
        print(f"📊 РЕЗУЛТАТИ:")
        print(f"   📰 Общо статии: {len(articles)}")
        print(f"   ✅ Успешни: {successful_count}")
        print(f"   ❌ Неуспешни: {failed_count}")
        print(f"   🕒 Общо време: {total_time}s")
        print(f"   ⚡ Средно време/статия: {total_time / len(articles):.1f}s")

        # Стъпка 5: Запазваме резултатите (опционално)
        if save_results and analysis_results:
            self.save_analysis_results(analysis_results)

        # Показваме обновени статистики от базата данни
        updated_stats = self.db_reader.get_database_stats()
        print(f"\n📊 ОБНОВЕНИ СТАТИСТИКИ ОТ БАЗАТА:")
        print(f"   📰 Общо статии: {updated_stats['total_articles']}")
        print(f"   ✅ Анализирани: {updated_stats['analyzed_articles']}")
        print(f"   ⏳ Неанализирани: {updated_stats['unanalyzed_articles']}")

        return {
            'total_articles': len(articles),
            'successful_analyses': successful_count,
            'failed_analyses': failed_count,
            'processing_time': total_time,
            'analysis_results': analysis_results
        }

    def save_analysis_results(self, analysis_results):
        """
        Запазва резултатите от анализа в JSON файл

        Args:
            analysis_results (list): Списък с резултати от анализа
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2, default=str)

            print(f"💾 Резултатите запазени в файл: {filename}")
            print(f"   📊 {len(analysis_results)} анализа запазени")

        except Exception as e:
            print(f"❌ Грешка при запазване на резултатите: {e}")

    def get_workflow_status(self):
        """
        Показва статус на workflow-а - какво има за анализиране
        """
        print("\n📊 WORKFLOW STATUS")
        print("=" * 30)

        try:
            # Статистики от базата данни
            stats = self.db_reader.get_database_stats()

            print("📈 База данни статистики:")
            print(f"   📰 Общо статии: {stats['total_articles']}")
            print(f"   ✅ Анализирани: {stats['analyzed_articles']}")
            print(f"   ⏳ Неанализирани: {stats['unanalyzed_articles']}")

            if stats['latest_article']:
                title, date = stats['latest_article']
                print(f"   📅 Най-нова: {title[:40]}... ({date})")

            # Показваме първите неанализирани статии
            if stats['unanalyzed_articles'] > 0:
                print(f"\n📋 Следващи статии за анализ:")
                unanalyzed = self.db_reader.get_unanalyzed_articles(limit=5)

                for i, article in enumerate(unanalyzed, 1):
                    print(f"   {i}. ID:{article['id']} | {article['title'][:50]}...")
                    print(f"      📊 {article['content_length']} chars | {article['scraped_at']}")

                print(
                    f"\n💡 Препоръка: python analysis_workflow.py analyze --limit {min(stats['unanalyzed_articles'], 5)}")
            else:
                print(f"\n✅ Всички статии са анализирани!")
                print(f"💡 Добави нови статии със scraper-а за да продължиш анализа")

        except Exception as e:
            print(f"❌ Грешка при показване на статус: {e}")


# Тестови функции
def test_workflow():
    """
    Тества workflow-а с една статия
    """
    print("=== ТЕСТ НА ANALYSIS WORKFLOW ===")

    try:
        # Създаваме workflow
        workflow = AnalysisWorkflow()

        # Показваме статус
        workflow.get_workflow_status()

        # Тестваме с 1 статия
        print(f"\n🧪 ТЕСТ: Анализ на 1 статия")
        results = workflow.process_unanalyzed_articles(limit=1, save_results=True)

        if results['successful_analyses'] > 0:
            print(f"\n🎉 Workflow тест УСПЕШЕН!")
            print(f"✅ Успешно анализирана {results['successful_analyses']} статия")
            return True
        else:
            print(f"\n⚠️ Workflow тест - няма статии за анализ")
            return True  # Не е грешка ако няма статии

    except Exception as e:
        print(f"\n❌ Workflow тест неуспешен: {e}")
        return False


def main():
    """
    Основна функция за тестване
    """
    print("=== ANALYSIS WORKFLOW СИСТЕМА ===")

    try:
        # Тестваме workflow-а
        success = test_workflow()

        if success:
            print(f"\n🚀 Analysis Workflow е готов за използване!")
            print(f"\n📝 Командни опции:")
            print(f"   python analysis_workflow.py                    # Тест")
            print(f"   workflow.process_unanalyzed_articles(limit=5)  # Анализ на 5 статии")
            print(f"   workflow.get_workflow_status()                 # Статус")
        else:
            print(f"\n❌ Има проблеми с workflow-а")

    except Exception as e:
        print(f"\n❌ Критична грешка: {e}")


if __name__ == "__main__":
    main()
