from transformers import pipeline
import time


class TextSummarizer:
    def __init__(self):
        print("Зареждане на summarization модел...")
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        print("Summarization модел зареден!")

        # Опростени и реалистични лимити
        self.min_words_for_summary = 350  # Под това не правим резюме
        self.max_input_words = 600  # Лимит за входящ текст
        self.target_summary_words = 275  # Цел за резюме (250-300 думи)

    def _count_words(self, text):
        """Брои думите в текста"""
        return len(text.split())

    def _prepare_text_for_bart(self, text):
        """Подготвя текста за BART (ако е твърде дълъг)"""
        words = text.split()
        if len(words) <= self.max_input_words:
            return text

        # За много дълги текстове: първите 60% + последните 40%
        first_part_size = int(self.max_input_words * 0.6)
        last_part_size = self.max_input_words - first_part_size

        first_part = words[:first_part_size]
        last_part = words[-last_part_size:]

        prepared_text = " ".join(first_part) + " ... " + " ".join(last_part)
        print(f"Текст подготвен за BART: {len(words)} → {len(prepared_text.split())} думи")
        return prepared_text

    def should_summarize(self, text):
        """Проверява дали текстът се нуждае от резюме"""
        word_count = self._count_words(text)
        return word_count >= self.min_words_for_summary

    def summarize(self, text):
        """Създава резюме на текста"""
        word_count = self._count_words(text)

        if not self.should_summarize(text):
            return {
                'success': False,
                'reason': f'Текстът е твърде кратък ({word_count} думи). Минимум за резюме: {self.min_words_for_summary} думи. Използвай директен анализ.',
                'original_text': text,
                'original_word_count': word_count,
                'recommendation': 'direct_analysis'
            }

        try:
            # Подготвяме текста за BART
            prepared_text = self._prepare_text_for_bart(text)

            # Правим summarization с подобрени параметри
            print(f"Създаване на резюме от {word_count} думи...")
            start_time = time.time()

            # Оптимизирани BART параметри за 250-300 думи резюме
            summary_result = self.summarizer(
                prepared_text,
                max_length=450,  # ~300-350 думи резултат
                min_length=320,  # ~220-250 думи резултат
                do_sample=False,  # Детерминистичен резултат
                length_penalty=1.0  # Без penalty за дължина
            )

            summary_text = summary_result[0]['summary_text']
            summary_time = round(time.time() - start_time, 2)
            summary_word_count = self._count_words(summary_text)

            print(f"Резюме готово: {summary_word_count} думи ({summary_time}s)")

            return {
                'success': True,
                'summary': summary_text,
                'original_word_count': word_count,
                'summary_word_count': summary_word_count,
                'compression_ratio': round(word_count / summary_word_count, 1),
                'processing_time': summary_time
            }

        except Exception as e:
            print(f"Грешка при summarization: {e}")

            # Опростен fallback метод - взимаме първите изречения
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if len(sentences) >= 3:
                # Взимаме първите няколко изречения до достигане на ~275 думи
                fallback_text = ""
                word_count_so_far = 0

                for sentence in sentences:
                    sentence_words = self._count_words(sentence)
                    if word_count_so_far + sentence_words <= self.target_summary_words:
                        fallback_text += sentence + ". "
                        word_count_so_far += sentence_words
                    else:
                        break

                fallback_word_count = self._count_words(fallback_text)

                return {
                    'success': True,
                    'summary': fallback_text.strip(),
                    'original_word_count': word_count,
                    'summary_word_count': fallback_word_count,
                    'compression_ratio': round(word_count / fallback_word_count, 1),
                    'method': 'fallback_first_sentences',
                    'note': f'BART summarization неуспешна. Използвани първи изречения.'
                }
            else:
                return {
                    'success': False,
                    'reason': f'Summarization грешка: {str(e)}',
                    'original_text': text,
                    'original_word_count': word_count
                }


# Тест
if __name__ == "__main__":
    summarizer = TextSummarizer()
    print("TextSummarizer готов за използване!")
    print(f"Минимум думи за summarization: {summarizer.min_words_for_summary}")
    print(f"Максимум входящи думи: {summarizer.max_input_words}")
    print(f"Цел за резюме: {summarizer.target_summary_words} думи")