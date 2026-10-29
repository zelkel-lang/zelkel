{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };

      pythonEnv = pkgs.python3.withPackages (ps: with ps; [
        rich
      ]);
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          pythonEnv
          ruff
          llvmPackages_latest.llvm
          clang
        ];

        shellHook = ''
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          export PYTHONPATH="${builtins.toString ./.}:$PYTHONPATH"
        '';
      };
    };
}
