# Fontes de dados e plano responsável de treinamento

Este documento define como obter exemplos para treinar o SINAL LIBRAS sem copiar vídeos de terceiros sem autorização.

## YouTube: material de ensino não é automaticamente dataset

Vídeos públicos do YouTube podem ser excelentes para estudar Libras e localizar especialistas, mas a publicação no YouTube não concede automaticamente permissão para baixar, extrair quadros, redistribuir ou usar o vídeo para treinamento. Os Termos do YouTube restringem download, reprodução e acesso automatizado, salvo autorização aplicável. Portanto, este projeto **não fará raspagem (scraping), download em massa nem extração automática de vídeos do YouTube**.

Uso permitido nesta etapa:
- assistir aos vídeos pelo próprio YouTube;
- identificar professores, intérpretes e pessoas surdas fluentes que possam colaborar;
- solicitar autorização escrita ao titular dos direitos e consentimento das pessoas filmadas;
- convidar colaboradores a enviar gravações próprias, com autorização documentada para treinamento.

Uma autorização deve esclarecer, no mínimo, uso para pesquisa/treinamento de IA, armazenamento, tratamento dos dados, divulgação de resultados e eventual uso futuro do modelo. Consentimento para aparecer em um vídeo não significa, por si só, autorização para treinar IA.

## Dataset público encontrado para avaliação

### LIBRAS-EQT-UECE (Zenodo, versão 4)

- Registro: https://zenodo.org/records/21398895
- DOI: 10.5281/zenodo.21398895
- Publicado em 16/07/2026.
- Arquivos anunciados: `Landmarks.zip` (773,6 MB), vídeos RGB (9,0 GB) e outro conjunto de vídeos (35,6 GB), total aproximado de 45,4 GB.
- Licença conferida diretamente no `LICENSE.txt` da versão v4: Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). Exige atribuição e proíbe uso comercial. Não usar em produto monetizado sem autorização/licença diferente dos titulares.
- A licença exige atribuição e **não permite uso comercial**. Antes de qualquer uso, conferir o README, a estrutura, as anotações, as condições de consentimento e se a tarefa/labels servem ao nosso objetivo.

Este dataset é uma opção para um experimento estritamente não comercial, respeitando a licença e citando os autores. Ele não deve ser usado em uma versão comercial ou monetizada sem uma autorização/licença diferente. A documentação científica descreve um pacote contínuo processado com partições de anotações `.npy` (train/dev/test), quadros e recursos. A auditoria realizada neste projeto confirmou que `Landmarks.zip` contém arrays `.npy` organizados em pastas por sinal/glossa e informante. Ainda não inspecionamos o conteúdo interno do pacote contínuo de 35,6 GB nem confirmamos como seus identificadores se relacionam com cada arquivo de landmarks. Isso o torna uma fonte promissora para pesquisar tradução contínua, mas ainda precisamos auditar o conteúdo e confirmar como as frases e glossas estão alinhadas. O arquivo de landmarks tem centenas de MB; não é adequado para baixar e treinar diretamente no celular Android.

## Outra fonte em avaliação — V-Librasil

Há uma cópia de dataset descrita no Hugging Face como 4.086 vídeos e 1.366 classes de sinais isolados, originada do portal V-Librasil/UFPE. A página consultada não apresenta uma licença clara para reutilização dos vídeos. **Não usar para treinamento** até confirmar diretamente com os titulares a licença, os direitos dos vídeos e a autorização para obras derivadas/treinamento.

## Estratégia técnica

1. Auditar licença, documentação, rótulos, consentimento e qualidade de cada dataset antes de baixar.
2. Começar com reconhecimento de sinais isolados para validar o pipeline; isso não equivale a traduzir frases contínuas.
3. Separar treino, validação e teste por pessoa sinalizadora, nunca misturando vídeos da mesma pessoa entre os grupos.
4. Validar rótulos e traduções com pessoas surdas e profissionais fluentes em Libras.
5. Evoluir para reconhecimento contínuo e tradução de frases, incluindo mãos, rosto, tronco, movimento, contexto e gramática.
6. Só então integrar um modelo ao app e testar a inferência contínua na câmera e em vídeos da galeria.

## Limites atuais

O repositório contém extração de landmarks e um classificador GRU experimental, mas ainda não tem um modelo treinado com dados reais nem um tradutor de frases. O classificador atual é para sinais isolados e requer um conjunto preparado, dependência PyTorch e ambiente de treinamento. O GitHub Pages apenas hospeda a interface; não executa treinamento pesado.

## Referências

- YouTube Terms of Service: https://www.youtube.com/t/terms
- LIBRAS-EQT-UECE v4: https://zenodo.org/records/21398895
- Licença CC BY-NC 4.0: https://creativecommons.org/licenses/by-nc/4.0/
- V-Librasil dataset card (licença ainda precisa ser confirmada): https://huggingface.co/datasets/ibmectech/v-librasil-raw


## Inspecionar o pacote de landmarks antes de converter

Depois de obter legalmente `Landmarks.zip` no ambiente de treinamento, examine os nomes, formatos, cabeçalhos NPY e pequenas amostras sem extrair todo o arquivo:

```bash
python training/inspect_libras_eqt.py Landmarks.zip --limit 25
```

O inspetor não executa arquivos serializados, não extrai o ZIP e não treina modelo. Ele serve para identificar a estrutura real dos dados antes de escrever um conversor específico. Não carregue arquivos `.npy` com `allow_pickle=True` de fontes não confiáveis.

**Importante:** os arquivos CSV/JSON do dataset externo ainda não são automaticamente compatíveis com `prepare_dataset.py` ou `train_sequence.py`. Não misture esses dados ao treino até mapear corretamente coordenadas, glossas, frases, identidade do participante e partições oficiais. A partição oficial por participante deve ser preservada quando disponível.

## Detalhes linguísticos confirmados na documentação científica

O artigo associado ao dataset descreve 178 itens: 55 sinais isolados e 123 sequências contínuas, com 5.335 gravações processadas. As amostras contínuas têm anotação ao nível da sequência: cada vídeo/sequência é associado a uma sequência ordenada de glosas e à tradução em português, sem fronteiras temporais manuais para cada glosa. Isso permite investigar treinamento fracamente supervisionado com CTC/atenção.

A representação descrita no artigo tem 106 landmarks por quadro (318 valores x/y/z): corpo, duas mãos e pontos faciais selecionados. Os landmarks são entregues em CSV/JSON. A documentação do Zenodo confirma que o pacote processado contém arquivos `.npy` de partição e imagens 256x256; o pacote Landmarks é separado.

**Implicação para o SINAL LIBRAS:** o caminho mais promissor é treinar uma sequência visual → texto em português, e não apenas classificar cada gesto como uma palavra. O novo protótipo CTC é um primeiro experimento causal para esse caminho, mas ainda depende de um conversor que mapeie os CSV/JSON reais aos pares de sequência e tradução.

Fontes:
- Artigo e descrição técnica do corpus: https://doi.org/10.1109/ACCESS.2026.3715086
- README do Zenodo: https://zenodo.org/records/21398895/preview/README.md?include_deleted=0
- Licença da versão 4: https://zenodo.org/records/21398895/preview/LICENSE.txt?include_deleted=0


## Inspeção do pacote contínuo (sem extração)

Foi criado `inspect_uece_continuous_package.py` para inventariar o pacote `Libras-EQT-UECE-T.zip`. O script lista diretórios, extensões, candidatos a arquivos de anotação e lê somente os cabeçalhos dos primeiros arquivos NPY. Ele não extrai o ZIP, não carrega matrizes e não executa pickle.

```bash
python training/inspect_uece_continuous_package.py Libras-EQT-UECE-T.zip --samples 50
```

O pacote tem aproximadamente 35,6 GB. Não é necessário nem recomendável baixá-lo no celular. Quando a inspeção for executada em um ambiente com espaço suficiente, precisamos comparar os IDs e a estrutura das anotações com os caminhos de landmarks. Só depois dessa conferência será seguro criar o conversor para o formato CTC. Cabeçalhos NPY com dtype de objeto serão apenas identificados; nunca serão carregados com `allow_pickle=True`.


### Conferência direta da licença e do README v4

Em 04/11/2026, o arquivo `LICENSE.txt` da versão v4 foi aberto e conferido: ele declara CC BY-NC 4.0, exige atribuição e proíbe uso comercial. O README v4 também documenta a estrutura de `Libras-EQT-UECE-T.zip`: `annotations/dev.npy`, `annotations/test.npy`, `annotations/train.npy` e diretórios de quadros por gravação. O mesmo README descreve o ZIP de landmarks como CSV/JSON, mas a auditoria deste projeto encontrou NPY nesse pacote. Registrar e investigar essa diferença é obrigatório; não assumir que os dois pacotes têm o mesmo formato.
