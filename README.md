# ZCompose

Build & Run multiple Zephyr applications together.
Currently only focused (and tested) on native_sim on linux.

Inspired by docker-compose:

- Declarative ZCompose file
    - Zephyr applications
    - Networks to connect the applications
- `zcompose show`: show parsed ZCompose file
- `zcompose up/down`: bring network interfaces up/down
- `zcompose build`: build all applications in ZCompose file
- `zcompose run`: run all applications in ZCompose file

[![asciicast](https://asciinema.org/a/xR3Wqix91iI3TdaS9SKNWxAY8.svg)](https://asciinema.org/a/xR3Wqix91iI3TdaS9SKNWxAY8)
