# timrc [![Build Status](https://travis-ci.org/tnicolas42/timrc.svg?branch=master)](https://travis-ci.org/tnicolas42/timrc)

## Insallation

### Requirement

Pour installer timrc vous devez avoir deja installe certains programmes:
```bash
zsh
git
vim
oh-my-zsh
```
macos:
```bash
brew install zsh git vim
sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)"
```

ubuntu:
```bash
sudo apt-get install zsh git vim
sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)"
```

### Installation

Pour tout installer:
```bash
git clone git@github.com:tnicolas42/timrc.git ~/.tim && cd ~/.tim && ./install.sh -v && source ~/.zshrc
```

Installation etapes par etapes:

Cloner le repo git
```bash
git clone git@github.com:tnicolas42/timrc.git ~/.tim
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

