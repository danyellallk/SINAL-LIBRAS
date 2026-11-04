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

## Investigar o dataset LIBRAS-EQT-UECE

A documentação do dataset informa que ele contém vídeos isolados e contínuos organizados por glossas, partições de anotações `.npy`, quadros processados e um pacote separado de landmarks em CSV/JSON. Consulte [DATA_SOURCES.md](DATA_SOURCES.md) para licença e limitações.

Depois de obter legalmente o pacote `Landmarks.zip` em um ambiente de treinamento, rode:

```bash
python training/inspect_libras_eqt.py Landmarks.zip --limit 25
```

O inspetor lista extensões e tamanhos, mostra cabeçalhos CSV/JSON/NPY e pequenas amostras sem extrair o arquivo inteiro. Ele não treina nem converte o dataset. O notebook também executa `audit_libras_eqt_npy.py`, que percorre os 10.682 NPY dentro do ZIP sem extraí-los, conta glossas e pastas de informantes, resume dimensões/quadros/tipos numéricos, verifica valores não finitos e calcula estatísticas por coordenada (mínimo, máximo, média e proporção de zeros). **Não passe os arquivos externos diretamente ao classificador atual:** primeiro precisamos confirmar o esquema de coordenadas, os rótulos/glossas, as frases alinhadas e as partições oficiais. A auditoria grava `AUDITORIA_DETALHADA_COMPLETA.json` com todos os detalhes e imprime um resumo compacto no notebook, para facilitar o envio sem cortes. Preserve as divisões oficiais por participante para evitar vazamento entre treino e teste.

O classificador GRU deste repositório continua sendo apenas uma experiência de classificação de sequências rotuladas, não um tradutor contínuo de frases. O pacote contínuo da UECE pode permitir uma próxima etapa mais adequada, mas será necessário criar e validar um adaptador e um modelo de sequência para tradução.


## Modelo experimental de sequência contínua (CTC)

Foi adicionado `train_continuous_ctc.py`, um segundo experimento diferente do classificador de sinais isolados. Ele usa uma GRU **unidirecional causal** com CTC para aprender a emitir tokens de texto em ordem temporal. O estado recorrente pode ser mantido entre blocos durante a inferência.

### Formato JSONL esperado

Cada linha deve ser um objeto com:
- `sample_id`: identificador da gravação;
- `signer_id`: pseudônimo estável do participante;
- `split`: `train`, `dev` ou `test`;
- `portuguese_text`: frase-alvo em português;
- `frames`: matriz temporal de vetores numéricos. Cada quadro deve ter sempre a mesma dimensão (por exemplo, 318 para 106 landmarks x 3 coordenadas, ou 360 para o vetor deste app).

Exemplo ilustrativo (valores fictícios, não é dado real de Libras):

```json
{"sample_id":"exemplo-001","signer_id":"pessoa-a","split":"train","portuguese_text":"bom dia","frames":[[0.0,0.1,0.2],[0.1,0.2,0.3]]}
```

O exemplo acima é apenas esquemático e não pode ser treinado porque as dimensões são pequenas; cada quadro real deve ter 318 ou 360 valores conforme a fonte.

### Treinar

Depois de converter e validar os landmarks reais para o formato acima:

```bash
pip install -r training/requirements.txt
python training/train_continuous_ctc.py training/continuous_dataset.jsonl --output training/continuous_model
```

### Inferência em blocos

Com um checkpoint treinado e um JSON contendo `frames`:

```bash
python training/infer_continuous_stream.py training/continuous_model/sinal_libras_continuous_ctc.pt video_landmarks.json --chunk-frames 8
```

A inferência preserva o estado da GRU entre blocos e emite texto provisório à medida que os quadros chegam. A saída ainda pode mudar e o colapso CTC simples não faz revisão linguística. O script demonstra o fluxo técnico de processamento incremental, mas não está integrado à câmera do aplicativo.

### Limitações essenciais

- O CTC aqui é uma linha de pesquisa experimental para alinhar uma sequência visual a tokens de português; não garante gramática natural, contexto, regionalismos ou interpretação correta. O script também descarta amostras cujo número de quadros seja insuficiente para alinhar os tokens pela regra CTC.
- O dataset UECE tem vídeos contínuos e anotações ao nível da sequência, mas precisamos confirmar os nomes e a organização exata dos arquivos de landmarks e alinhar cada sequência ao texto correto antes de gerar o JSONL.
- O dataset tem 55 sinais isolados e 123 sequências contínuas; é um corpus inicial pequeno para um tradutor geral. A documentação científica relata 5.335 gravações e uma divisão por participante/item que deve ser respeitada.
- As informações consultadas indicam CC BY-NC 4.0, que restringe o uso comercial e exige atribuição. Antes de treinar, confira o conteúdo integral do `LICENSE.txt` da versão exata e as demais permissões aplicáveis. Não usar para lançar ou monetizar uma versão comercial sem autorização/licença adequada.
- O modelo não foi treinado neste commit: nenhum corpus real foi baixado ou convertido automaticamente.


Para o corpus UECE, respeite as partições oficiais train/dev/test. O artigo descreve identificadores de informante locais por item; ao validar vazamento, forme `signer_id` como identificador do item + identificador local do informante, e não trate rótulos locais iguais em itens diferentes como necessariamente a mesma pessoa física. A partição publicada garante separação de execuções por item, mas o artigo alerta que não garante participantes físicos inteiramente inéditos entre todas as partições.


### Auditar o arquivo antes de treinar

Execute primeiro o validador, para detectar dimensão incorreta, valores inválidos, IDs duplicados e participantes misturados entre partições:

```bash
python training/validate_continuous_jsonl.py training/continuous_dataset.jsonl --expected-dim 318
```

Use `--expected-dim 360` apenas se os vetores vierem do extrator do aplicativo. Para o corpus UECE, a documentação descreve 106 landmarks com coordenadas x/y/z, portanto 318 valores por quadro. O validador rejeita dimensões desconhecidas (incluindo 126, que corresponde apenas às mãos) e detecta mistura de dimensões no mesmo JSONL. O treinador CTC também repete as verificações de IDs, valores finitos e esquema antes de iniciar, para evitar treino acidental com dados incompatíveis. O validador não confirma que o vídeo e a tradução estão corretamente alinhados; isso exige auditoria de metadados e revisão linguística.


## Auditoria do corpus UECE no celular (Google Colab)

Para evitar baixar quase 774 MB diretamente no Android, há um notebook que faz o download diretamente no ambiente Colab, confere o MD5 oficial e inspeciona o ZIP sem extrair todos os arquivos:

[ Abrir notebook de auditoria no GitHub ](https://github.com/danyellallk/SINAL-LIBRAS/blob/main/training/SINAL_LIBRAS_Auditoria_UECE.ipynb)

No GitHub, abra o notebook e escolha **Open in Colab** (ou baixe o arquivo e envie para o Colab). Execute as células em ordem. O notebook não treina a IA; ele apenas produz o inventário técnico que precisamos para criar o conversor sem adivinhar o formato dos dados. O pacote tem aproximadamente 773,6 MB e pode levar algum tempo para baixar.


## Inspecionar o pacote contínuo UECE sem extração

O pacote `Libras-EQT-UECE-T.zip` é muito maior que o pacote de landmarks. Para descobrir a estrutura real das anotações sem extrair dezenas de GB, use:

```bash
python training/inspect_uece_continuous_package.py Libras-EQT-UECE-T.zip --samples 50
```

O script lista os diretórios e arquivos candidatos a anotações, contabiliza extensões e lê somente cabeçalhos NPY. Ele não extrai o ZIP, não carrega arrays e não executa pickle. Arquivos NPY com dtype de objeto são apenas identificados e não desserializados.

**Não criamos ainda o conversor UECE → JSONL.** Primeiro precisamos conferir os identificadores de gravação nas anotações e provar que cada sequência de landmarks corresponde à sequência de glosas e ao texto em português corretos. Só então os pares poderão entrar no treinamento CTC.


### Inspeção estática das anotações NPY

O README oficial v4 mostra as anotações contínuas em `annotations/train.npy`, `annotations/dev.npy` e `annotations/test.npy`. Se o cabeçalho indicar dtype de objeto, o script abaixo permite examinar os opcodes do payload pickle sem desserializar o objeto:

```bash
python training/inspect_npy_pickle_static.py Libras-EQT-UECE-T.zip --member "Libras-EQT-UECE-T/annotations/train.npy"
```

Substitua o caminho interno pelo nome exato mostrado pelo inventário do ZIP. O script apenas analisa a estrutura do pickle com `pickletools`; não usa `pickle.load`, `numpy.load(..., allow_pickle=True)` nem executa objetos. A saída pode revelar classes/referências globais e a estrutura de serialização, mas não é um conversor e não recupera valores de anotação. Nunca execute pickle de origem externa.


## Inspecionar o ZIP contínuo de 35,6 GB sem baixá-lo inteiro

Foi adicionado `inspect_uece_remote_zip.py`. Ele consulta os metadados do Zenodo e tenta ler o diretório central do ZIP e apenas os primeiros bytes dos NPY usando requisições HTTP Range. Assim, o ambiente Colab pode inspecionar a estrutura sem armazenar o pacote inteiro. O servidor precisa aceitar HTTP Range; se não aceitar, o script para sem iniciar um download completo.

No Colab:

```python
!pip -q install remotezip requests
!python training/inspect_uece_remote_zip.py --max-samples 80
```

O script não desserializa NPY de objeto, não executa pickle e limita a leitura de cada membro. O resultado identifica nomes, tamanhos, extensões, candidatos a anotações e cabeçalhos NPY. Isso ainda não é a tradução: depois de conhecer o esquema real, precisamos decodificar os metadados com segurança e validar a correspondência entre IDs, glossas e frases em português.
