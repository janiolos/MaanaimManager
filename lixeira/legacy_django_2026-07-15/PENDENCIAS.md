## Pendência

`data/static` não foi movido porque o diretório está com ownership `nobody:nobody` e sem permissão de escrita para o usuário atual.

Se quiser concluir essa parte depois, execute a partir de uma sessão com privilégio real de root:

```bash
mv data/static lixeira/legacy_django_2026-07-15/data/
```
