#!/bin/sh

sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install git -y

git config --global core.pager 'less -x1,5'
git config --global user.name "tnicolas42"
git config --global user.email "tnicolas@student.42.fr"

echo 'ssh-keygen -t rsa -b 4096 -C "tnicolas@student.42.fr"'
echo 'eval "$(ssh-agent -s)"'
echo 'ssh-add ~/.ssh/id_rsa'
echo 'cat ~/.ssh/id_rsa.pub'

echo "paste ssh key in github"

echo "then run curl https://raw.githubusercontent.com/tnicolas42/timrc/master/installs/linux_install.sh | sh"
