{ pkgs ? import <nixpkgs> {}}:
pkgs.lib.extendDerivation true {
	py2 = pkgs.callPackage nix/default.nix {
		pythonPackages = pkgs.python2Packages;
	};
} (pkgs.callPackage nix/default.nix {
	pythonPackages = pkgs.python3Packages;
})
