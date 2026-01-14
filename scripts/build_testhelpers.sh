#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CLIENT_GO_PATH="${CLIENT_GO_PATH:-"$ROOT_DIR/../client-go"}"
CLIENT_NODE_PATH="${CLIENT_NODE_PATH:-"$ROOT_DIR/../client-node"}"
CLIENT_PYTHON_PATH="${CLIENT_PYTHON_PATH:-"$ROOT_DIR/../client-python"}"
CLIENT_JAVA_PATH="${CLIENT_JAVA_PATH:-"$ROOT_DIR/../client-java"}"
CLIENT_DOTNET_PATH="${CLIENT_DOTNET_PATH:-"$ROOT_DIR/../client-dotnet"}"

run_in() {
  local dir="$1"
  shift
  pushd "$dir" >/dev/null
  "$@"
  popd >/dev/null
}

# Go - build binary
run_in "$CLIENT_GO_PATH" go build -o testhelper ./cmd/testhelper

# Node - install dependencies (testhelper runs via tsx)
run_in "$CLIENT_NODE_PATH" npm install

# Python - setup venv with SDK installed
run_in "$CLIENT_PYTHON_PATH" python3 -m venv .venv
run_in "$CLIENT_PYTHON_PATH" .venv/bin/pip install -e .

# Java - build SDK jar then install to local Maven repo
if [ -x "$CLIENT_JAVA_PATH/gradlew" ]; then
  run_in "$CLIENT_JAVA_PATH" ./gradlew clean jar
else
  run_in "$CLIENT_JAVA_PATH" gradle clean jar
fi

jar_version=""
if [ -f "$CLIENT_JAVA_PATH/gradle.properties" ]; then
  jar_version="$(grep -E '^version=' "$CLIENT_JAVA_PATH/gradle.properties" | head -n1 | cut -d= -f2- | tr -d '[:space:]')"
fi
if [ -z "$jar_version" ]; then
  jar_version="$(grep -E "^version\\s*=" "$CLIENT_JAVA_PATH/build.gradle" | head -n1 | sed -E "s/.*version\\s*=\\s*['\\\"]([^'\\\"]+)['\\\"].*/\\1/")"
fi
if [ -z "$jar_version" ]; then
  echo "Error: could not determine client-java version" >&2
  exit 1
fi

jar_path=""
for f in "$CLIENT_JAVA_PATH"/build/libs/*"$jar_version".jar; do
  case "$f" in
    *-sources.jar|*-javadoc.jar) continue ;;
  esac
  jar_path="$f"
  break
done

if [ -z "$jar_path" ]; then
  echo "Error: no client jar found in $CLIENT_JAVA_PATH/build/libs for version $jar_version" >&2
  exit 1
fi

run_in "$CLIENT_JAVA_PATH" mvn install:install-file \
  -Dfile="$jar_path" \
  -DgroupId=com.vaultsandbox \
  -DartifactId=client \
  -Dversion="$jar_version" \
  -Dpackaging=jar \
  -DgeneratePom=true
run_in "$CLIENT_JAVA_PATH/scripts/testhelper" mvn clean package

# .NET - build (runs via dotnet run)
run_in "$CLIENT_DOTNET_PATH/scripts/Testhelper" dotnet build
