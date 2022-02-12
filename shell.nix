{ pkgs ? import <nixpkgs> { } }:

let
  inherit (pkgs) mkShell python3;
  python = python3.withPackages (ppkgs:
    with ppkgs; [
      python-lsp-server
      python-lsp-black
      pyls-isort
      pylsp-mypy

      rope
      pyflakes
      mccabe
      pycodestyle
      pydocstyle
    ]);
in mkShell { nativeBuildInputs = with pkgs; [ jq python ]; }
