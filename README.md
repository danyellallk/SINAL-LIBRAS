# SINAL LIBRAS

Protótipo gratuito, mobile-first e instalável como PWA para apoiar a comunicação entre português e Libras.

## O que existe nesta versão
- Catálogo de fontes externas para consulta de vídeos e sinais: TV INES (cotidiano e A Vida em Libras), Corpus de Libras/UFSC, GoiásLibras, V-Librasil/UFPE e WikiLibras. O app abre os acervos originais e não copia vídeos de terceiros.
- Salvamento automático do rascunho de conversa no armazenamento local do aparelho, com recuperação ao reabrir e remoção pelo botão “Limpar texto”. O conteúdo não é enviado ao servidor.
- Navegação por quatro abas fixas no rodapé: Conversar, Favoritos, Explorar e Mais. Cada aba mostra somente sua área de conteúdo para facilitar o uso no celular.
- Área de conversa aprimorada: contador de até 500 caracteres, botão para limpar o texto e aviso automático de conexão/offline.
- Interface v1.4 simplificada: a área de conversa fica em destaque; frases rápidas, favoritos, instalação e ferramentas avançadas ficam organizados em seções expansíveis para reduzir a quantidade de botões visíveis.
- Interface responsiva para Android e navegador. Rodapé e indicadores acessíveis com mensagens de estado.
- Alternância entre os sentidos Português → Libras e Libras → Português.
- Frases rápidas para preencher a mensagem.
- Leitura de texto em voz alta usando os recursos do navegador.
- Prévia e gravação local de vídeo pela câmera do Android, mediante permissão do usuário e suporte do navegador; a gravação pode ser preparada para análise temporal. O arquivo permanece no aparelho e ainda não é traduzido automaticamente.
- Manifesto e cache básico para instalação/uso offline.
- Orientação e botão de instalação como aplicativo no Android, quando o navegador oferece suporte.
- Mensagens favoritas salvas localmente no aparelho, com opção de reutilizar e excluir.
- Copiar mensagens e compartilhar pelo menu nativo do Android, quando disponível; alternativa de cópia para navegadores sem compartilhamento direto.
- Digitação por voz em português, quando o navegador oferece a API de reconhecimento de fala; exige permissão do microfone e pode depender de conexão.
- Widget oficial VLibras para apoio à tradução de conteúdo textual português → Libras (requer internet).
- Seleção de vídeo local de até 100 MB e extração de três quadros para inspeção visual, sem enviar o arquivo à internet.
- Detecção experimental de até duas mãos e de 21 pontos por mão nos quadros, com MediaPipe no navegador; o vídeo e os quadros são processados localmente. É necessário internet para carregar a biblioteca e o modelo.
- Exportação local dos pontos detectados em arquivo JSON, com coordenadas normalizadas e indicação de lateralidade quando disponível.
- Análise experimental de 12 momentos do vídeo com MediaPipe em modo temporal, exportando sequências de coordenadas e tempos para estudo posterior. A versão 2.0 também tenta registrar 33 pontos corporais e 15 pontos faciais selecionados, além das mãos; se os modelos de corpo ou rosto não carregarem, a análise continua com os recursos disponíveis.
- Organização local de exemplos: permite associar rótulo e contexto a uma sequência temporal, declarar se aguarda validação ou foi revisada por pessoa fluente em Libras, confirmar autorização de uso do vídeo e exportar o conjunto em JSON. Os dados ficam no armazenamento local do navegador.
- Gerenciamento dos exemplos locais: lista os registros salvos, permite alterar a situação de revisão declarada e excluir exemplos individualmente. O limite é de 20 registros para reduzir o risco de lotar o armazenamento do navegador.
- Preparação experimental para treinamento: cada exemplo pode receber um pseudônimo da pessoa sinalizadora. Na exportação, os vídeos da mesma pessoa são mantidos no mesmo grupo (treino, validação ou teste), reduzindo vazamento de identidade entre grupos.

## Uso responsável dos acervos externos
Os links do catálogo servem para consulta e descoberta de material. A disponibilidade pública de um vídeo não significa autorização para baixá-lo, republicá-lo, extrair quadros ou incorporá-lo a um conjunto de treinamento. Antes de qualquer reutilização, é necessário verificar a licença e os termos de cada acervo e obter autorização quando aplicável. Corpus de pesquisa pode exigir cadastro, acesso aprovado ou consentimento específico. O app registra apenas links de origem nesta etapa.

## Limitações importantes
Esta versão **ainda não traduz automaticamente** português para Libras e **não reconhece o significado de sinais** pela câmera ou por vídeos. A gravação pela câmera e a seleção de arquivos apenas fornecem o vídeo para a etapa de extração de pontos; não são interpretação semântica. A detecção de pontos das mãos é apenas uma etapa visual, não uma tradução. O JSON exportado contém coordenadas de até 21 pontos por mão, pontos corporais e um conjunto reduzido de pontos faciais nos quadros amostrados; não contém rótulos de sinais, frases ou interpretação semântica. A extração de quadros serve apenas para inspeção visual e preparação de uma futura etapa de reconhecimento. A análise temporal amostra 12 momentos do vídeo e registra mudanças nas coordenadas das mãos, mas não reconhece palavras ou frases em Libras. O cadastro de exemplos apenas associa rótulos informados pelo usuário às coordenadas; a situação de revisão é autodeclarada e não é verificada pelo aplicativo. A divisão por pseudônimo é uma organização preliminar, não um treinamento de modelo nem uma garantia de que os grupos fiquem equilibrados. Identificadores ausentes em exemplos antigos recebem um grupo legado comum. É necessário obter autorização da pessoa filmada e validar os exemplos com pessoas fluentes em Libras. O resultado informa isso explicitamente. Libras é uma língua natural, com gramática e elementos não manuais próprios; não deve ser reduzida a uma lista de gestos ou tradução palavra por palavra.

## Privacidade da análise visual
O processamento dos quadros de vídeo acontece no dispositivo. A biblioteca e os modelos de mãos, pose e rosto são carregados de serviços externos; a biblioteca pode enviar métricas de uso. O vídeo selecionado não é enviado para esses serviços. Os pontos faciais são coordenadas selecionadas para estudo de movimento, não identificação biométrica.

## Privacidade da detecção de mãos
O processamento dos quadros com MediaPipe acontece no dispositivo, mas a biblioteca e o modelo são carregados de serviços externos e a biblioteca pode enviar métricas de uso. O vídeo selecionado não é enviado para esses serviços. Consulte a documentação oficial do [MediaPipe Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js).

## Observação sobre o VLibras
O widget é um serviço externo oficial e gratuito. Ele pode ajudar na compreensão de textos, mas a tradução automática pode conter erros e não substitui intérprete humano.

## Preparação de dados para treinamento
A exportação v2 inclui pseudônimo da pessoa sinalizadora e um campo `split` (`treino`, `validacao` ou `teste`) calculado de forma determinística por pseudônimo. O objetivo é manter gravações da mesma pessoa no mesmo grupo e evitar que o modelo seja avaliado com vídeos de alguém que já apareceu no treinamento. Com poucos participantes, a divisão pode ficar desequilibrada ou algum grupo pode ficar vazio; revise a distribuição antes de qualquer treinamento. Use apenas vídeos com autorização explícita e rótulos revisados por pessoas fluentes em Libras. Não use o conjunto V-Librasil para gerar derivados ou treinamento até confirmar a permissão compatível: a referência acadêmica indica licença CC BY-NC-ND 3.0 Brasil, que restringe obras derivadas.

## Preparação de dados para treinamento
O diretório `training/` contém um script Python sem dependências externas para validar e padronizar a exportação JSON em JSONL, com mãos, corpo, pontos faciais, rótulos e separação por pseudônimo de sinalizador. Consulte `training/README.md`. Esta ferramenta apenas prepara dados; ainda não existe um modelo treinado nem tradução automática de vídeo.

## Próximas etapas
1. Desenvolver e validar reconhecimento de sinais em sequências de vídeo com dados autorizados e participação de pessoas fluentes em Libras.
2. Criar biblioteca de sinais com vídeos revisados por pessoas fluentes em Libras.
3. Construir fluxo de frases com estrutura linguística adequada.
4. Pesquisar reconhecimento de mãos/corpo/expressões com dados autorizados e testes com a comunidade surda.
5. Avaliar avatar 3D e conversação assistida.

## Publicar gratuitamente
O projeto pode ser publicado pelo GitHub Pages. Não requer serviço pago para esta primeira versão.

## Experimento de treinamento
O diretório `training/` também inclui um classificador GRU experimental em PyTorch para sinais isolados. Ele requer um conjunto com classes e grupos de treino/validação adequados; não realiza tradução de frases e não está integrado ao app ainda.
Consulte `training/README.md` antes de executar. O app ainda não contém um modelo de tradução Libras–Português treinado.


## Entrada por gravação no Android (v2.3)
Na aba **Mais**, abra a câmera, permita o acesso e toque em **Iniciar gravação**. Ao terminar, toque em **Parar e usar vídeo**. O vídeo gravado é mantido localmente e fica pronto para a etapa de preparação dos quadros e análise temporal. Se o navegador não oferecer MediaRecorder, use a seleção de vídeo do aparelho. A gravação não envia o vídeo para um servidor e ainda não produz tradução em português.

## Base de pesquisa LIBRAS-EQT-UECE — atenção à licença
Foi identificada a base LIBRAS-EQT-UECE (DOI: 10.5281/zenodo.21398895), que contém amostras isoladas e contínuas e arquivos de landmarks. A versão consultada informa licença CC BY-NC 4.0: exige atribuição e **proíbe uso comercial**. Portanto, ela não deve ser incorporada a um produto comercial sem autorização/licença separada dos titulares. Antes de qualquer experimento, é necessário conferir a licença de cada versão/arquivo, citar os autores e respeitar consentimentos e condições do conjunto. Não baixamos nem copiamos essa base para este repositório.


### Selecionar vídeo da galeria (v2.4)
Na área da câmera, o botão **Escolher vídeo da galeria** abre os vídeos disponíveis no Android. Ao selecionar um arquivo de até 100 MB, ele é carregado localmente e fica pronto para a etapa **Explorar → Preparar quadros do vídeo**. O seletor usa o mesmo fluxo local de análise; nenhum vídeo é enviado automaticamente.

## Fontes para treinamento e uso responsável
Consulte [`training/DATA_SOURCES.md`](training/DATA_SOURCES.md) para as fontes de dados avaliadas, licenças, restrições do YouTube e plano de treinamento responsável. Nenhum vídeo do YouTube é baixado ou usado automaticamente pelo projeto.
