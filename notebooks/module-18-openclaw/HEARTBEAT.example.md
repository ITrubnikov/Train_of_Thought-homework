tasks:
- name: eth-watch
  interval: 2h
  prompt: "Проверь курс ETH/USD через web_fetch по https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd. Если курс изменился больше чем на 5% с прошлой проверки (прошлое значение держи в MEMORY.md) — напиши мне. Иначе ответь HEARTBEAT_OK."
- name: disk-space
  interval: 6h
  prompt: "Проверь свободное место на диске (df -h). Если меньше 10% — предупреди меня, иначе HEARTBEAT_OK."
