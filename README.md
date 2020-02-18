# show_alliance

Генератор видео-мультфильмов на основе сведений, загруженных с серверов CCP, zKillboard и распакованных из Static ESI CCP.

*Результат работы генератора*

[![GF Company eveonline](https://img.youtube.com/vi/Yyw3nRLmW6Y/0.jpg)](https://www.youtube.com/watch?v=Yyw3nRLmW6Y "GF Company eveonline")

Для изготовления мультфильма понадобится Python, [статический ESI](https://developers.eveonline.com/resource/resources), [генератор видео](https://code.google.com/archive/p/showteamwork/) show-team-work, подключение к Internet и терпение на несколько суток работы ЭВМ. Скорость выполнения скрипта напрямую зависит от ограничений, которые выставляют сервера CCP и zKillboard при скачивании данных. Мне удалось экспериментально выяснить, что при соблюдении [всех условий](https://github.com/zKillboard/zKillboard/wiki/API-(Killmails))  интервал отдачи .json документов серверами невозможно установить менее 2 сек, иначе подключения начинают отвергаться и ip адрес на некоторое время уходит в бан. Таким образом данные для 1.5-годовалого альянса GF-Company скачивались около 5 суток. В корне репозитория имеется bath-скрипт, с помощью которого можно автоматически перезапускать python-скрипт, если подключения к серверам начинают рваться (однако коды завершений не проверялись, поэтому надо следить за тем, чтобы скрипт не начал бесконечно перезапускаться скачав всю имеющуюся информацию).

Ссылки по теме:
* Простейший интерфейс для получения данных: https://esi.evetech.net/ui/#/
* Статический набор данных ESI: https://developers.eveonline.com/resource/resources
* Интерфейс борды: https://github.com/zKillboard/zKillboard/wiki/API-(Killmails)
* Документация: https://eveonline-third-party-documentation.readthedocs.io/en/latest/sso/index.html
* Вот здесь раньше можно было создать API Key: https://community.eveonline.com/support/api-key/update
* Но при нажатии на кнопку Submit перенаправляют сюда: https://developers.eveonline.com/blog/article/a-eulogy-for-xml-crest и извиняются за то, что XML API Key больше не работают.
* Вот здесь на русском написано почему это отключили и как с этим теперь жить дальше: https://forums.eveonline.com/t/xml-crest-esi/78590