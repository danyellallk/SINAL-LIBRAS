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
- Licença declarada: Creative Commons CC BY-NC 4.0.
- A licença exige atribuição e **não permite uso comercial**. Antes de qualquer uso, conferir o README, a estrutura, as anotações, as condições de consentimento e se a tarefa/labels servem ao nosso objetivo.

Este dataset é uma opção para um experimento estritamente não comercial, respeitando a licença e citando os autores. Ele não deve ser usado em uma versão comercial ou monetizada sem uma autorização/licença diferente. O arquivo de landmarks é menor que os vídeos, mas ainda tem centenas de MB; não é adequado para baixar e treinar diretamente no celular Android.

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
