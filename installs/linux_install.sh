#!/bin/zsh

sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install tig tmux wget curl gcc xclip zsh -y

sudo add-apt-repository ppa:jonathonf/vim
sudo apt update -y
sudo apt install vim -y

sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)"

git clone git@github.com:tnicolas42/timrc ~/.tim && cd ~/.tim && ./install.sh -v
