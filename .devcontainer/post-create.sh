# Change perms to vscode user
sudo chown -R vscode:vscode $DEV_CONTAINER_ROOT

# configure oh-my-zsh
export ZSH_CUSTOM=${HOME}/.oh-my-zsh/custom
mkdir -p $ZSH_CUSTOM/plugins/poetry
poetry completions zsh > $ZSH_CUSTOM/plugins/poetry/_poetry
sed -i -e "s/plugins=(git)/plugins=(git poetry)/" $HOME/.zshrc

# Configure poetry
poetry install

pre-commit install
