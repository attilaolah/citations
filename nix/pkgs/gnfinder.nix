{
  lib,
  buildGoModule,
  fetchFromGitHub,
}:
buildGoModule rec {
  pname = "gnfinder";
  version = "1.1.6";

  src = fetchFromGitHub {
    owner = "gnames";
    repo = "gnfinder";
    rev = "v${version}";
    hash = "sha256-huv9NnFQAZwzjZ7EYF0XNDXWBHA3F9yOjLRqxEvLzd0=";
  };

  vendorHash = "sha256-28+KOS5qeSvhkC5QgzwzOKyqqFlbtnUHTsBgZj8vBa0=";

  subPackages = ["."];

  ldflags = [
    "-s"
    "-w"
    "-X github.com/gnames/gnfinder/ent/version.Version=${version}"
  ];

  # Upstream tests require project fixtures that are not stable across builders.
  doCheck = false;

  meta = {
    description = "Find and verify scientific names in text";
    homepage = "https://github.com/gnames/gnfinder";
    changelog = "https://github.com/gnames/gnfinder/releases/tag/v${version}";
    license = lib.licenses.mit;
    mainProgram = "gnfinder";
    maintainers = [];
  };
}
