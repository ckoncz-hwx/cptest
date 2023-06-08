FROM gitpod/workspace-full:2022-04-11-18-21-27

RUN pyenv install 3.9.5 \
    && pyenv global 3.9.5