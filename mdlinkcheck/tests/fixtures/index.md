# Fixture index

Рабочая локальная ссылка: [существует](./exists.md).

Сломанная локальная ссылка: [нет такого файла](./missing.md).

Референсная ссылка: [пример][ref].

Автоссылка: <https://example.com/ok>.

Картинка: ![логотип](./img/logo.png).

Битая картинка: ![нет](./img/absent.png).

Ссылка на файл по абсолютному пути: [file](file:///tmp/mdlinkcheck-absent.md).

Пропускаемые: [почта](mailto:user@example.com), [телефон](tel:+70000000000),
[якорь](#fixture-index).

Ссылка внутри блока кода не должна попасть в результат:

```markdown
[код](./inside-code-block.md)
```

[ref]: https://example.com/reference
