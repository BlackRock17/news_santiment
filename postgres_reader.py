"""
PostgreSQL Database Reader за AI Анализ Проекта
Чете неанализирани статии от база данни "crypto_news"
"""

import psycopg2
import psycopg2.extras
from datetime import datetime


class PostgreSQLReader:
    def __init__(self):
        """
        Инициализира връзка към PostgreSQL база данни "crypto_news"
        Използва същите credentials като scraping проекта
        """
        print("🔗 Свързване към PostgreSQL база данни за четене...")

        # Същите credentials като в scraping проекта
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'crypto_news',  # Същата база като scraper-а
            'user': 'crypto_user',
            'password': 'password'
        }

        # Тестваме връзката веднага
        self._test_connection()
        print("✅ PostgreSQL Reader готов!")

    def _test_connection(self):
        """
        Тества дали може да се свърже с базата данни
        Хвърля грешка ако няма връзка
        """
        try:
            # Отваряме тест връзка
            conn = psycopg2.connect(**self.db_config)

            # Проверяваме дали таблицата 'articles' съществува
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = 'articles'
                """)
                table_exists = cursor.fetchone()[0] > 0

                if not table_exists:
                    raise Exception("Таблицата 'articles' не съществува в базата данни")

            conn.close()
            print("✅ Връзка с PostgreSQL успешна")
            print("✅ Таблица 'articles' намерена")

        except psycopg2.Error as e:
            print(f"❌ Грешка при свързване с PostgreSQL: {e}")
            raise
        except Exception as e:
            print(f"❌ Грешка: {e}")
            raise

    def get_connection(self):
        """
        Връща нова връзка към базата данни
        Използвай го в with statement: with reader.get_connection() as conn:
        """
        return psycopg2.connect(**self.db_config)

    def get_database_stats(self):
        """
        Показва основни статистики за базата данни
        Полезно за debugging и мониториране
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Общ брой статии
                    cursor.execute("SELECT COUNT(*) FROM articles")
                    total_articles = cursor.fetchone()[0]

                    # Анализирани статии
                    cursor.execute("SELECT COUNT(*) FROM articles WHERE is_analyzed = TRUE")
                    analyzed_articles = cursor.fetchone()[0]

                    # Неанализирани статии
                    cursor.execute("SELECT COUNT(*) FROM articles WHERE is_analyzed = FALSE")
                    unanalyzed_articles = cursor.fetchone()[0]

                    # Най-нова статия
                    cursor.execute("""
                        SELECT title, scraped_at 
                        FROM articles 
                        ORDER BY scraped_at DESC 
                        LIMIT 1
                    """)
                    latest_article = cursor.fetchone()

                    return {
                        'total_articles': total_articles,
                        'analyzed_articles': analyzed_articles,
                        'unanalyzed_articles': unanalyzed_articles,
                        'latest_article': latest_article
                    }

        except psycopg2.Error as e:
            print(f"❌ Грешка при извличане на статистики: {e}")
            return None

    def get_unanalyzed_articles(self, limit=10):
        """
        Връща неанализирани статии от базата данни

        Args:
            limit (int): Максимален брой статии за връщане (default: 10)

        Returns:
            list: Списък със статии в dict формат или празен списък
        """
        print(f"📋 Търсене на неанализирани статии (лимит: {limit})...")

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # SQL заявка за неанализирани статии
                    cursor.execute("""
                        SELECT id, url, title, content, author, published_date, 
                               content_length, scraped_at
                        FROM articles 
                        WHERE is_analyzed = FALSE 
                        ORDER BY scraped_at DESC 
                        LIMIT %s
                    """, (limit,))

                    # Превръщаме резултата в list of dictionaries
                    articles = cursor.fetchall()

                    # Конвертираме в обикновени dict-ове (по-лесно за работа)
                    result = []
                    for article in articles:
                        result.append({
                            'id': article['id'],
                            'url': article['url'],
                            'title': article['title'],
                            'content': article['content'],
                            'author': article['author'],
                            'published_date': article['published_date'],
                            'content_length': article['content_length'],
                            'scraped_at': article['scraped_at']
                        })

                    print(f"✅ Намерени {len(result)} неанализирани статии")
                    return result

        except psycopg2.Error as e:
            print(f"❌ Грешка при четене на статии: {e}")
            return []
        except Exception as e:
            print(f"❌ Неочаквана грешка: {e}")
            return []

    def mark_article_as_analyzed(self, article_id, analysis_summary=None):
        """
        Маркира статия като анализирана в базата данни

        Args:
            article_id (int): ID на статията за маркиране
            analysis_summary (str, optional): Кратко резюме на анализа

        Returns:
            bool: True ако успешно, False ако има грешка
        """
        print(f"✅ Маркиране на статия ID:{article_id} като анализирана...")

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Първо проверяваме дали статията съществува
                    cursor.execute("SELECT title FROM articles WHERE id = %s", (article_id,))
                    article = cursor.fetchone()

                    if not article:
                        print(f"❌ Статия с ID:{article_id} не съществува")
                        return False

                    # UPDATE заявка за маркиране като анализирана
                    cursor.execute("""
                        UPDATE articles 
                        SET is_analyzed = TRUE
                        WHERE id = %s
                    """, (article_id,))

                    # Проверяваме дали UPDATE-а е успешен
                    if cursor.rowcount == 1:
                        conn.commit()  # Запазваме промените
                        print(f"✅ Статия ID:{article_id} маркирана като анализирана")
                        return True
                    else:
                        print(f"⚠️ Статия ID:{article_id} не беше обновена")
                        return False

        except psycopg2.Error as e:
            print(f"❌ Грешка при маркиране на статия: {e}")
            return False
        except Exception as e:
            print(f"❌ Неочаквана грешка: {e}")
            return False

    def test_database_access(self):
        """
        Тестова функция - показва няколко статии от базата
        Полезно за проверка че всичко работи правилно
        """
        print("\n🧪 ТЕСТ НА DATABASE ACCESS")
        print("=" * 40)

        try:
            # Показваме статистики
            stats = self.get_database_stats()
            if stats:
                print("📊 Статистики:")
                print(f"   📰 Общо статии: {stats['total_articles']}")
                print(f"   ✅ Анализирани: {stats['analyzed_articles']}")
                print(f"   ⏳ Неанализирани: {stats['unanalyzed_articles']}")

                if stats['latest_article']:
                    title, date = stats['latest_article']
                    print(f"   📅 Най-нова: {title[:50]}... ({date})")

            # Показваме първите 3 неанализирани статии
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, title, content_length, scraped_at, url
                        FROM articles 
                        WHERE is_analyzed = FALSE 
                        ORDER BY scraped_at DESC 
                        LIMIT 3
                    """)

                    unanalyzed = cursor.fetchall()

                    if unanalyzed:
                        print(f"\n📋 Първи 3 неанализирани статии:")
                        for i, article in enumerate(unanalyzed, 1):
                            print(f"   {i}. ID:{article['id']} | {article['title'][:45]}...")
                            print(f"      📊 {article['content_length']} chars | {article['scraped_at']}")
                    else:
                        print("\n📋 Няма неанализирани статии")

            print("\n✅ Database тест успешен!")
            return True

        except Exception as e:
            print(f"\n❌ Database тест неуспешен: {e}")
            return False

    def test_full_workflow(self):
        """
        Тества пълния workflow: четене -> "анализ" -> маркиране
        ВНИМАНИЕ: Това е само тест, не прави истински анализ!
        """
        print("\n🔄 ТЕСТ НА ПЪЛЕН WORKFLOW")
        print("=" * 40)

        try:
            # Стъпка 1: Вземаме 1 неанализирана статия
            articles = self.get_unanalyzed_articles(limit=1)

            if not articles:
                print("📋 Няма неанализирани статии за тест")
                return False

            article = articles[0]
            print(f"\n📄 Избрана статия за тест:")
            print(f"   ID: {article['id']}")
            print(f"   Заглавие: {article['title'][:60]}...")
            print(f"   Дължина: {article['content_length']} символа")

            # Стъпка 2: "Симулираме" анализ (без да правим истински анализ)
            print(f"\n🤖 Симулиране на AI анализ...")
            print(f"   📝 Анализиране на съдържанието...")
            print(f"   🔍 Извличане на entities...")
            print(f"   📊 Изчисляване на sentiment...")

            # Стъпка 3: Маркираме като анализирана
            success = self.mark_article_as_analyzed(article['id'])

            if success:
                # Стъпка 4: Проверяваме дали наистина е маркирана
                updated_stats = self.get_database_stats()
                print(f"\n📊 Обновени статистики:")
                print(f"   ⏳ Неанализирани: {updated_stats['unanalyzed_articles']}")
                print(f"   ✅ Анализирани: {updated_stats['analyzed_articles']}")

                print(f"\n🎉 Пълен workflow тест УСПЕШЕН!")
                return True
            else:
                print(f"\n❌ Пълен workflow тест НЕУСПЕШЕН")
                return False

        except Exception as e:
            print(f"\n❌ Грешка в workflow тест: {e}")
            return False


# Тестова функция за проверка
def main():
    """
    Основна функция за тестване на PostgreSQL Reader
    """
    print("=== POSTGRESQL READER ТЕСТ ===")

    try:
        # Създаваме reader
        reader = PostgreSQLReader()

        # Основен тест
        basic_success = reader.test_database_access()

        if not basic_success:
            print("\n❌ Основният тест се провали")
            return

        # Тестваме новите методи
        print("\n" + "=" * 50)
        print("🧪 ТЕСТВАНЕ НА НОВИТЕ МЕТОДИ")
        print("=" * 50)

        # Тест 1: get_unanalyzed_articles()
        print("\n1️⃣ ТЕСТ: get_unanalyzed_articles()")
        articles = reader.get_unanalyzed_articles(limit=2)

        if articles:
            print(f"✅ Намерени {len(articles)} неанализирани статии:")
            for i, article in enumerate(articles, 1):
                print(f"   {i}. ID:{article['id']} - {article['title'][:50]}...")
        else:
            print("📋 Няма неанализирани статии")

        # Тест 2: Пълен workflow (само ако има неанализирани статии)
        if articles:
            print(f"\n2️⃣ ТЕСТ: Пълен workflow")
            workflow_success = reader.test_full_workflow()

            if workflow_success:
                print("\n🎉 Всички тестове УСПЕШНИ!")
                print("\n💡 PostgreSQL Reader е готов за интеграция с AI анализа!")
                print("\n🚀 Следващи стъпки:")
                print("   1. Интеграция с crypto_analyzer.py")
                print("   2. Създаване на analysis workflow")
                print("   3. Настройка на база данни 'Б' за резултати")
            else:
                print("\n❌ Workflow тест неуспешен")
        else:
            print(f"\n⏭️ Прескачам workflow тест (няма неанализирани статии)")
            print("\n💡 За да тестваш workflow:")
            print("   1. Добави нови статии със scraper-а")
            print("   2. Стартирай отново postgres_reader.py")

    except Exception as e:
        print(f"\n❌ Критична грешка: {e}")
        print("\n🔧 Възможни решения:")
        print("   1. Провери дали PostgreSQL сървърът работи")
        print("   2. Провери дали базата данни 'crypto_news' съществува")
        print("   3. Провери username/password credentials")


if __name__ == "__main__":
    main()
