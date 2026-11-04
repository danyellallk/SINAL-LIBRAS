# Preparação do conjunto SINAL LIBRAS

Esta etapa transforma a exportação JSON do app em JSONL com formato consistente para experimentos futuros.

## Como usar

1. Exporte o conjunto JSON no app SINAL LIBRAS.
2. Transfira o arquivo para esta pasta no repositório ou para o ambiente de treinamento.
3. Execute:

```bash
python training/prepare_dataset.py sinal-libras-conjunto-de-exemplos.json --output training/prepared_dataset.jsonl
```

Para incluir rascunhos (somente para inspeção, não recomendado para treino):

```bash
python training/prepare_dataset.py exemplos.json --include-drafts
```

O script usa somente a biblioteca padrão do Python. Gera um arquivo JSONL e `dataset_summary.json`.

## Formato padronizado

Cada registro contém rótulo, contexto, pseudônimo do sinalizador, divisão por pessoa e 12 (ou mais, conforme a exportação) quadros. Cada quadro contém:
- mão esquerda e direita: 21 pontos cada;
- corpo: 33 pontos;
- rosto: 15 pontos selecionados;
- coordenadas x/y/z e valor de visibilidade/presença.

Pontos ausentes são preenchidos com zero e distinguíveis pelo quarto valor (máscara de presença/visibilidade).

## Cuidados

- O script não treina rede neural e não traduz vídeos.
- A situação "revisado" e a confirmação de autorização são declarações do usuário; o script não as verifica.
- A divisão é feita pelo pseudônimo para impedir que gravações da mesma pessoa caiam em grupos diferentes. Com poucos sinalizadores, treino/validação/teste podem ficar desequilibrados.
- Use apenas dados cujo uso em treinamento esteja autorizado pela licença e pelo consentimento aplicável.
- Para reconhecer frases, será necessário um conjunto maior, contínuo e linguisticamente anotado, validado por pessoas surdas fluentes em Libras.
