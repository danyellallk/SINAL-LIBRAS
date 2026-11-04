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

## Primeiro classificador experimental (PyTorch)

O arquivo `train_sequence.py` implementa uma rede GRU bidirecional pequena para classificar **sinais isolados** a partir da sequência de pontos. Não é um tradutor de Libras e não deve ser apresentado como tal.

Instale Python e PyTorch em um ambiente de treinamento (por exemplo, Google Colab gratuito, se estiver disponível para sua conta). Em seguida, envie o JSONL preparado e execute:

```bash
pip install -r training/requirements.txt
python training/train_sequence.py training/prepared_dataset.jsonl --output training/model
```

A saída inclui:
- `sinal_libras_gru.pt`: pesos do protótipo;
- `classes.json`: nomes das classes;
- `metrics.json`: quantidade de exemplos e acurácia de validação/teste, quando houver dados.

O script exige ao menos duas classes no grupo de treino e exemplos de validação. Se a divisão por sinalizador não gerar os grupos necessários, reúna dados de mais pessoas sinalizadoras. Não mova gravações da mesma pessoa entre treino e teste apenas para fazer o script funcionar.

**Atenção:** poucos vídeos podem gerar acurácia enganosa e sobreajuste. O resultado é somente um experimento inicial, não um sistema pronto para uso. Avaliação séria requer mais sinalizadores, variantes regionais, contexto, expressões faciais e revisão linguística por pessoas surdas fluentes em Libras. Não use vídeos sem consentimento e licença que permita treinamento.
