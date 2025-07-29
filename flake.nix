{
  description = "A robust development environment for Python with Playwright for the web2llm project.";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      # Define supported systems to make the flake portable.
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      # Generate outputs for each supported system.
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      # Define the package set for a given system.
      pkgsFor = system: import nixpkgs {
        inherit system;
        config = {
          # Allow Nix to fetch unfree browser binaries for Playwright.
          allowUnfree = true;
        };
      };

    in
    {
      # Generate a devShell for each supported system.
      devShells = forAllSystems (system:
        let
          pkgs = pkgsFor system;

          pythonWithProjectDeps = pkgs.python3.withPackages (ps: with ps; [
            playwright
            beautifulsoup4
            lxml
            markdownify
            gitpython
            pdfplumber
            pyyaml
            pathspec
            httpx
            pytest
            pytest-mock
            pytest-asyncio
          ]);
        in
        pkgs.mkShell {
          packages = with pkgs; [
            pythonWithProjectDeps
            playwright-driver
            ruff
            pre-commit
            git
          ];

          PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
          PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";

          shellHook = ''
            echo "Nix-managed Python dev environment for 'web2llm' on ${system} active."
            export PYTHONPATH=$PWD:$PYTHONPATH
            alias web2llm="python -m web2llm.cli"
            echo "Use 'web2llm' to run from source."
          '';
        });
    };
}
