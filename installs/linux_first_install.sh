#!/bin/sh

sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install git -y

git config --global core.pager 'less -x1,5'
git config --global user.name "tnicolas42"
git config --global user.email "tnicolas@student.42.fr"

ssh-keygen -t rsa -b 4096 -C "tnicolas@student.42.fr"
eval "$(ssh-agent -s)"
ssh-add -K ~/.ssh/id_rsa
xclip -sel clip < ~/.ssh/id_rsa.pub

echo "paste ssh key in github"
