{
  description = "Research skeleton for ONNX Runtime KV-cache bottleneck analysis and FPGA-based decode accelerator validation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      lib = pkgs.lib;

      pythonEnv =
        pkgs.python3.withPackages
          (ps:
            let
              opt = name:
                lib.optionals (builtins.hasAttr name ps) [ (builtins.getAttr name ps) ];
            in
            [
              ps.pip
              ps.virtualenv
              ps.numpy
              ps.pandas
              ps.matplotlib
            ]
            ++ opt "onnx"
            ++ opt "onnxruntime");

      quartusAttrCandidates = [
        [ "quartus-prime-lite" ]
        [ "quartus-prime-standard" ]
        [ "quartus-prime" ]
        [ "quartus" ]
      ];

      quartusAttrMatches =
        builtins.filter (path: lib.hasAttrByPath path pkgs) quartusAttrCandidates;

      quartusPackage =
        if quartusAttrMatches == [ ] then
          null
        else
          lib.getAttrFromPath (builtins.head quartusAttrMatches) pkgs;

      quartusAttrLabel =
        if quartusAttrMatches == [ ] then
          "not available from current nixpkgs"
        else
          builtins.concatStringsSep "." (builtins.head quartusAttrMatches);

      basePackages =
        [
          pkgs.git
          pkgs.direnv
          pkgs.jdk17_headless
          pkgs.sbt
          pkgs.scala
          pkgs.python3
          pythonEnv
          pkgs.just
          pkgs.gnumake
          pkgs.pkg-config
        ]
        ++ lib.optionals (builtins.hasAttr "verilator" pkgs) [ pkgs.verilator ];

      commonShellHook = ''
        export JAVA_HOME="${pkgs.jdk17_headless}"
        export SLLM_FPGA_ROOT="$PWD"
        export NIXPKGS_ALLOW_UNFREE=1

        if [ -f "$PWD/quartus/de10_lite_qk/scripts/quartus_env.sh" ]; then
          . "$PWD/quartus/de10_lite_qk/scripts/quartus_env.sh"
          if quartus_setup_path; then
            echo "[quartus] quartus_sh: $(command -v quartus_sh)"
            echo "[quartus] QUARTUS_ROOT=$QUARTUS_ROOT"
          else
            echo "[quartus] warning: Quartus not found. SpinalHDL, simulation, and Python tooling remain usable."
          fi
        else
          echo "[quartus] warning: Quartus helper script not found. SpinalHDL, simulation, and Python tooling remain usable."
        fi

        echo "[devshell] JAVA_HOME=$JAVA_HOME"
        echo "[devshell] optional nixpkgs Quartus attribute: ${quartusAttrLabel}"
      '';
    in
    {
      devShells.${system} = {
        default = pkgs.mkShell {
          packages = basePackages;
          shellHook = commonShellHook;
        };

        quartus = pkgs.mkShell {
          packages = basePackages ++ lib.optionals (quartusPackage != null) [ quartusPackage ];
          shellHook =
            commonShellHook
            + ''
              if [ "${if quartusPackage == null then "0" else "1"}" = "1" ]; then
                echo "[quartus] nixpkgs package available and included in this shell."
              else
                echo "[quartus] nixpkgs package not available; using external detection only."
              fi
            '';
        };
      };
    };
}
