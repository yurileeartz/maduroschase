🏃‍♂️💥 Maduro’s Chase

Um jogo em Python + Pygame onde Donald Trump enfrenta Nicolás Maduro em um labirinto cheio de barris misteriosos.
Trump precisa atirar antes que Maduro consiga alcançar os barris!

🎮 Como jogar

Setas / WASD → Movem o Trump pelo labirinto.

Mouse (clique) → Faz o Trump atirar com a bazuca.

Objetivo do Trump → Atingir o Maduro com o tiro antes que ele chegue a um barril.

Objetivo do Maduro → Chegar até os barris e “vencer” a partida.

📂 Estrutura de pastas
MaduroChase/
│── MadurosChase.py        # Arquivo principal do jogo
│
├── images/                # Imagens do jogo
│   ├── maze.png
│   ├── game_intro.png
│   ├── game_over.png
│   ├── barrel.png
│   ├── trump_idle.png
│   ├── trump_shot.png
│   ├── trump_shot2.png
│   ├── maduros_idle.png
│   ├── maduros_walk.png
│   ├── maduros_hit.png
│
├── songs/                 # Sons e músicas
│   ├── intro_song.mp3
│   ├── backgroundsong.mp3
│   ├── bazooka_shot.wav
│   ├── maduroscream.mp3

🖼️ Mecânicas e animações

Trump

Estado padrão: trump_idle.png

Quando atira: animação rápida trump_shot.png → trump_shot2.png e volta para idle

Maduro

Parado: maduros_idle.png

Caminhando em direção aos barris: maduros_walk.png

Quando atingido: maduros_hit.png

Barris

Aparecem em posições aleatórias no labirinto

Se Maduro chegar a um, ele vence

🔊 Áudio

🎵 Intro → intro_song.mp3

🎵 Fundo (loop) → backgroundsong.mp3

💥 Tiro da bazuca → bazooka_shot.wav

😱 Grito do Maduro (curto) → maduroscream.mp3

🏆 Condições de vitória

Trump vence → Se o tiro atingir Maduro antes dele alcançar um barril

Maduro vence → Se conseguir tocar em qualquer barril

🚀 Como rodar

Instale o Python 3.10+

Instale as dependências:

pip install pygame


Rode o jogo:

python MadurosChase.py

📌 Requisitos

Python 3.10 ou superior

Pygame

⚠️ Aviso

Este jogo foi feito apenas para entretenimento e aprendizado.
Não tem vínculo político e usa humor/sátira para criar uma experiência divertida.
