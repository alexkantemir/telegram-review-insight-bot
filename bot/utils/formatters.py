from bot.schemas.review_analysis import ReviewAnalysis

SENTIMENT_LABELS: dict[str, str] = {
    "positive": "положительная",
    "neutral": "нейтральная",
    "negative": "негативная",
    "mixed": "смешанная",
    "none": "нет данных",
}

REVIEW_TYPE_LABELS: dict[str, str] = {
    "complaint": "жалоба",
    "gratitude": "благодарность",
    "suggestion": "предложение",
    "question": "вопрос",
    "repeated_claim": "повторное обращение",
}

TOPIC_LABELS: dict[str, str] = {
    "delivery": "доставка",
    "product_quality": "качество товара",
    "support": "поддержка",
    "price": "цена",
    "website": "сайт",
    "return": "возврат",
    "assortment": "ассортимент",
    "communication": "коммуникация",
    "other": "другое",
    "none": "нет данных",
}


def _label(mapping: dict[str, str], value: str) -> str:
    return mapping.get(value, value)


def format_analysis_response(analysis: ReviewAnalysis) -> str:
    escalation = "Да" if analysis.escalation_required else "Нет"
    return (
        "<b>Анализ отзыва</b>\n\n"
        f"<b>Тональность:</b> {_label(SENTIMENT_LABELS, analysis.sentiment.value)}\n"
        f"<b>Тип отзыва:</b> {_label(REVIEW_TYPE_LABELS, analysis.review_type.value)}\n"
        f"<b>Тема:</b> {_label(TOPIC_LABELS, analysis.topic.value)}\n"
        f"<b>Краткое резюме:</b> {analysis.short_summary}\n"
        f"<b>Требуется эскалация:</b> {escalation}\n\n"
        f"<b>Предложенный ответ:</b>\n{analysis.suggested_reply}"
    )


def format_stats(stats: dict) -> str:
    sentiment_lines = "\n".join(
        f"  • {_label(SENTIMENT_LABELS, key)}: {value}"
        for key, value in stats["sentiment_distribution"].items()
    )
    topic_lines = "\n".join(
        f"  • {_label(TOPIC_LABELS, key)}: {value}"
        for key, value in stats["topic_distribution"].items()
    )
    recurring_issues = stats["top_recurring_issues"]
    if recurring_issues:
        issues_lines = "\n".join(
            f"  • {_label(TOPIC_LABELS, issue['topic'])} — {issue['count']} раз"
            for issue in recurring_issues
        )
    else:
        issues_lines = "  • Выраженных повторяющихся проблем не выявлено"
    return (
        "<b>Статистика по отзывам</b>\n\n"
        f"<b>Всего отзывов:</b> {stats['total_reviews']}\n"
        f"<b>Эскалации:</b> {stats['escalation_count']}\n\n"
        f"<b>Распределение по тональности:</b>\n{sentiment_lines}\n\n"
        f"<b>Распределение по темам:</b>\n{topic_lines}\n\n"
        f"<b>Частые проблемы:</b>\n{issues_lines}"
    )


def format_last_reviews(reviews: list[dict]) -> str:
    if not reviews:
        return (
            "Отзывов пока нет. "
            "Отправьте текст отзыва обычным сообщением."
        )

    blocks: list[str] = ["<b>Последние отзывы</b>\n"]
    for item in reviews:
        escalation = "Да" if item["escalation_required"] else "Нет"
        blocks.append(
            f"#{item['id']} — {item['created_at']}\n"
            f"<b>Тональность:</b> {_label(SENTIMENT_LABELS, item['sentiment'])} | "
            f"<b>Тип:</b> {_label(REVIEW_TYPE_LABELS, item['review_type'])} | "
            f"<b>Тема:</b> {_label(TOPIC_LABELS, item['topic'])}\n"
            f"<b>Резюме:</b> {item['short_summary']}\n"
            f"<b>Эскалация:</b> {escalation}\n"
            f"<i>{item['raw_text'][:120]}{'…' if len(item['raw_text']) > 120 else ''}</i>\n"
        )
    return "\n".join(blocks)
