"""
Standard Elo rating system, same family of algorithm used by chess
ratings and by LMSYS Chatbot Arena for ranking LLMs head-to-head.
"""

K_FACTOR = 32


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))


def update_ratings(rating_a: float, rating_b: float, result: str):
    """
    result: "a" -> A wins, "b" -> B wins, "tie" -> draw
    Returns (new_rating_a, new_rating_b)
    """
    expected_a = expected_score(rating_a, rating_b)
    expected_b = expected_score(rating_b, rating_a)

    if result == "a":
        score_a, score_b = 1.0, 0.0
    elif result == "b":
        score_a, score_b = 0.0, 1.0
    else:  # tie
        score_a, score_b = 0.5, 0.5

    new_rating_a = rating_a + K_FACTOR * (score_a - expected_a)
    new_rating_b = rating_b + K_FACTOR * (score_b - expected_b)
    return round(new_rating_a, 2), round(new_rating_b, 2)
