# Datamatrix Storage Server

## Сервер сбора данных со сканеров на линии выпуска.

Модуль представляет из себя программу,
которая при старте создаёт на локальной машине на фиксированном порту сервер.

В задачи сервера входит:

1. Регистрация сканеров в сети.
2. Взаимодействие с каждым сканером в отдельном потоке. [Протокол взаимодействия](./docs/protocol.md)
3. Сохранение архивных данных сканера в формате CSV-таблицы.

API Сервера:

- init_server:
- run_server:
- stop_server:

- connection_info:

- register_new_scanner:
- is_alive(scanner_id):
- set_scanner_settings(scanner_settings)

python setup_cx_freeze.py bdist_msi -d built_msi