from sentiment_analyzer import SentimentAnalyzer
from entity_analyzer import EntityAnalyzer
from text_summarizer import TextSummarizer


class CryptoAnalyzer:
    def __init__(self):
        print("=== ИНИЦИАЛИЗИРАНЕ НА CRYPTO ANALYZER ===")

        # Инициализираме всички компоненти
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_analyzer = EntityAnalyzer()
        self.text_summarizer = TextSummarizer()

        print("Всички модели са заредени!")

    def analyze_crypto_text(self, text):
        """Прави пълен анализ на криптовалутен текст"""
        print("Започвам пълен анализ...")

        original_word_count = self._count_words(text)
        print(f"Оригинален текст: {original_word_count} думи")

        # СТЪПКА 1: Решаваме дали да правим summarization
        text_for_sentiment = text
        summarization_info = {'used': False}

        if self.text_summarizer.should_summarize(text):
            print("Текстът е дълъг - правя резюме за sentiment анализ...")

            summary_result = self.text_summarizer.summarize(text)

            if summary_result['success']:
                text_for_sentiment = summary_result['summary']
                summarization_info = {
                    'used': True,
                    'original_words': summary_result['original_word_count'],
                    'summary_words': summary_result['summary_word_count'],
                    'compression_ratio': summary_result['compression_ratio'],
                    'processing_time': summary_result['processing_time'],
                    'summary_text': summary_result['summary']
                }

                # Добавяме fallback информация ако има
                if 'method' in summary_result:
                    summarization_info['method'] = summary_result['method']
                if 'note' in summary_result:
                    summarization_info['note'] = summary_result['note']

                print(f"Резюме готово: {summary_result['summary_word_count']} думи")
            else:
                print(f"Summarization неуспешно: {summary_result['reason']}")
                print("Използвам оригиналния текст за анализ")
                summarization_info['failed'] = True
                summarization_info['error'] = summary_result['reason']
        else:
            print("Текстът е кратък - директен анализ без резюме")

        # СТЪПКА 2: Sentiment анализ (на резюме или оригинал)
        print("Правя sentiment анализ...")
        sentiment_result = self.sentiment_analyzer.analyze(text_for_sentiment)

        # СТЪПКА 3: Entity анализ (винаги на оригиналния текст)
        print("Правя entity анализ...")
        entities_result = self.entity_analyzer.extract_entities(text)

        # СТЪПКА 4: Комбинираме резултатите
        full_analysis = {
            'text_info': {
                'original_length': original_word_count,
                'analyzed_length': self._count_words(text_for_sentiment),
                'preview': text[:150] + "..." if len(text) > 150 else text
            },
            'summarization': summarization_info,
            'sentiment': {
                'label': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence'],
                'analyzed_text_preview': text_for_sentiment[:100] + "..." if len(
                    text_for_sentiment) > 100 else text_for_sentiment
            },
            'entities': entities_result,
            'summary': self._generate_summary(sentiment_result, entities_result, summarization_info)
        }

        return full_analysis

    def _count_words(self, text):
        """Помощна функция за броене на думи"""
        return len(text.split())

    def _generate_summary(self, sentiment, entities, summarization_info):
        """Генерира кратко резюме на анализа"""
        # Броим entities
        total_entities = sum(len(items) for items in entities.values())
        crypto_count = len(entities['crypto_related'])
        person_count = len(entities['persons'])

        summary = f"Sentiment: {sentiment['sentiment']} ({sentiment['confidence']:.2f}). "
        summary += f"Намерени {total_entities} entities"

        if crypto_count > 0:
            summary += f", включително {crypto_count} crypto-related"
        if person_count > 0:
            summary += f", {person_count} persons"

        # Добавяме информация за summarization
        if summarization_info['used']:
            compression = summarization_info['compression_ratio']
            summary += f". Текст съкратен {compression}:1"

        return summary


# Тест
if __name__ == "__main__":
    analyzer = CryptoAnalyzer()
    print("CryptoAnalyzer готов за използване!")
    print("Компоненти:")
    print("- SentimentAnalyzer")
    print("- EntityAnalyzer")
    print("- TextSummarizer")
    print(f"\nSummarization лимит: {analyzer.text_summarizer.min_words_for_summary}+ думи")