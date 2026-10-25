# Environment

All measured runs execute on GitHub-hosted Linux runners. A Windows laptop is used to write the scripts,
analyse the authors' artifacts and the CI outputs, and run small smoke tests.

## Why Linux runners

- The authors ran PDFBox on Linux with AdoptOpenJDK 11.0.8 (recorded in `pdfbox/execution/execution.log` of the
  experiments repository).
- PDFBox looks up the fonts installed on the machine (`FileSystemFontProvider`) and caches them in
  `~/.pdfbox.cache`. Several target methods are font methods (`NamingTable.getName`, `TrueTypeFont.getAdvanceWidth`,
  ...), so their invocation counts depend on the installed fonts. The working example of the paper (Fig. 2) shows
  the font `LiberationSans`, so the authors' machine had the Liberation fonts. On the runners the font set is
  controlled (`fonts-liberation` installed, full `fc-list` recorded in each run).
- The runners are free for public repositories (4 vCPU, 16 GB RAM, 6 hours per job).

## CI toolchain (`scripts/ci/`)

| Component | Version | Source | Check |
|---|---|---|---|
| Runner image | `ubuntu-22.04` | GitHub-hosted | image version recorded in `env-report.txt` |
| JDK | AdoptOpenJDK 11.0.8+10 (HotSpot) | github.com/AdoptOpenJDK/openjdk11-binaries | sha256 from the release |
| Maven | 3.6.3 | archive.apache.org | sha512 from the archive |
| Fonts | `fonts-liberation` (apt) | Ubuntu | `fc-list` in `env-report.txt` |

Every run uploads `env-report.txt` (runner image, CPU, memory, disk, Java and Maven versions, locale, fonts).

## Laptop toolchain (`setup/windows/install-tools.ps1`)

Windows 10, 8 GB RAM, 8 logical CPUs. Docker and WSL are not available and there are no administrator rights,
so all tools are portable and live in `C:\w\tools`.

| Component | Version | Check |
|---|---|---|
| JDK | AdoptOpenJDK 11.0.8+10 (`OpenJDK11U-jdk_x64_windows_hotspot_11.0.8_10.zip`) | sha256 `473e5527...6baa48` |
| Maven | 3.6.3 | sha512 from the archive |
| GitHub CLI | 2.102.0 | release checksums |
| uv | 0.13.1 | release sha256 |
| Python | 3.11.17 (installed by uv) | |
| Python packages | pandas 1.5.3, numpy 1.26.4, matplotlib 3.8.4 | `requirements.txt` |

pandas is pinned below 2.0 because the authors' scripts (`find-pseudo-tested.py`) use `DataFrame.append`, which
pandas 2 removed. Python 3.11 is used because pandas 1.5 has no build for newer Python versions.

`setup/windows/env.ps1` and `setup/env.sh` set `JAVA_HOME`, `PATH`, `MAVEN_OPTS` and
`JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF-8`. The last one makes local Java runs use UTF-8 like Linux: PANKTI writes
its XML files with the platform default charset, which is Cp1252 on Windows.

## Notes from setting up the laptop

- `Invoke-WebRequest` repeatedly stopped the 194 MB JDK download at about 150-170 MB without an error. The script
  now uses `curl.exe` (shipped with Windows 10) with retries and resume, and checks every checksum.
- In Windows PowerShell 5.1, output that native tools write on stderr (uv progress, for example) becomes a
  terminating error under `$ErrorActionPreference = "Stop"`. Native calls go through a small wrapper that only
  looks at the exit code.
- Some file names in the experiments repository exceed the Windows path limit. `setup/fetch-artifacts.sh` enables
  `core.longpaths` and checks out only `README.md` and `pdfbox/` (sparse checkout). Git Bash rewrites arguments
  that start with `/` into Windows paths, which breaks sparse-checkout patterns; `MSYS2_ARG_CONV_EXCL` disables
  that for the one command.
