#!/usr/bin/env bash
# Session environment for the portable Windows toolchain of setup/windows/install-tools.ps1 (Git Bash).
# Usage: source setup/env.sh <tools_dir>   (default: /c/w/tools, the directory used on the development laptop)
tools="${1:-/c/w/tools}"
export JAVA_HOME="$tools/jdk-11.0.8+10"
export MAVEN_HOME="$tools/apache-maven-3.6.3"
export MAVEN_OPTS="-Xmx2g"
export JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8"
export PATH="$JAVA_HOME/bin:$MAVEN_HOME/bin:$tools/gh/bin:$tools/uv:$tools/py311/Scripts:$PATH"
