# Datamatrix Storage Server

Приложение для обработки и хранения данных о выпущенных и промаркированных продуктов.

[[_TOC_]]

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


### MSI сборка

Для сборки *msi* файла, в разделе **Run and Debug** выберете **Build MSI** и нажмите **Start Debug** (либо используйте запуск через **F5**). 
После чего в проекте по адресу `src\build_tools\build_msi` появится *msi* файл, позволяющий выполнить установку приложения в систему.

*Альтернативный вариант:* находясь в папке `build_tools` выполнить команду

 ```bash
 python buildapp.py --msi
 ```
