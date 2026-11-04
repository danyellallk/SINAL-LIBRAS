# SINAL LIBRAS

Protótipo gratuito, mobile-first e instalável como PWA para apoiar a comunicação entre português e Libras.

## O que existe nesta versão
- Interface responsiva para Android e navegador.
- Alternância entre os sentidos Português → Libras e Libras → Português.
- Frases rápidas para preencher a mensagem.
- Leitura de texto em voz alta usando os recursos do navegador.
- Prévia da câmera, mediante permissão do usuário.
- Manifesto e cache básico para instalação/uso offline.
- Orientação e botão de instalação como aplicativo no Android, quando o navegador oferece suporte.
- Mensagens favoritas salvas localmente no aparelho, com opção de reutilizar e excluir.
- Copiar mensagens e compartilhar pelo menu nativo do Android, quando disponível; alternativa de cópia para navegadores sem compartilhamento direto.
- Digitação por voz em português, quando o navegador oferece a API de reconhecimento de fala; exige permissão do microfone e pode depender de conexão.
- Widget oficial VLibras para apoio à tradução de conteúdo textual português → Libras (requer internet).
- Seleção de vídeo local de até 100 MB e extração de três quadros para inspeção visual, sem enviar o arquivo à internet.
- Detecção experimental de até duas mãos e de 21 pontos por mão nos quadros, com MediaPipe no navegador; o vídeo e os quadros são processados localmente. É necessário internet para carregar a biblioteca e o modelo.
- Exportação local dos pontos detectados em arquivo JSON, com coordenadas normalizadas e indicação de lateralidade quando disponível.
- Análise experimental de 12 momentos do vídeo com MediaPipe em modo temporal, exportando sequências de coordenadas e tempos para estudo posterior.
- Organização local de exemplos: permite associar rótulo e contexto a uma sequência temporal, declarar se aguarda validação ou foi revisada por pessoa fluente em Libras, confirmar autorização de uso do vídeo e exportar o conjunto em JSON. Os dados ficam no armazenamento local do navegador.
- Gerenciamento dos exemplos locais: lista os registros salvos, permite alterar a situação de revisão declarada e excluir exemplos individualmente. O limite é de 20 registros para reduzir o risco de lotar o armazenamento do navegador.

## Limitações importantes
Esta versão **não traduz automaticamente** português para Libras e **não reconhece o significado de sinais** pela câmera ou por vídeos. A detecção de pontos das mãos é apenas uma etapa visual, não uma tradução. O JSON exportado contém coordenadas de até 21 pontos por mão nos quadros amostrados; não contém rótulos de sinais, frases ou interpretação semântica. A extração de quadros serve apenas para inspeção visual e preparação de uma futura etapa de reconhecimento. A análise temporal amostra 12 momentos do vídeo e registra mudanças nas coordenadas das mãos, mas não reconhece palavras ou frases em Libras. O cadastro de exemplos apenas associa rótulos informados pelo usuário às coordenadas; a situação de revisão é autodeclarada e não é verificada pelo aplicativo. É necessário obter autorização da pessoa filmada e validar os exemplos com pessoas fluentes em Libras. O resultado informa isso explicitamente. Libras é uma língua natural, com gramática e elementos não manuais próprios; não deve ser reduzida a uma lista de gestos ou tradução palavra por palavra.

## Privacidade da detecção de mãos
O processamento dos quadros com MediaPipe acontece no dispositivo, mas a biblioteca e o modelo são carregados de serviços externos e a biblioteca pode enviar métricas de uso. O vídeo selecionado não é enviado para esses serviços. Consulte a documentação oficial do [MediaPipe Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js).

## Observação sobre o VLibras
O widget é um serviço externo oficial e gratuito. Ele pode ajudar na compreensão de textos, mas a tradução automática pode conter erros e não substitui intérprete humano.

## Próximas etapas
1. Desenvolver e validar reconhecimento de sinais em sequências de vídeo com dados autorizados e participação de pessoas fluentes em Libras.
2. Criar biblioteca de sinais com vídeos revisados por pessoas fluentes em Libras.
3. Construir fluxo de frases com estrutura linguística adequada.
4. Pesquisar reconhecimento de mãos/corpo/expressões com dados autorizados e testes com a comunidade surda.
5. Avaliar avatar 3D e conversação assistida.

## Publicar gratuitamente
O projeto pode ser publicado pelo GitHub Pages. Não requer serviço pago para esta primeira versão.