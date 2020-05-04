# timrc

## Insallation

### Requirement

Pour installer timrc vous devez avoir deja installe certains programmes:
```bash
zsh
git
vim
wget
oh-my-zsh
```
macos:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew install zsh git vim wget
sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)"
```

ubuntu:
```bash
sudo apt-get install zsh git vim wget
# oh-my-zsh
sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)"
# vim 8
sudo add-apt-repository ppa:jonathonf/vim
sudo apt update
sudo apt install vim
```

### Installation

Pour tout installer:
```bash
git clone https://github.com/tnicolas42/timrc ~/.tim && cd ~/.tim && ./install.sh -v && source ~/.zshrc
```
```bash
git clone git@github.com:tnicolas42/timrc ~/.tim && cd ~/.tim && ./install.sh -v && source ~/.zshrc
```

Installation etapes par etapes:

Cloner le repo git
```bash
git clone https://github.com/tnicolas42/timrc ~/.tim
cd ~/.tim
```

Installer tout
```bash
./install.sh
```

Afficher l'aide
```bash
./install.sh --help
```

Ne pas installer la config zsh
```bash
./install.sh --nozsh
```

Ne pas installer la config vim
```bash
./install.sh --novim
```

## Full installation linux

```
curl https://raw.githubusercontent.com/tnicolas42/timrc/master/installs/linux_first_install.sh | sh
```

add the ssh key

```
curl https://raw.githubusercontent.com/tnicolas42/timrc/master/installs/linux_install.sh | sh
```
