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


# Тестова функция за проверка
def main():
    """
    Основна функция за тестване на PostgreSQL Reader
    """
    print("=== POSTGRESQL READER ТЕСТ ===")

    try:
        # Създаваме reader
        reader = PostgreSQLReader()

        # Тестваме функционалността
        success = reader.test_database_access()

        if success:
            print("\n🎉 PostgreSQL Reader работи отлично!")
            print("\n💡 Следващи стъпки:")
            print("   1. Добавяне на метод get_unanalyzed_articles()")
            print("   2. Добавяне на метод mark_article_as_analyzed()")
        else:
            print("\n❌ Има проблеми с PostgreSQL Reader")

    except Exception as e:
        print(f"\n❌ Критична грешка: {e}")
        print("\n🔧 Възможни решения:")
        print("   1. Провери дали PostgreSQL сървърът работи")
        print("   2. Провери дали базата данни 'crypto_news' съществува")
        print("   3. Провери username/password credentials")


if __name__ == "__main__":
    main()
