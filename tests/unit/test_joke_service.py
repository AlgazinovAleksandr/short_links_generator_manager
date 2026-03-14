import pytest
from unittest.mock import patch, mock_open
from src.services.joke_service import get_random_joke, SEPARATOR


SAMPLE_JOKES_CONTENT = """
Однажды ты спросишь, что для меня на 1 месте - ты или программирование. Я отвечу, что программирование, а ты уйдешь, так и не узнав, что ты у меня на 0 месте.
ILOVEPIZZA
Как показал последний соцопрос, для 62 процентов российских мужчин понятия 'отпуск' и 'запой' тождественны. Остальные просто не знают смысла слова 'тождественны'.
ILOVEPIZZA
Слабаки ставят разделители наподобие каких-нибудь тильд, точек с запятой там, нескольких тире. И только те кто преисполнился в своем познании-сознании ставят...
ILOVEPIZZA
Недавно производители программного обеспечения США сделали просто ошеломляющее открытие: Оказывается, скорость чтения россиян в тысячи раз превышает скорость чтения американцев. Это стало очевидно после подсчета миллисекунд, за которые среднестатистический россиянин успевает прочитать пользовательское (лицензионное) соглашение и нажать кнопку «СОГЛАСЕН»…
ILOVEPIZZA
There lived a certain man in Russian long ago, he was big and strong, in his eyes a flaming glow. Most people look at him with terror and with fear..."""


def test_get_random_joke_returns_string():
    with patch("src.services.joke_service.JOKES_FILE") as mock_path:
        mock_path.read_text.return_value = SAMPLE_JOKES_CONTENT
        joke = get_random_joke()
    assert isinstance(joke, str)
    assert len(joke) > 0

def test_get_random_joke_is_one_of_expected():
    with patch("src.services.joke_service.JOKES_FILE") as mock_path:
        mock_path.read_text.return_value = SAMPLE_JOKES_CONTENT
        joke = get_random_joke()
    # очень красиво, I LIKE THAT 我喜欢这个
    expected = ["Однажды ты спросишь, что для меня на 1 месте - ты или программирование. Я отвечу, что программирование, а ты уйдешь, так и не узнав, что ты у меня на 0 месте.", 
                "Как показал последний соцопрос, для 62 процентов российских мужчин понятия 'отпуск' и 'запой' тождественны. Остальные просто не знают смысла слова 'тождественны'.", 
                "Слабаки ставят разделители наподобие каких-нибудь тильд, точек с запятой там, нескольких тире. И только те кто преисполнился в своем познании-сознании ставят...",
                "Недавно производители программного обеспечения США сделали просто ошеломляющее открытие: Оказывается, скорость чтения россиян в тысячи раз превышает скорость чтения американцев. Это стало очевидно после подсчета миллисекунд, за которые среднестатистический россиянин успевает прочитать пользовательское (лицензионное) соглашение и нажать кнопку «СОГЛАСЕН»…",
                "There lived a certain man in Russian long ago, he was big and strong, in his eyes a flaming glow. Most people look at him with terror and with fear..."]
    assert joke in expected

def test_get_random_joke_empty_file():
    with patch("src.services.joke_service.JOKES_FILE") as mock_path:
        mock_path.read_text.return_value = "ILOVEPIZZA\nILOVEPIZZA"
        joke = get_random_joke()
    assert joke == "No jokes available right now."

def test_separator_constant():
    assert SEPARATOR == "ILOVEPIZZA"
