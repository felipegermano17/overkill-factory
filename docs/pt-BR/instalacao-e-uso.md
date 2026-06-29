# Instalação e uso

Da raiz do repo: `python -m pip install ./factory`, depois `factoryctl doctor` e `factoryctl run minimal`. Para desenvolvimento: entrar em `factory/`, rodar `python -m unittest discover -s tests -p "test_*.py" -q`, `python scripts/factoryctl.py doctor` e `python scripts/factoryctl.py run minimal`. Para docs: `python -m pip install "./factory[docs]"` e `python -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site`.

## Regra principal

A fábrica deve facilitar confiança. Se algo não foi provado, deve ser dito como pendente. Se algo é reparável pela fábrica, não deve virar pergunta para o operador. Se exige decisão humana real, o gerente deve apresentar contexto, opções, consequências, recomendação e próximo passo.
